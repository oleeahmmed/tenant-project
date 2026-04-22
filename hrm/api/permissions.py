from rest_framework.permissions import BasePermission
from auth_tenants.permissions import TenantManager


class IsHrmTenantAdmin(BasePermission):
    """🎯 UNIFIED HRM Admin Permission - Uses generic tenant system"""

    def has_permission(self, request, view):
        u = request.user
        if not u.is_authenticated:
            return False
        
        t = TenantManager.get_tenant(request)
        if t is None:
            return False
        
        role = getattr(u, "role", None)
        if role == "super_admin":
            return True
        
        if role not in ("tenant_admin", "staff"):
            return False
        
        if not TenantManager.user_belongs_to_tenant(u, t):
            return False
        
        if role == "tenant_admin":
            return True
        
        required = getattr(view, "required_permission", "hrm.api.admin")
        return u.has_tenant_permission(required)
