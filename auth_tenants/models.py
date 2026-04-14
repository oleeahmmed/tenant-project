import uuid
import random
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# ── Permission (Super Admin master list) ──────────────────────────────────────
class Permission(models.Model):
    """
    Super Admin এই master list maintain করবে।
    Tenant Admin শুধু এই list থেকে role বা member এ assign করতে পারবে।
    """
    CATEGORIES = [
        ("foundation", "Foundation"),
        ("inventory", "Inventory"),
        ("finance", "Finance"),
        ("purchase", "Purchase"),
        ("sales", "Sales"),
        ("production", "Production"),
        ("jiraclone", "Jira clone"),
        ("chat", "Chat"),
        ("pos", "POS"),
        ("hrm", "HRM"),
        ("recruitment", "Recruitment"),
        ("support", "Support"),
        ("screenhot", "Screenhot"),
        ("auth_tenants", "Tenant Auth"),
        ("system", "System"),
    ]

    codename    = models.CharField(max_length=100, unique=True)
    # codename format: "contacts.view", "campaigns.create" ইত্যাদি
    label       = models.CharField(max_length=255)
    # label: human-readable, যেমন "View Contacts"
    category    = models.CharField(max_length=50, choices=CATEGORIES)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category", "codename"]

    def __str__(self):
        return f"{self.codename} — {self.label}"


# ── Tenant ────────────────────────────────────────────────────────────────────
class Tenant(models.Model):
    name       = models.CharField(max_length=255)
    slug       = models.SlugField(unique=True)
    logo       = models.ImageField(
        upload_to="tenant_logos/",
        blank=True,
        null=True,
        help_text="Shown on inventory printouts and similar documents.",
    )
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def is_module_enabled(self, module_code: str) -> bool:
        code = (module_code or "").strip().lower()
        if not code:
            return False
        if code in ("auth_tenants", "foundation"):
            return True
        row = self.module_subscriptions.filter(module_code=code).only("is_enabled").first()
        # Backward-compatible default: enabled when no explicit subscription row exists.
        return True if row is None else bool(row.is_enabled)


class TenantModuleSubscription(models.Model):
    class ModuleCode(models.TextChoices):
        HRM = "hrm", "HRM"
        RECRUITMENT = "recruitment", "Recruitment"
        INVENTORY = "inventory", "Inventory"
        FINANCE = "finance", "Finance"
        PURCHASE = "purchase", "Purchase"
        SALES = "sales", "Sales"
        PRODUCTION = "production", "Production"
        JIRACLONE = "jiraclone", "Jira clone"
        CHAT = "chat", "Chat"
        POS = "pos", "POS"
        SUPPORT = "support", "Support"
        SCREENHOT = "screenhot", "Screenhot"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="module_subscriptions")
    module_code = models.CharField(max_length=50, choices=ModuleCode.choices)
    is_enabled = models.BooleanField(default=True)
    enabled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant", "module_code")]

    def __str__(self):
        state = "enabled" if self.is_enabled else "disabled"
        return f"{self.tenant} - {self.module_code} ({state})"


class TenantPermissionGrant(models.Model):
    """Super admin controlled permission allow-list per tenant."""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="permission_grants")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="tenant_grants")
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant", "permission")]

    def __str__(self):
        state = "enabled" if self.is_enabled else "disabled"
        return f"{self.tenant} :: {self.permission.codename} ({state})"


# ── Role (Tenant-scoped) ──────────────────────────────────────────────────────
class Role(models.Model):
    """
    Tenant Admin নিজের tenant এর জন্য role বানাবে।
    permissions শুধু Permission master list এর codename থেকে নেওয়া যাবে।
    """
    tenant      = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="roles")
    name        = models.CharField(max_length=100)
    permissions = models.ManyToManyField(
                    Permission, blank=True, related_name="roles"
                  )
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "name")

    def __str__(self):
        return f"{self.tenant.name} → {self.name}"


# ── User Manager ──────────────────────────────────────────────────────────────
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email required")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.setdefault("role", "super_admin")
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


