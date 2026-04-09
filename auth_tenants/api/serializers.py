from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework import serializers
from auth_tenants.models import Tenant, OTPVerification, Role, Invitation, Permission
from .utils import send_otp_email, send_invitation_email

User = get_user_model()


# ── Permission (Super Admin) ──────────────────────────────────────────────────
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Permission
        fields = ["id", "codename", "label", "category", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


# ── Register ──────────────────────────────────────────────────────────────────
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


# ── Accept Invitation ─────────────────────────────────────────────────────────
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
    # write: permission id list পাঠাও
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.filter(is_active=True),
        many=True, write_only=True, required=False, source="permissions"
    )
    # read: codename list দেখাবে
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model  = Role
        fields = ["id", "name", "permissions", "permission_ids", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        perms = validated_data.pop("permissions", [])
        role  = Role.objects.create(**validated_data)
        role.permissions.set(perms)
        return role

    def update(self, instance, validated_data):
        perms = validated_data.pop("permissions", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if perms is not None:
            instance.permissions.set(perms)
        return instance


# ── Invitation ────────────────────────────────────────────────────────────────
class InvitationCreateSerializer(serializers.Serializer):
    name    = serializers.CharField(max_length=255)
    email   = serializers.EmailField()
    role_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate(self, data):
        tenant = self.context["tenant"]
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
        tenant     = self.context["tenant"]
        invited_by = self.context["invited_by"]
        request    = self.context.get("request")
        invite = Invitation.objects.create(
            tenant=tenant,
            invited_by=invited_by,
            email=validated_data["email"],
            name=validated_data["name"],
            role=validated_data.get("role"),
            expires_at=timezone.now() + timezone.timedelta(hours=48),
        )
        invite_url = None
        if request:
            invite_url = request.build_absolute_uri(
                reverse("invite_accept", kwargs={"token": invite.token})
            )
        send_invitation_email(invite.email, invite.name, tenant.name, str(invite.token), invite_url=invite_url)
        return invite


class InvitationSerializer(serializers.ModelSerializer):
    role_name       = serializers.CharField(source="role.name", read_only=True)
    invited_by_name = serializers.CharField(source="invited_by.name", read_only=True)

    class Meta:
        model  = Invitation
        fields = ["id", "email", "name", "role_name", "invited_by_name",
                  "is_accepted", "expires_at", "created_at"]


# ── User ──────────────────────────────────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    tenant_name       = serializers.CharField(source="tenant.name", read_only=True)
    custom_role_name  = serializers.CharField(source="custom_role.name", read_only=True)
    effective_permissions = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ["id", "email", "name", "role", "tenant_name",
                  "custom_role_name", "effective_permissions", "created_at"]

    def get_effective_permissions(self, obj):
        if obj.role in ("super_admin", "tenant_admin"):
            return "__all__"
        return sorted(obj.get_all_permissions_set())


# ── Member Permission Update ──────────────────────────────────────────────────
class MemberPermissionSerializer(serializers.Serializer):
    """
    Tenant Admin member এর extra_permissions directly add/remove করবে।
    শুধু master list এর active permission গুলো দেওয়া যাবে।
    """
    add_permission_ids    = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.filter(is_active=True),
        many=True, required=False
    )
    remove_permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.filter(is_active=True),
        many=True, required=False
    )


# ── Tenant ────────────────────────────────────────────────────────────────────
class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tenant
        fields = ["id", "name", "slug", "is_active", "created_at"]
