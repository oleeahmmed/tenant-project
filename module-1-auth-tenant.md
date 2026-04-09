# Module 1: Auth & Tenant Management — Step by Step Guide

> একটাই Django app: `auth_tenants`
> যেকোনো multi-tenant project এ plug করা যাবে।
> SQLite দিয়ে শুরু, পরে PostgreSQL এ switch করার নির্দেশনা আছে।

---

## নতুন Features এই Version এ

- Tenant Admin invite পাঠাতে পারবে — email এ secure token যাবে
- Invited member সেই token দিয়ে নিজে password set করে register করবে
- সে automatically ওই tenant এর অধীনে হবে
- Tenant Admin custom role বানাতে পারবে (যেমন: Manager, Support, Sales)
- প্রতিটা role এ granular permission assign করা যাবে
- সব role ও permission tenant-scoped — এক tenant এর role অন্য tenant দেখতে পাবে না

---

## প্রজেক্ট স্ট্রাকচার

```
whatsapp-automation/
├── venv/
├── config/                 ← Django project settings
├── auth_tenants/           ← Django app
│   ├── migrations/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py           ← Tenant, User, OTP, Role, Invitation
│   ├── admin.py
│   └── api/                ← শুধু API code এখানে
│       ├── __init__.py
│       ├── views.py
│       ├── serializers.py
│       ├── urls.py
│       ├── permissions.py
│       └── utils.py
├── .env
├── requirements.txt
└── manage.py
```

---

## ধাপ ১: venv ও packages

```bash
python -m venv venv
```

- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

```bash
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers python-dotenv
pip freeze > requirements.txt
```

---

## ধাপ ২: Project ও app বানাও

```bash
django-admin startproject config .
python manage.py startapp auth_tenants
```

এরপর `auth_tenants/` folder এর ভেতরে `api/` folder বানাও:

```bash
mkdir auth_tenants\api
type nul > auth_tenants\api\__init__.py
```

`auth_tenants/apps.py` এমনিতেই ঠিক থাকবে:

```python
from django.apps import AppConfig

class AuthTenantsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "auth_tenants"
```

---

## ধাপ ৩: .env

```
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True

# SQLite (development)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# PostgreSQL (production) — নিচেরগুলো uncomment করো, উপরেরগুলো comment করো
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=whatsapp_saas
# DB_USER=postgres
# DB_PASSWORD=yourpassword
# DB_HOST=localhost
# DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7

# Invitation link এ ব্যবহার হবে
FRONTEND_URL=http://localhost:3000
```

---

## ধাপ ৪: settings.py

`core/settings.py`:

```python
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "auth_tenants",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ← সবার আগে
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# Database config
if os.getenv("DB_ENGINE") == "django.db.backends.postgresql":
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / os.getenv("DB_NAME", "db.sqlite3"),
    }}

AUTH_USER_MODEL = "auth_tenants.User"  # ← app_label, full path না

# ⚠️ Note: app টা api/ folder এ থাকলেও Django AUTH_USER_MODEL এ
# apps.py এর app_label ব্যবহার হয়, যেটা "auth_tenants"।
# api/auth_tenants/apps.py তে নিশ্চিত করো:
# name = "auth_tenants"
# label = "auth_tenants"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("ACCESS_TOKEN_LIFETIME_MINUTES", 60))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("REFRESH_TOKEN_LIFETIME_DAYS", 7))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@yourdomain.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
# Development এ সব allow করতে চাইলে:
# CORS_ALLOW_ALL_ORIGINS = True
```

---

## ধাপ ৫: Models

`auth_tenants/models.py`:

