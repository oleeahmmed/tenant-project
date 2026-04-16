from django.contrib import admin

from .models import VaultCategory, VaultEntry, VaultFileAttachment, VaultSharedEntry


@admin.register(VaultCategory)
class VaultCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "customer", "is_active")
    list_filter = ("tenant", "is_active")
    search_fields = ("name", "customer__name")


@admin.register(VaultEntry)
class VaultEntryAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "project", "category", "is_favorite")
    list_filter = ("tenant", "is_favorite")
    search_fields = ("name", "username", "project__key", "project__name", "category__name", "category__customer__name")


@admin.register(VaultFileAttachment)
class VaultFileAttachmentAdmin(admin.ModelAdmin):
    list_display = ("entry", "tenant", "title", "created_at")
    list_filter = ("tenant",)


@admin.register(VaultSharedEntry)
class VaultSharedEntryAdmin(admin.ModelAdmin):
    list_display = ("entry", "shared_with_email", "permission", "is_active", "expires_at")
    list_filter = ("tenant", "permission", "is_active")
