"""
🎯 ULTIMATE PERMISSION SYSTEM
Single file that handles EVERYTHING - permissions, tenants, modules, mixins, API views
Zero dependencies, completely self-contained
"""
from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.template import Library
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

User = get_user_model()

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 CORE TENANT & MODULE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class TenantManager:
    """🎯 Complete tenant management - replaces all HRM functions"""
    
    SESSION_KEY = "active_tenant_id"
    
    @staticmethod
    def get_tenant(request):
        """Get tenant from request - works for all user types"""
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        user = request.user
        
        # Super admin can switch tenants via session
        if user.role == "super_admin":
            tenant_id = request.session.get(TenantManager.SESSION_KEY)
            if tenant_id:
                try:
                    from .models import Tenant
                    return Tenant.objects.get(pk=tenant_id, is_active=True)
                except Tenant.DoesNotExist:
                    pass
            # Default to first active tenant
            from .models import Tenant
            return Tenant.objects.filter(is_active=True).first()
        
        # Regular users use their assigned tenant
        return user.tenant if user.tenant and user.tenant.is_active else None
    
    @staticmethod
    def user_belongs_to_tenant(user, tenant):
        """Check if user can access this tenant"""
        if not user or not user.is_authenticated or not tenant:
            return False
        
        # Super admin can access any tenant
        if user.role == "super_admin":
            return True
        
        # Others must match their assigned tenant
        return user.tenant_id == tenant.id
    
    @staticmethod
    def set_active_tenant(request, tenant_id):
        """Set active tenant (super admin only)"""
        if request.user.role == "super_admin":
            request.session[TenantManager.SESSION_KEY] = tenant_id
            return True
        return False


class ModuleManager:
    """🎯 Complete module management - dynamic discovery"""
    
    @staticmethod
    def get_installed_modules():
        """Auto-discover all installed modules from settings.LOCAL_APPS"""
        modules = {}
        
        # Get LOCAL_APPS from settings
        local_apps = getattr(settings, 'LOCAL_APPS', [])
        
        for app_label in local_apps:
            try:
                app_config = apps.get_app_config(app_label)
                
                # Map app to module code
                module_code = app_label
                if app_label == 'rental_management':
                    module_code = 'rental'
                
                if module_code not in modules:
                    modules[module_code] = []
                modules[module_code].append(app_label)
                
            except LookupError:
                continue
        
        return modules
    
    @staticmethod
    def get_workspace_modules():
        """Get modules for navigation"""
        modules = ModuleManager.get_installed_modules()
        
        # Core modules always included
        core_modules = ['auth_tenants', 'foundation']
        
        # Get all modules except excluded ones
        excluded = ['config', 'ui', 'tests', 'tmp_uploads', 'media', 'venv']
        workspace_modules = [m for m in modules.keys() if m not in excluded]
        
        # Add core modules if missing
        for core in core_modules:
            if core not in workspace_modules:
                workspace_modules.append(core)
        
        return sorted(workspace_modules)
    
    @staticmethod
    def can_access_module(user, tenant, module_code):
        """Check if user can access a module"""
        if not user or not user.is_authenticated:
            return False
        
        # Super admin can access everything
        if user.role == "super_admin":
            return True
        
        if not tenant:
            return False
        
        # Check subscription access
        if not tenant.can_access_module(module_code):
            return False
        
        # Check user permissions
        return PermissionManager.has_module_permission(user, module_code)


class PermissionManager:
    """🎯 Complete permission management"""
    
    CRUD_ACTIONS = ("view", "add", "change", "delete")
    MODULE_ACTIONS = ("view", "manage", "delete")
    

    
    @staticmethod
    def has_module_permission(user, module_code):
        """Check if user has any permission in module"""
        # Check module-level permissions
        for action in PermissionManager.MODULE_ACTIONS:
            if user.has_tenant_permission(f"{module_code}.{action}"):
                return True
        
        # Check model-level permissions
        modules = ModuleManager.get_installed_modules()
        for app_label in modules.get(module_code, []):
            try:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    model_name = model._meta.model_name
                    for action in PermissionManager.CRUD_ACTIONS:
                        codename = f"{app_label}.{model_name}.{action}"
                        if user.has_tenant_permission(codename):
                            return True
            except LookupError:
                continue
        
        return False
    
    @staticmethod
    def get_navigation_flags(user, tenant):
        """Get module visibility flags for navigation"""
        flags = {}
        modules = ModuleManager.get_workspace_modules()
        
        for module in modules:
            flags[module] = ModuleManager.can_access_module(user, tenant, module)
        
        # Special flags
        workspace_modules = [m for m in modules if m != "chat"]
        flags["any_workspace"] = any(flags[m] for m in workspace_modules)
        
        return flags

