from django.contrib import messages
from django.shortcuts import redirect

from auth_tenants.mixins import TenantMixin, DashboardMixin, PageContextMixin


class SchoolAdminMixin(TenantMixin):
    """🎯 UNIFIED SCHOOL ADMIN MIXIN"""
    module_code = "school"
    
    def _resolve_permission_codename(self):
        """Auto-resolve permission based on method"""
        if hasattr(self, 'permission_codename') and self.permission_codename:
            return self.permission_codename
        
        method = (self.request.method or "GET").upper()
        if method == "DELETE":
            return "school.delete"
        elif method in ("POST", "PUT", "PATCH"):
            return "school.manage"
        else:
            return "school.view"
    
    def test_func(self):
        """Enhanced permission check with auto-resolved permissions"""
        # Set required_permission dynamically
        self.required_permission = self._resolve_permission_codename()
        return super().test_func()


class SchoolPageContextMixin(PageContextMixin):
    """School page context"""
    active_page = "school"
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = params.urlencode()
        return ctx