```python
import uuid
import random
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# ── Tenant ────────────────────────────────────────────────────────────────────
class Tenant(models.Model):
    name        = models.CharField(max_length=255)
    slug        = models.SlugField(unique=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ── Role (Tenant-scoped) ──────────────────────────────────────────────────────
class Role(models.Model):
    """
    Tenant Admin নিজের tenant এর জন্য custom role বানাতে পারবে।
    যেমন: Manager, Support, Sales
    """
    tenant      = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="roles")
    name        = models.CharField(max_length=100)
    permissions = models.JSONField(default=list)
    # permissions এর format: ["contacts.view", "contacts.create", "campaigns.view", ...]
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
    # Staff এর custom role (Tenant Admin এর বানানো Role)
    custom_role = models.ForeignKey(
                    Role, null=True, blank=True,
                    on_delete=models.SET_NULL, related_name="users"
                  )
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["name"]

    def has_tenant_permission(self, perm: str) -> bool:
        """
        Staff এর custom_role এ permission আছে কিনা check করো।
        Tenant Admin সব permission পাবে।
        """
        if self.role in ("super_admin", "tenant_admin"):
            return True
        if self.custom_role:
            return perm in self.custom_role.permissions
        return False

    def __str__(self):
        return f"{self.email} ({self.role})"


# ── OTP ───────────────────────────────────────────────────────────────────────
class OTPVerification(models.Model):
    email       = models.EmailField()
    otp_code    = models.CharField(max_length=6)
    is_used     = models.BooleanField(default=False)
    expires_at  = models.DateTimeField()
    created_at  = models.DateTimeField(auto_now_add=True)

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
    """
    Tenant Admin staff কে invite করবে।
    Staff এই token দিয়ে নিজে register করবে।
    """
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
```

---

## ধাপ ৬: Permissions

`auth_tenants/api/permissions.py`:

```python
from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "super_admin"


class IsTenantAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("super_admin", "tenant_admin")


class IsSameTenant(BasePermission):
    """Object level — নিজের tenant এর data ছাড়া access নেই"""
    def has_object_permission(self, request, view, obj):
        return getattr(obj, "tenant", None) == request.user.tenant


def HasTenantPerm(perm: str):
    """
    Dynamic permission class factory।
    ব্যবহার: permission_classes = [HasTenantPerm("contacts.view")]
    """
    class _Permission(BasePermission):
        def has_permission(self, request, view):
            return (
                request.user.is_authenticated
                and request.user.tenant is not None
                and request.user.has_tenant_permission(perm)
            )
    _Permission.__name__ = f"HasPerm_{perm}"
    return _Permission
```

---

## ধাপ ৭: Utils

`auth_tenants/api/utils.py`:

```python
from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(email: str, otp_code: str):
    send_mail(
        subject="Your OTP Code",
        message=f"Your OTP is: {otp_code}\nValid for 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def send_invitation_email(email: str, name: str, tenant_name: str, token: str):
    invite_url = f"{settings.FRONTEND_URL}/accept-invite?token={token}"
    send_mail(
        subject=f"You're invited to join {tenant_name}",
        message=(
            f"Hi {name},\n\n"
            f"You have been invited to join {tenant_name}.\n\n"
            f"Click the link below to set your password and activate your account:\n"
            f"{invite_url}\n\n"
            f"This link expires in 48 hours."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
```

---

## ধাপ ৮: Serializers

`auth_tenants/api/serializers.py`:

