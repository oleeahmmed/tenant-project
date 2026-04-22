from django.contrib import messages
from django.shortcuts import redirect

from auth_tenants.mixins import TenantMixin, DashboardMixin, PageContextMixin


class VaultAdminMixin(TenantMixin):
    """🎯 UNIFIED VAULT ADMIN MIXIN"""
    module_code = "vault"
    required_permission = "vault.view"


class VaultDashboardAccessMixin(DashboardMixin):
    """🎯 UNIFIED VAULT DASHBOARD MIXIN"""
    
    def test_func(self):
        """Dashboard access with vault module check"""
        if not super().test_func():
            return False
        
        user = self.request.user
        
        # Super admin can always access
        if user.role == "super_admin":
            return True
        
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return False
        
        # Check vault module access
        if not tenant.can_access_module("vault"):
            return False
        
        # Check basic vault permission
        return user.has_tenant_permission("vault.view")


class VaultPageContextMixin(PageContextMixin):
    """Vault page context"""
    active_page = "vault"
