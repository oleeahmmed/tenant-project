from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from auth_tenants.permissions import get_tenant, TenantManager
from auth_tenants.mixins import TenantMixin, DashboardMixin, PageContextMixin


class InventoryAdminMixin(TenantMixin):
    """🎯 UNIFIED INVENTORY ADMIN MIXIN"""
    module_code = "inventory"
    
    def _resolve_permission_codename(self):
        """Auto-resolve permission based on view and method"""
        explicit = getattr(self, "permission_codename", "") or ""
        if explicit:
            return explicit

        method = (self.request.method or "GET").upper()
        model = getattr(self, "model", None)
        
        if model is not None and hasattr(model, "_meta"):
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            action = "view"
            
            if method == "DELETE":
                action = "delete"
            elif method in ("POST", "PUT", "PATCH"):
                if "Create" in self.__class__.__name__:
                    action = "add"
                elif "Delete" in self.__class__.__name__:
                    action = "delete"
                elif "Update" in self.__class__.__name__:
                    action = "change"
                else:
                    action = "change"
            
            return f"{app_label}.{model_name}.{action}"

        # Fallback to module permissions
        if method == "DELETE":
            return "inventory.delete"
        elif method in ("POST", "PUT", "PATCH"):
            return "inventory.manage"
        else:
            return "inventory.view"
    
    def test_func(self):
        """Enhanced permission check with auto-resolved permissions"""
        # Set required_permission dynamically
        self.required_permission = self._resolve_permission_codename()
        return super().test_func()


class InventoryPageContextMixin(PageContextMixin):
    """Inventory page context"""
    active_page = "inventory"


class InventoryDashboardAccessMixin(DashboardMixin):
    """🎯 UNIFIED INVENTORY DASHBOARD MIXIN"""
    
    def test_func(self):
        """Dashboard access with inventory module check"""
        if not super().test_func():
            return False
        
        user = self.request.user
        
        # Super admin can always access
        if user.role == "super_admin":
            return True
        
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return False
        
        # Check inventory module access
        if not tenant.can_access_module("inventory"):
            return False
        
        # Check basic inventory permission
        return user.has_tenant_permission("inventory.view")