```python
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from .models import Tenant, OTPVerification, Role, Invitation
from .utils import send_otp_email, send_invitation_email

User = get_user_model()


# ── Register (Tenant Admin — নতুন company) ────────────────────────────────────
class RegisterSerializer(serializers.Serializer):
    name         = serializers.CharField(max_length=255)
    email        = serializers.EmailField()
    password     = serializers.CharField(min_length=8, write_only=True)
    company_name = serializers.CharField(max_length=255)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        slug = slugify(validated_data["company_name"])
        base_slug, counter = slug, 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        tenant = Tenant.objects.create(name=validated_data["company_name"], slug=slug)
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            name=validated_data["name"],
            role="tenant_admin",
            tenant=tenant,
            is_active=False,
        )
        otp = OTPVerification.generate(user.email)
        send_otp_email(user.email, otp.otp_code)
        return user


# ── OTP Verify ────────────────────────────────────────────────────────────────
class VerifyOTPSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            otp = OTPVerification.objects.filter(
                email=data["email"], otp_code=data["otp_code"]
            ).latest("created_at")
        except OTPVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP.")
        if not otp.is_valid():
            raise serializers.ValidationError("OTP expired or already used.")
        data["otp_obj"] = otp
        return data


# ── Accept Invitation (Staff — invite link দিয়ে register) ─────────────────────
class AcceptInvitationSerializer(serializers.Serializer):
    token    = serializers.UUIDField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_token(self, value):
        try:
            invite = Invitation.objects.select_related("tenant", "role").get(token=value)
        except Invitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation token.")
        if not invite.is_valid():
            raise serializers.ValidationError("Invitation expired or already accepted.")
        self.context["invite"] = invite
        return value

    def create(self, validated_data):
        invite = self.context["invite"]
        user = User.objects.create_user(
            email=invite.email,
            password=validated_data["password"],
            name=invite.name,
            role="staff",
            tenant=invite.tenant,
            custom_role=invite.role,
            is_active=True,
        )
        invite.is_accepted = True
        invite.save()
        return user


# ── Role ──────────────────────────────────────────────────────────────────────
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Role
        fields = ["id", "name", "permissions", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_permissions(self, value):
        # permissions একটা list of string হতে হবে
        if not isinstance(value, list):
            raise serializers.ValidationError("permissions must be a list.")
        if not all(isinstance(p, str) for p in value):
            raise serializers.ValidationError("Each permission must be a string.")
        return value


# ── Invitation ────────────────────────────────────────────────────────────────
class InvitationCreateSerializer(serializers.Serializer):
    name     = serializers.CharField(max_length=255)
    email    = serializers.EmailField()
    role_id  = serializers.IntegerField(required=False, allow_null=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate(self, data):
        tenant = self.context["tenant"]
        # Pending invite আছে কিনা check করো
        if Invitation.objects.filter(
            email=data["email"], tenant=tenant,
            is_accepted=False, expires_at__gt=timezone.now()
        ).exists():
            raise serializers.ValidationError("An active invitation already exists for this email.")

        role = None
        if data.get("role_id"):
            try:
                role = Role.objects.get(pk=data["role_id"], tenant=tenant)
            except Role.DoesNotExist:
                raise serializers.ValidationError("Role not found in your tenant.")
        data["role"] = role
        return data

    def create(self, validated_data):
        tenant = self.context["tenant"]
        invited_by = self.context["invited_by"]
        invite = Invitation.objects.create(
            tenant=tenant,
            invited_by=invited_by,
            email=validated_data["email"],
            name=validated_data["name"],
            role=validated_data.get("role"),
            expires_at=timezone.now() + timezone.timedelta(hours=48),
        )
        send_invitation_email(invite.email, invite.name, tenant.name, str(invite.token))
        return invite


class InvitationSerializer(serializers.ModelSerializer):
    role_name    = serializers.CharField(source="role.name", read_only=True)
    invited_by_name = serializers.CharField(source="invited_by.name", read_only=True)

    class Meta:
        model  = Invitation
        fields = ["id", "email", "name", "role_name", "invited_by_name",
                  "is_accepted", "expires_at", "created_at"]


# ── User ──────────────────────────────────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    tenant_name     = serializers.CharField(source="tenant.name", read_only=True)
    custom_role_name = serializers.CharField(source="custom_role.name", read_only=True)

    class Meta:
        model  = User
        fields = ["id", "email", "name", "role", "tenant_name",
                  "custom_role_name", "created_at"]


# ── Tenant ────────────────────────────────────────────────────────────────────
class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tenant
        fields = ["id", "name", "slug", "is_active", "created_at"]
```

---

## ধাপ ৯: Views

`auth_tenants/api/views.py`:

