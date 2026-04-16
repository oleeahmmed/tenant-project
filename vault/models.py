import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


User = settings.AUTH_USER_MODEL


def _get_fernet() -> Fernet:
    raw_key = (
        getattr(settings, "ENTRY_ENCRYPTION_KEY", None) or os.getenv("ENTRY_ENCRYPTION_KEY") or ""
    ).strip()
    if not raw_key:
        raise ValueError(
            "ENTRY_ENCRYPTION_KEY is required. Add it to your .env (or rely on DEBUG + SECRET_KEY "
            "dev fallback in config.settings)."
        )
    if len(raw_key) == 44:
        key = raw_key.encode()
    else:
        key = base64.urlsafe_b64encode(hashlib.sha256(raw_key.encode()).digest())
    return Fernet(key)


class VaultTenantScopedModel(models.Model):
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_rows",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class VaultCategory(VaultTenantScopedModel):
    customer = models.ForeignKey(
        "foundation.Customer",
        on_delete=models.CASCADE,
        related_name="vault_categories",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["customer__name", "name"]
        unique_together = [("tenant", "customer", "name")]

    def clean(self):
        if self.tenant_id and self.customer_id and self.customer.tenant_id != self.tenant_id:
            raise ValidationError({"customer": "Customer must belong to the same tenant."})

    def __str__(self):
        customer_name = self.customer.name if self.customer_id else "No customer"
        return f"{customer_name} / {self.name}"


class VaultEntry(VaultTenantScopedModel):
    category = models.ForeignKey(
        VaultCategory,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    project = models.ForeignKey(
        "jiraclone.JiraProject",
        on_delete=models.CASCADE,
        related_name="vault_entries",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    url = models.URLField(blank=True)
    username = models.CharField(max_length=255, blank=True)
    password_encrypted = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_favorite = models.BooleanField(default=False)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    class Meta:
        ordering = ["category__customer__name", "project__key", "category__name", "name"]
        unique_together = [("tenant", "category", "name")]

    def clean(self):
        if self.tenant_id and self.category_id and self.category.tenant_id != self.tenant_id:
            raise ValidationError({"category": "Category must belong to the same tenant."})
        if self.tenant_id and self.project_id and self.project.tenant_id != self.tenant_id:
            raise ValidationError({"project": "Project must belong to the same tenant."})
        if self.category_id and self.project_id and self.project.customer_id != self.category.customer_id:
            raise ValidationError({"project": "Project customer must match selected category customer."})

    def set_password(self, raw_password: str):
        if not raw_password:
            self.password_encrypted = ""
            return
        self.password_encrypted = _get_fernet().encrypt(raw_password.encode("utf-8")).decode("utf-8")

    def get_password(self) -> str:
        if not self.password_encrypted:
            return ""
        try:
            plain = _get_fernet().decrypt(self.password_encrypted.encode("utf-8"))
        except (InvalidToken, ValueError):
            return ""
        self.last_accessed_at = timezone.now()
        self.save(update_fields=["last_accessed_at"])
        return plain.decode("utf-8")

    def __str__(self):
        return self.name


class VaultFileAttachment(VaultTenantScopedModel):
    entry = models.ForeignKey(
        VaultEntry,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="vault/files/%Y/%m/")
    title = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.tenant_id and self.entry_id and self.entry.tenant_id != self.tenant_id:
            raise ValidationError({"entry": "Entry must belong to the same tenant."})

    def __str__(self):
        return self.title or self.file.name


class VaultSharedEntry(VaultTenantScopedModel):
    class PermissionType(models.TextChoices):
        VIEW = "view", "View"
        COPY = "copy", "Copy"
        EDIT = "edit", "Edit"

    entry = models.ForeignKey(
        VaultEntry,
        on_delete=models.CASCADE,
        related_name="shares",
    )
    shared_with_email = models.EmailField()
    permission = models.CharField(max_length=10, choices=PermissionType.choices, default=PermissionType.VIEW)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    shared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("tenant", "entry", "shared_with_email")]

    def clean(self):
        if self.tenant_id and self.entry_id and self.entry.tenant_id != self.tenant_id:
            raise ValidationError({"entry": "Entry must belong to the same tenant."})

    def __str__(self):
        return f"{self.entry.name} → {self.shared_with_email}"