# ═══════════════════════════════════════════════════════════════════════════════
# 🛡️ PERMISSION CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class IsSuperAdmin(BasePermission):
    """Super admin only"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "super_admin"


class IsTenantAdmin(BasePermission):
    """Tenant admin or super admin"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("super_admin", "tenant_admin")


class IsAuthenticated(BasePermission):
    """Authenticated user with valid tenant"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        tenant = TenantManager.get_tenant(request)
        return tenant is not None


class HasModuleAccess(BasePermission):
    """Check module access based on subscription and permissions"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get module from view
        module_code = getattr(view, 'module_code', None)
        if not module_code:
            return True  # No module restriction
        
        tenant = TenantManager.get_tenant(request)
        return ModuleManager.can_access_module(request.user, tenant, module_code)


class HasPermission(BasePermission):
    """Check specific permission"""
    
    def __init__(self, permission):
        self.permission = permission
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.role == "super_admin":
            return True
        
        return request.user.has_tenant_permission(self.permission)


def RequirePermission(permission):
    """Factory for permission classes"""
    class _Permission(HasPermission):
        def __init__(self):
            super().__init__(permission)
    
    _Permission.__name__ = f"Require_{permission.replace('.', '_')}"
    return _Permission


class IsSameTenant(BasePermission):
    """Object-level: user can only access their tenant's data"""
    def has_object_permission(self, request, view, obj):
        tenant = TenantManager.get_tenant(request)
        return tenant is not None and getattr(obj, "tenant", None) == tenant

# ═══════════════════════════════════════════════════════════════════════════════
# 🏗️ API VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class TenantAPIView(APIView):
    """
    🎯 ULTIMATE API VIEW
    Use this for ALL your API views - handles everything automatically!
    
    Example:
    class MyAPIView(TenantAPIView):
        module_code = "inventory"
        required_permission = "inventory.view"
        
        def get(self, request):
            tenant = self.get_tenant()
            return self.success_response({"message": "Hello!"})
    """
    
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    # Override these in your views
    module_code = None          # e.g., "inventory", "hrm", "rental"
    required_permission = None  # e.g., "inventory.view", "hrm.manage"
    
    def dispatch(self, request, *args, **kwargs):
        """Auto-check permissions before processing request"""
        
        # Get tenant (always required)
        self.tenant = TenantManager.get_tenant(request)
        if not self.tenant:
            return self.error_response("No tenant found", status.HTTP_403_FORBIDDEN)
        
        # Check if user belongs to tenant
        if not TenantManager.user_belongs_to_tenant(request.user, self.tenant):
            return self.error_response("Access denied", status.HTTP_403_FORBIDDEN)
        
        # Check module access
        if self.module_code:
            if not ModuleManager.can_access_module(request.user, self.tenant, self.module_code):
                return self.error_response(
                    f"Module '{self.module_code}' not available in your plan",
                    status.HTTP_403_FORBIDDEN
                )
        
        # Check specific permission
        if self.required_permission:
            if request.user.role != "super_admin":
                if not request.user.has_tenant_permission(self.required_permission):
                    return self.error_response(
                        f"Permission '{self.required_permission}' required",
                        status.HTTP_403_FORBIDDEN
                    )
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_tenant(self):
        """Get current tenant (always available after dispatch)"""
        return getattr(self, 'tenant', None)
    
    def error_response(self, message, code=status.HTTP_400_BAD_REQUEST, **extra):
        """Standard error response"""
        data = {"ok": False, "error": message}
        data.update(extra)
        return Response(data, status=code)
    
    def success_response(self, data=None, code=status.HTTP_200_OK, **extra):
        """Standard success response"""
        response = {"ok": True}
        if data is not None:
            response["data"] = data
        response.update(extra)
        return Response(response, status=code)