```python
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Tenant, OTPVerification, Role, Invitation
from .serializers import (
    RegisterSerializer, VerifyOTPSerializer, AcceptInvitationSerializer,
    UserSerializer, TenantSerializer, RoleSerializer,
    InvitationCreateSerializer, InvitationSerializer,
)
from .permissions import IsSuperAdmin, IsTenantAdmin

User = get_user_model()


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


# ── Register ──────────────────────────────────────────────────────────────────
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(
            {"detail": "Registration successful. Check your email for OTP."},
            status=status.HTTP_201_CREATED,
        )


# ── OTP Verify ────────────────────────────────────────────────────────────────
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = VerifyOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        otp = s.validated_data["otp_obj"]
        user = User.objects.get(email=otp.email)
        otp.is_used = True
        otp.save()
        user.is_active = True
        user.save()
        return Response(get_tokens(user))


# ── Accept Invitation ─────────────────────────────────────────────────────────
class AcceptInvitationView(APIView):
    """
    Staff invite link এ click করে এই endpoint এ আসবে।
    token + password দিলে account তৈরি হবে, tenant automatically assign হবে।
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        """Invitation valid কিনা check করো (frontend preview এর জন্য)"""
        try:
            invite = Invitation.objects.select_related("tenant", "role").get(token=token)
        except Invitation.DoesNotExist:
            return Response({"detail": "Invalid token."}, status=status.HTTP_404_NOT_FOUND)
        if not invite.is_valid():
            return Response({"detail": "Invitation expired or already accepted."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "email": invite.email,
            "name": invite.name,
            "tenant": invite.tenant.name,
            "role": invite.role.name if invite.role else None,
        })

    def post(self, request, token):
        """Password set করো এবং account activate করো"""
        s = AcceptInvitationSerializer(
            data={**request.data, "token": token},
            context={}
        )
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(get_tokens(user), status=status.HTTP_201_CREATED)


# ── Me ────────────────────────────────────────────────────────────────────────
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


# ── Tenant Profile ────────────────────────────────────────────────────────────
class TenantMeView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        return Response(TenantSerializer(request.user.tenant).data)

    def patch(self, request):
        s = TenantSerializer(request.user.tenant, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)


# ── Role Management (Tenant Admin only) ───────────────────────────────────────
class RoleListView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        roles = Role.objects.filter(tenant=request.user.tenant)
        return Response(RoleSerializer(roles, many=True).data)

    def post(self, request):
        s = RoleSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(tenant=request.user.tenant)
        return Response(s.data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    permission_classes = [IsTenantAdmin]

    def _get_role(self, pk, tenant):
        try:
            return Role.objects.get(pk=pk, tenant=tenant)
        except Role.DoesNotExist:
            return None

    def get(self, request, pk):
        role = self._get_role(pk, request.user.tenant)
        if not role:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(RoleSerializer(role).data)

    def patch(self, request, pk):
        role = self._get_role(pk, request.user.tenant)
        if not role:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        s = RoleSerializer(role, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)

    def delete(self, request, pk):
        role = self._get_role(pk, request.user.tenant)
        if not role:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Invitation Management ─────────────────────────────────────────────────────
class InvitationListView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        invites = Invitation.objects.filter(tenant=request.user.tenant).order_by("-created_at")
        return Response(InvitationSerializer(invites, many=True).data)

    def post(self, request):
        s = InvitationCreateSerializer(
            data=request.data,
            context={"tenant": request.user.tenant, "invited_by": request.user}
        )
        s.is_valid(raise_exception=True)
        invite = s.save()
        return Response(InvitationSerializer(invite).data, status=status.HTTP_201_CREATED)


class InvitationCancelView(APIView):
    permission_classes = [IsTenantAdmin]

    def delete(self, request, pk):
        try:
            invite = Invitation.objects.get(pk=pk, tenant=request.user.tenant, is_accepted=False)
        except Invitation.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Member Management ─────────────────────────────────────────────────────────
class MemberListView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        members = User.objects.filter(tenant=request.user.tenant, role="staff")
        return Response(UserSerializer(members, many=True).data)


class MemberDetailView(APIView):
    permission_classes = [IsTenantAdmin]

    def _get_member(self, pk, tenant):
        try:
            return User.objects.get(pk=pk, tenant=tenant, role="staff")
        except User.DoesNotExist:
            return None

    def patch(self, request, pk):
        """Staff এর role পরিবর্তন করো"""
        member = self._get_member(pk, request.user.tenant)
        if not member:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        role_id = request.data.get("role_id")
        if role_id:
            try:
                role = Role.objects.get(pk=role_id, tenant=request.user.tenant)
            except Role.DoesNotExist:
                return Response({"detail": "Role not found."}, status=status.HTTP_400_BAD_REQUEST)
            member.custom_role = role
            member.save()
        return Response(UserSerializer(member).data)

    def delete(self, request, pk):
        """Staff remove করো"""
        member = self._get_member(pk, request.user.tenant)
        if not member:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Super Admin ───────────────────────────────────────────────────────────────
class TenantListView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        return Response(TenantSerializer(Tenant.objects.all(), many=True).data)
```

---

## ধাপ ১০: URLs

