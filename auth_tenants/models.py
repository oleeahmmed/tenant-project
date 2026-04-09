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
        ("contacts",      "Contacts"),
        ("campaigns",     "Campaigns"),
        ("conversations", "Conversations"),
        ("analytics",     "Analytics"),
        ("billing",       "Billing"),
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
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


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
        if self.role in ("super_admin", "tenant_admin"):
            return True
        return perm in self.get_all_permissions_set()

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
