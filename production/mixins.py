from django.contrib import messages
from django.shortcuts import redirect

from auth_tenants.mixins import TenantMixin, DashboardMixin, PageContextMixin


class ProductionAdminMixin(TenantMixin):
    """🎯 UNIFIED PRODUCTION ADMIN MIXIN"""
    module_code = "production"
    required_permission = "production.view"


class ProductionDashboardAccessMixin(DashboardMixin):
    """🎯 UNIFIED PRODUCTION DASHBOARD MIXIN"""
    
    def test_func(self):
        """Dashboard access with production module check"""
        if not super().test_func():
            return False
        
        user = self.request.user
        
        # Super admin can always access
        if user.role == "super_admin":
            return True
        
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return False
        
        # Check production module access
        if not tenant.can_access_module("production"):
            return False
        
        # Check basic production permission
        return user.has_tenant_permission("production.view")


class ProductionPageContextMixin(PageContextMixin):
    """Production page context"""
    active_page = "production"