`auth_tenants/api/urls.py`:

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from .views import (
    RegisterView, VerifyOTPView, AcceptInvitationView, MeView,
    TenantMeView,
    RoleListView, RoleDetailView,
    InvitationListView, InvitationCancelView,
    MemberListView, MemberDetailView,
    TenantListView,
)

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path("register/",               RegisterView.as_view()),
    path("verify-otp/",             VerifyOTPView.as_view()),
    path("login/",                  TokenObtainPairView.as_view()),
    path("token/refresh/",          TokenRefreshView.as_view()),
    path("logout/",                 TokenBlacklistView.as_view()),
    path("me/",                     MeView.as_view()),

    # ── Invitation (public — token দিয়ে) ──────────────────────────────────────
    path("invite/<uuid:token>/",    AcceptInvitationView.as_view()),

    # ── Tenant ────────────────────────────────────────────────────────────────
    path("tenant/me/",              TenantMeView.as_view()),

    # ── Roles ─────────────────────────────────────────────────────────────────
    path("tenant/roles/",           RoleListView.as_view()),
    path("tenant/roles/<int:pk>/",  RoleDetailView.as_view()),

    # ── Invitations ───────────────────────────────────────────────────────────
    path("tenant/invitations/",             InvitationListView.as_view()),
    path("tenant/invitations/<int:pk>/",    InvitationCancelView.as_view()),

    # ── Members ───────────────────────────────────────────────────────────────
    path("tenant/members/",             MemberListView.as_view()),
    path("tenant/members/<int:pk>/",    MemberDetailView.as_view()),

    # ── Super Admin ───────────────────────────────────────────────────────────
    path("tenants/",                TenantListView.as_view()),
]
```

`core/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("auth_tenants.api.urls")),
]
```

---

## ধাপ ১১: Admin

`auth_tenants/admin.py`:

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Tenant, OTPVerification, Role, Invitation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ("email", "name", "role", "tenant", "custom_role", "is_active")
    list_filter   = ("role", "is_active", "tenant")
    search_fields = ("email", "name")
    ordering      = ("-created_at",)
    fieldsets = (
        (None,          {"fields": ("email", "password")}),
        ("Info",        {"fields": ("name", "role", "tenant", "custom_role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "name", "password1", "password2", "role", "tenant")}),
    )


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display  = ("name", "slug", "is_active", "created_at")
    search_fields = ("name",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display  = ("name", "tenant", "created_at")
    list_filter   = ("tenant",)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display  = ("email", "tenant", "role", "is_accepted", "expires_at")
    list_filter   = ("tenant", "is_accepted")


@admin.register(OTPVerification)
class OTPAdmin(admin.ModelAdmin):
    list_display  = ("email", "otp_code", "is_used", "expires_at")
```

---

## ধাপ ১২: Migration ও Server

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## API টেস্ট করো

### ── Auth ──────────────────────────────────────────────────────────────────

**Step 1: Register (নতুন Tenant Admin)**

```
POST /api/auth/register/

{
    "name": "Rahim",
    "email": "rahim@example.com",
    "password": "securepass123",
    "company_name": "Rahim Enterprise"
}
```
> Console এ OTP দেখাবে

**Step 2: OTP Verify**

```
POST /api/auth/verify-otp/

{
    "email": "rahim@example.com",
    "otp_code": "123456"
}
```
Response: `{ "access": "...", "refresh": "..." }`

**Step 3: Login**

```
POST /api/auth/login/

{
    "email": "rahim@example.com",
    "password": "securepass123"
}
```

এরপর সব request এ header দাও:
```
Authorization: Bearer <access_token>
```

**Step 4: নিজের info**

```
GET /api/auth/me/
Authorization: Bearer <token>
```

---

### ── Role Management ───────────────────────────────────────────────────────

> শুধু Tenant Admin করতে পারবে। Role গুলো tenant-scoped।

**Step 5: Role বানাও**

```
POST /api/auth/tenant/roles/
Authorization: Bearer <token>

{
    "name": "Support",
    "permissions": ["contacts.view", "conversations.view", "conversations.reply"]
}
```

**Step 6: আরেকটা Role বানাও**

```
POST /api/auth/tenant/roles/
Authorization: Bearer <token>

{
    "name": "Manager",
    "permissions": [
        "contacts.view", "contacts.create", "contacts.edit",
        "campaigns.view", "campaigns.create",
        "conversations.view", "conversations.reply", "conversations.assign"
    ]
}
```

**Step 7: সব Role দেখো**

```
GET /api/auth/tenant/roles/
Authorization: Bearer <token>
```

**Step 8: Role এর permission আপডেট করো**

```
PATCH /api/auth/tenant/roles/1/
Authorization: Bearer <token>

{
    "permissions": ["contacts.view", "conversations.view"]
}
```

**Step 9: Role delete করো**

```
DELETE /api/auth/tenant/roles/1/
Authorization: Bearer <token>
```

---

### ── Invitation Flow ────────────────────────────────────────────────────────

**Step 10: Staff কে Invite পাঠাও**

