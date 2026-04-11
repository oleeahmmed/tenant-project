"""
Custom Admin Configuration for Django Auth Models
Register User and Group with Unfold Admin
"""
from django.contrib import admin
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.contenttypes.models import ContentType
from unfold.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _


# Unregister default User and Group admin
admin.site.unregister(User)
admin.site.unregister(Group)


# ==================== USER ADMIN ====================
@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Custom User Admin with Unfold styling"""
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['-date_joined']
    
    fieldsets = (
        (_('Login Information'), {
            'fields': ('username', 'password'),
            'classes': ['tab'],
        }),
        (_('Personal Information'), {
            'fields': ('first_name', 'last_name', 'email'),
            'classes': ['tab'],
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
            'classes': ['tab'],
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ['tab'],
        }),
    )
    
    add_fieldsets = (
        (_('Create New User'), {
            'classes': ['wide'],
            'fields': ('username', 'password1', 'password2'),
        }),
        (_('Personal Information'), {
            'classes': ['wide'],
            'fields': ('first_name', 'last_name', 'email'),
        }),
        (_('Permissions'), {
            'classes': ['wide'],
            'fields': ('is_staff', 'is_active'),
        }),
    )
    
    filter_horizontal = ['groups', 'user_permissions']


# ==================== GROUP ADMIN ====================
@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    """Custom Group Admin with Unfold styling"""
    
    list_display = ['name', 'permission_count']
    search_fields = ['name']
    ordering = ['name']
    filter_horizontal = ['permissions']
    
    fieldsets = (
        (_('Group Information'), {
            'fields': ('name',),
            'classes': ['tab'],
        }),
        (_('Permissions'), {
            'fields': ('permissions',),
            'classes': ['tab'],
        }),
    )
    
    def permission_count(self, obj):
        """Display number of permissions in the group"""
        return obj.permissions.count()
    permission_count.short_description = _('Permissions')


# ==================== PERMISSION ADMIN ====================
@admin.register(Permission)
class PermissionAdmin(ModelAdmin):
    """Permission Admin - for viewing/managing permissions"""
    
    list_display = ['name', 'content_type', 'codename', 'app_label']
    list_filter = ['content_type__app_label']
    search_fields = ['name', 'codename', 'content_type__app_label', 'content_type__model']
    ordering = ['content_type__app_label', 'content_type__model', 'codename']
    
    fieldsets = (
        (_('Permission Information'), {
            'fields': ('name', 'content_type', 'codename'),
        }),
    )
    
    def app_label(self, obj):
        """Display app label"""
        return obj.content_type.app_label
    app_label.short_description = _('App')
    app_label.admin_order_field = 'content_type__app_label'
    
    def has_add_permission(self, request):
        """Disable adding permissions manually"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting permissions"""
        return False


# ==================== CONTENT TYPE ADMIN (Optional) ====================
@admin.register(ContentType)
class ContentTypeAdmin(ModelAdmin):
    """ContentType Admin - for viewing content types"""
    
    list_display = ['app_label', 'model', 'id']
    list_filter = ['app_label']
    search_fields = ['app_label', 'model']
    ordering = ['app_label', 'model']
    
    def has_add_permission(self, request):
        """Disable adding content types manually"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting content types"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing content types"""
        return False

