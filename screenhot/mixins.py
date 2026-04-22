from django.contrib import messages
from django.shortcuts import redirect

from auth_tenants.mixins import TenantMixin, DashboardMixin, PageContextMixin


class ScreenhotModuleAdminMixin(TenantMixin):
    """🎯 UNIFIED SCREENHOT ADMIN MIXIN"""
    module_code = "screenhot"
    required_permission = "screenhot.view"


class ScreenhotDashboardAccessMixin(DashboardMixin):
    """🎯 UNIFIED SCREENHOT DASHBOARD MIXIN"""
    
    def test_func(self):
        """Dashboard access with screenhot module check"""
        if not super().test_func():
            return False
        
        user = self.request.user
        
        # Super admin can always access
        if user.role == "super_admin":
            return True
        
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return False
        
        # Check screenhot module access
        if not tenant.can_access_module("screenhot"):
            return False
        
        # Check basic screenhot permission
        return user.has_tenant_permission("screenhot.view")


class ScreenhotPageContextMixin(PageContextMixin):
    """Screenhot page context"""
    active_page = "screenhot"
