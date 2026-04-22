from django.contrib import messages
from django.shortcuts import redirect

from auth_tenants.mixins import TenantMixin, DashboardMixin, PageContextMixin


class PurchaseAdminMixin(TenantMixin):
    """🎯 UNIFIED PURCHASE ADMIN MIXIN"""
    module_code = "purchase"
    required_permission = "purchase.view"


class PurchaseDashboardAccessMixin(DashboardMixin):
    """🎯 UNIFIED PURCHASE DASHBOARD MIXIN"""
    
    def test_func(self):
        """Dashboard access with purchase module check"""
        if not super().test_func():
            return False
        
        user = self.request.user
        
        # Super admin can always access
        if user.role == "super_admin":
            return True
        
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return False
        
        # Check purchase module access
        if not tenant.can_access_module("purchase"):
            return False
        
        # Check basic purchase permission
        return user.has_tenant_permission("purchase.view")


class PurchasePageContextMixin(PageContextMixin):
    """Purchase page context"""
    active_page = "purchase"

