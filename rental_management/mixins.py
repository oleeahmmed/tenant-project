from django.contrib import messages
from django.shortcuts import redirect

from auth_tenants.mixins import TenantMixin, DashboardMixin, PageContextMixin


class RentalAdminMixin(TenantMixin):
    """🎯 UNIFIED RENTAL ADMIN MIXIN"""
    module_code = "rental"
    
    def _resolve_permission_codename(self):
        """Auto-resolve permission based on method"""
        if hasattr(self, 'permission_codename') and self.permission_codename:
            return self.permission_codename
        
        method = (self.request.method or "GET").upper()
        if method == "DELETE":
            return "rental.delete"
        elif method in ("POST", "PUT", "PATCH"):
            return "rental.manage"
        else:
            return "rental.view"
    
    def test_func(self):
        """Enhanced permission check with auto-resolved permissions"""
        # Set required_permission dynamically
        self.required_permission = self._resolve_permission_codename()
        return super().test_func()


class RentalDashboardAccessMixin(DashboardMixin):
    """🎯 UNIFIED RENTAL DASHBOARD MIXIN"""
    
    def test_func(self):
        """Dashboard access with rental module check"""
        if not super().test_func():
            return False
        
        user = self.request.user
        
        # Super admin can always access
        if user.role == "super_admin":
            return True
        
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return False
        
        # Check rental module access
        if not tenant.can_access_module("rental"):
            return False
        
        # Check basic rental permission
        return user.has_tenant_permission("rental.view")


class RentalPageContextMixin(PageContextMixin):
    """Rental page context"""
    active_page = "rental"
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = params.urlencode()
        return ctx
