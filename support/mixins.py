from django.contrib import messages
from django.shortcuts import redirect

from auth_tenants.mixins import TenantMixin, DashboardMixin, PageContextMixin


class SupportModuleAdminMixin(TenantMixin):
    """🎯 UNIFIED SUPPORT ADMIN MIXIN"""
    module_code = "support"
    required_permission = "support.view"


class SupportDashboardAccessMixin(DashboardMixin):
    """🎯 UNIFIED SUPPORT DASHBOARD MIXIN"""
    
    def test_func(self):
        """Dashboard access with support module check"""
        if not super().test_func():
            return False
        
        user = self.request.user
        
        # Super admin can always access
        if user.role == "super_admin":
            return True
        
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return False
        
        # Check support module access
        if not tenant.can_access_module("support"):
            return False
        
        # Check basic support permission
        return user.has_tenant_permission("support.view")


class SupportPageContextMixin(PageContextMixin):
    """Support page context"""
    active_page = "support"