# Legacy compatibility class
class TenantScopedApiView(TenantAPIView):
    """🎯 LEGACY COMPATIBILITY - Use TenantAPIView for new code"""
    
    def get_tenant(self):
        if hasattr(self, "_tenant_scope"):
            return self._tenant_scope
        
        tenant = TenantManager.get_tenant(self.request)
        if tenant is None:
            self.permission_denied(self.request, message="No workspace tenant selected.")
        
        if not TenantManager.user_belongs_to_tenant(self.request.user, tenant):
            self.permission_denied(self.request, message="User is outside workspace tenant.")
        
        if self.module_code and not tenant.can_access_module(self.module_code):
            self.permission_denied(self.request, message=f"{self.module_code} module is disabled.")
        
        if (
            self.required_permission
            and self.request.user.role != "super_admin"
            and not self.request.user.has_tenant_permission(self.required_permission)
        ):
            self.permission_denied(self.request, message="Missing permission.")
        
        self._tenant_scope = tenant
        return tenant

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_tenant(request):
    """Quick function to get tenant from request"""
    return TenantManager.get_tenant(request)

def user_belongs_to_tenant(user, tenant):
    """Quick function to check user-tenant relationship"""
    return TenantManager.user_belongs_to_tenant(user, tenant)

def can_access_module(request, module_code):
    """Quick function to check module access"""
    tenant = get_tenant(request)
    return ModuleManager.can_access_module(request.user, tenant, module_code)

def get_navigation_flags(request):
    """Quick function to get navigation flags"""
    tenant = get_tenant(request)
    return PermissionManager.get_navigation_flags(request.user, tenant)

def has_permission(request, permission):
    """Quick function to check permission"""
    if request.user.role == "super_admin":
        return True
    return request.user.has_tenant_permission(permission)

# ═══════════════════════════════════════════════════════════════════════════════
# 🏷️ TEMPLATE TAGS
# ═══════════════════════════════════════════════════════════════════════════════

register = Library()

@register.simple_tag(takes_context=True)
def workspace_nav(context):
    """
    🎯 NAVIGATION FLAGS
    Usage: {% workspace_nav as nav %}
    """
    request = context["request"]
    return get_navigation_flags(request)

@register.filter
def module_enabled(tenant, module_code):
    """
    🎯 MODULE CHECK
    Usage: {{ tenant|module_enabled:"inventory" }}
    """
    if not tenant:
        return False
    return tenant.can_access_module(module_code)

@register.simple_tag(takes_context=True)
def current_tenant(context):
    """
    🎯 GET CURRENT TENANT
    Usage: {% current_tenant as tenant %}
    """
    request = context["request"]
    return get_tenant(request)

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_tenant(request):
    """Quick function to get tenant from request"""
    return TenantManager.get_tenant(request)

def can_access_module(request, module_code):
    """Quick function to check module access"""
    tenant = get_tenant(request)
    return ModuleManager.can_access_module(request.user, tenant, module_code)

def get_navigation_flags(request):
    """Quick function to get navigation flags"""
    tenant = get_tenant(request)
    return PermissionManager.get_navigation_flags(request.user, tenant)

def has_permission(request, permission):
    """Quick function to check permission"""
    if request.user.role == "super_admin":
        return True
    return request.user.has_tenant_permission(permission)

# ═══════════════════════════════════════════════════════════════════════════════
# 🏷️ EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Core managers
    'TenantManager',
    'ModuleManager', 
    'PermissionManager',
    
    # Permission classes
    'IsSuperAdmin',
    'IsTenantAdmin',
    'IsAuthenticated',
    'HasModuleAccess',
    'RequirePermission',
    'IsSameTenant',
    
    # API views
    'TenantAPIView',
    'TenantScopedApiView',  # Legacy
    
    # Convenience functions
    'get_tenant',
    'user_belongs_to_tenant',
    'can_access_module',
    'get_navigation_flags',
    'has_permission',
    
    # Template tags
    'register',
]