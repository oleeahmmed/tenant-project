from django.contrib import messages
from django.shortcuts import redirect

from auth_tenants.mixins import TenantMixin, DashboardMixin, PageContextMixin


class SalesAdminMixin(TenantMixin):
    """🎯 UNIFIED SALES ADMIN MIXIN"""
    module_code = "sales"
    required_permission = "sales.view"


class SalesDashboardAccessMixin(DashboardMixin):
    """🎯 UNIFIED SALES DASHBOARD MIXIN"""
    
    def test_func(self):
        """Dashboard access with sales module check"""
        if not super().test_func():
            return False
        
        user = self.request.user
        
        # Super admin can always access
        if user.role == "super_admin":
            return True
        
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return False
        
        # Check sales module access
        if not tenant.can_access_module("sales"):
            return False
        
        # Check basic sales permission
        return user.has_tenant_permission("sales.view")


class SalesPageContextMixin(PageContextMixin):
    """Sales page context"""
    active_page = "sales"