# ── User ──────────────────────────────────────────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin):
    ROLES = [
        ("super_admin",  "Super Admin"),
        ("tenant_admin", "Tenant Admin"),
        ("staff",        "Staff"),
    ]

    email       = models.EmailField(unique=True)
    name        = models.CharField(max_length=255)
    role        = models.CharField(max_length=20, choices=ROLES, default="staff")
    tenant      = models.ForeignKey(
                    Tenant, null=True, blank=True,
                    on_delete=models.CASCADE, related_name="members"
                  )
    custom_role = models.ForeignKey(
                    Role, null=True, blank=True,
                    on_delete=models.SET_NULL, related_name="users"
                  )
    # Role এর বাইরে directly assign করা extra permissions
    extra_permissions = models.ManyToManyField(
                          Permission, blank=True, related_name="users"
                        )
    avatar     = models.ImageField(upload_to="avatars/", null=True, blank=True)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["name"]

    def get_all_permissions_set(self):
        """
        User এর সব effective permissions — role + extra_permissions মিলিয়ে।
        """
        perms = set()
        if self.custom_role_id:
            perms.update(
                self.custom_role.permissions.filter(is_active=True)
                    .values_list("codename", flat=True)
            )
        perms.update(
            self.extra_permissions.filter(is_active=True)
                .values_list("codename", flat=True)
        )
        return perms

    def has_tenant_permission(self, perm: str) -> bool:
        if self.role == "super_admin":
            return True
        if not self.tenant_id:
            return False

        grants = TenantPermissionGrant.objects.filter(tenant_id=self.tenant_id).only("id")
        has_grant_matrix = grants.exists()

        if self.role == "tenant_admin":
            if not has_grant_matrix:
                # Backward-compatible fallback when matrix not configured yet.
                return True
            grant = TenantPermissionGrant.objects.filter(
                tenant_id=self.tenant_id,
                permission__codename=perm,
            ).select_related("permission").first()
            if grant is not None:
                return grant.is_enabled
            # Matrix exists but this codename has no row yet (e.g. new module like POS): allow if
            # tenant has that module enabled and permission exists in catalog.
            perm_obj = Permission.objects.filter(codename=perm, is_active=True).only("category").first()
            if not perm_obj:
                return False
            if perm_obj.category in ("system",):
                return False
            if perm_obj.category == "auth_tenants":
                return True
            t = Tenant.objects.filter(pk=self.tenant_id).first()
            if not t:
                return False
            return t.is_module_enabled(perm_obj.category)

        if self.role != "staff":
            return False
        if perm not in self.get_all_permissions_set():
            return False
        # Backward-compatible: if no grant rows are configured yet, allow legacy behavior.
        if not has_grant_matrix:
            return True
        return TenantPermissionGrant.objects.filter(
            tenant_id=self.tenant_id,
            permission__codename=perm,
            is_enabled=True,
        ).exists()

    def __str__(self):
        return f"{self.email} ({self.role})"


# ── OTP ───────────────────────────────────────────────────────────────────────
class OTPVerification(models.Model):
    email      = models.EmailField()
    otp_code   = models.CharField(max_length=6)
    is_used    = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def generate(cls, email):
        cls.objects.filter(email=email, is_used=False).update(is_used=True)
        return cls.objects.create(
            email=email,
            otp_code=str(random.randint(100000, 999999)),
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )

    def __str__(self):
        return f"{self.email} — {self.otp_code}"


# ── Invitation ────────────────────────────────────────────────────────────────
class Invitation(models.Model):
    tenant      = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="invitations")
    invited_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_invitations")
    email       = models.EmailField()
    name        = models.CharField(max_length=255)
    role        = models.ForeignKey(
                    Role, null=True, blank=True,
                    on_delete=models.SET_NULL, related_name="invitations"
                  )
    token       = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_accepted = models.BooleanField(default=False)
    expires_at  = models.DateTimeField()
    created_at  = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return not self.is_accepted and timezone.now() < self.expires_at

    def __str__(self):
        return f"Invite → {self.email} ({self.tenant.name})"