```
POST /api/auth/tenant/invitations/
Authorization: Bearer <token>

{
    "name": "Karim",
    "email": "karim@example.com",
    "role_id": 2
}
```
> Console এ invitation link দেখাবে:
> `http://localhost:3000/accept-invite?token=<uuid>`

**Step 11: Invitation list দেখো**

```
GET /api/auth/tenant/invitations/
Authorization: Bearer <token>
```

**Step 12: Invitation preview (Staff এর browser থেকে)**

```
GET /api/auth/invite/<token>/
```
Response:
```json
{
    "email": "karim@example.com",
    "name": "Karim",
    "tenant": "Rahim Enterprise",
    "role": "Manager"
}
```

**Step 13: Invitation Accept করো (Staff নিজে password set করবে)**

```
POST /api/auth/invite/<token>/

{
    "password": "karimpass123"
}
```
Response: `{ "access": "...", "refresh": "..." }`
> Karim এখন Rahim Enterprise এর অধীনে Manager role সহ active।

**Step 14: Invitation cancel করো (accept হওয়ার আগে)**

```
DELETE /api/auth/tenant/invitations/1/
Authorization: Bearer <token>
```

---

### ── Member Management ─────────────────────────────────────────────────────

**Step 15: সব member দেখো**

```
GET /api/auth/tenant/members/
Authorization: Bearer <token>
```

**Step 16: Member এর role পরিবর্তন করো**

```
PATCH /api/auth/tenant/members/2/
Authorization: Bearer <token>

{
    "role_id": 1
}
```

**Step 17: Member remove করো**

```
DELETE /api/auth/tenant/members/2/
Authorization: Bearer <token>
```

---

### ── Super Admin ───────────────────────────────────────────────────────────

**Step 18: সব Tenant দেখো (Super Admin only)**

```
GET /api/auth/tenants/
Authorization: Bearer <superadmin_token>
```

---

### ── Logout ────────────────────────────────────────────────────────────────

**Step 19: Logout**

```
POST /api/auth/logout/
Authorization: Bearer <token>

{
    "refresh": "<refresh_token>"
}
```

---

## Permission System কীভাবে কাজ করে

```
Tenant Admin → সব permission আছে (check ছাড়াই)
Staff       → custom_role এর permissions list এ যা আছে শুধু তাই
```

অন্য module এ permission check করতে:

```python
# যেকোনো view এ এভাবে ব্যবহার করো
from auth_tenants.api.permissions import HasTenantPerm

class ContactListView(APIView):
    permission_classes = [HasTenantPerm("contacts.view")]
    ...

class ContactCreateView(APIView):
    permission_classes = [HasTenantPerm("contacts.create")]
    ...
```

Available permissions (convention):
```
contacts.view / contacts.create / contacts.edit / contacts.delete
campaigns.view / campaigns.create / campaigns.send
conversations.view / conversations.reply / conversations.assign
analytics.view
```

---

## সমস্যা হলে

| সমস্যা | সমাধান |
|--------|---------|
| `AUTH_USER_MODEL` error | settings এ `AUTH_USER_MODEL = "auth_tenants.User"` আছে কিনা দেখো |
| Migration error | `db.sqlite3` মুছে আবার `makemigrations` + `migrate` দাও |
| `401 Unauthorized` | Header এ `Bearer <token>` ঠিকমতো দিয়েছ কিনা দেখো |
| Invitation link কাজ করছে না | token UUID format এ আছে কিনা দেখো |
| OTP দেখা যাচ্ছে না | `.env` এ `EMAIL_BACKEND=...console.EmailBackend` আছে কিনা দেখো |

---

## PostgreSQL এ Switch করতে হলে

```bash
pip install psycopg2-binary
```

`.env` আপডেট করো:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=whatsapp_saas
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

```bash
python manage.py migrate
```

---

## সংক্ষেপে পুরো Flow

```
Tenant Admin register → OTP verify → Login
    ↓
Role বানাও (Support, Manager, Sales...)
    ↓
Staff কে invite পাঠাও (email + role assign)
    ↓
Staff invite link এ click করে password set করে
    ↓
Staff automatically ওই Tenant এর অধীনে active
    ↓
Staff login করলে শুধু তার role এর permissions কাজ করবে
```

3 ধরনের user:
- `super_admin` → সব tenant দেখতে পারে
- `tenant_admin` → নিজের tenant manage করে, role বানায়, invite পাঠায়
- `staff` → invite accept করে join করে, custom_role এর permission অনুযায়ী কাজ করে
