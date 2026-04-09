from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Tenant, OTPVerification, Role, Invitation, Permission


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ("email", "name", "role", "tenant", "custom_role", "is_active")
    list_filter    = ("role", "is_active", "tenant")
    search_fields  = ("email", "name")
    ordering       = ("-created_at",)
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
    list_display = ("name", "tenant", "created_at")
    list_filter  = ("tenant",)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "tenant", "role", "is_accepted", "expires_at")
    list_filter  = ("tenant", "is_accepted")


@admin.register(OTPVerification)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("email", "otp_code", "is_used", "expires_at")


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display  = ("codename", "label", "category", "is_active")
    list_filter   = ("category", "is_active")
    search_fields = ("codename", "label")
