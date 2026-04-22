"""
🎯 DJANGO VIEW MIXINS
All Django view mixins for tenant-based access control
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from auth_tenants.permissions import get_tenant, TenantManager, ModuleManager


class TenantMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    🎯 BASE TENANT MIXIN
    Use this for ALL your Django views that need tenant access
    
    Example:
    class MyView(TenantMixin, ListView):
        module_code = "inventory"
        required_permission = "inventory.view"
        model = Product
    """
    
    # Override these in your views
    module_code = None              # e.g., "inventory", "hrm", "rental"
    required_permission = None      # e.g., "inventory.view", "hrm.manage"
    
    def dispatch(self, request, *args, **kwargs):
        """Auto-attach tenant to request"""
        request.tenant = get_tenant(request)
        return super().dispatch(request, *args, **kwargs)
    
    def test_func(self):
        """Check all permissions"""
        user = self.request.user
        tenant = getattr(self.request, 'tenant', None)
        
        if not user.is_authenticated or not tenant:
            return False
        
        # Super admin can access everything
        if user.role == "super_admin":
            return True
        
        # Check if user belongs to tenant
        if not TenantManager.user_belongs_to_tenant(user, tenant):
            return False
        
        # Check module access
        if self.module_code:
            if not ModuleManager.can_access_module(user, tenant, self.module_code):
                return False
        
        # Check specific permission
        if self.required_permission:
            if not user.has_tenant_permission(self.required_permission):
                return False
        
        return True
    
    def handle_no_permission(self):
        """Handle permission denied"""
        user = self.request.user
        
        if not user.is_authenticated:
            return super().handle_no_permission()
        
        tenant = getattr(self.request, 'tenant', None)
        
        if not tenant:
            messages.error(self.request, "No tenant assigned to your account.")
        elif self.module_code and not tenant.can_access_module(self.module_code):
            messages.error(self.request, f"Module '{self.module_code}' not available in your plan.")
        else:
            messages.error(self.request, "Access denied.")
        
        return redirect("dashboard")


class AdminMixin(TenantMixin):
    """
    🎯 ADMIN ACCESS MIXIN
    For admin-only views (tenant_admin + super_admin)
    """
    
    def test_func(self):
        """Admin access check"""
        if not super().test_func():
            return False
        
        user = self.request.user
        return user.role in ("super_admin", "tenant_admin")


class DashboardMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    🎯 DASHBOARD ACCESS MIXIN
    For dashboard views (super_admin can access without tenant)
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Auto-attach tenant to request"""
        request.tenant = get_tenant(request)
        return super().dispatch(request, *args, **kwargs)
    
    def test_func(self):
        """Dashboard access check"""
        user = self.request.user
        
        if not user.is_authenticated:
            return False
        
        # Super admin can always access dashboard
        if user.role == "super_admin":
            return True
        
        # Others need valid tenant
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            return False
        
        return TenantManager.user_belongs_to_tenant(user, tenant)
    
    def handle_no_permission(self):
        """Handle permission denied"""
        messages.error(self.request, "Access denied.")
        return redirect("login")


class PageContextMixin:
    """
    🎯 PAGE CONTEXT MIXIN
    Add common context data to views
    """
    
    active_page = None
    page_title = None
    
    def get_context_data(self, **kwargs):
        """Add common context"""
        context = super().get_context_data(**kwargs)
        
        if self.active_page:
            context["active_page"] = self.active_page
        
        if self.page_title:
            context["page_title"] = self.page_title
        
        return context


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 CONVENIENCE MIXINS
# ═══════════════════════════════════════════════════════════════════════════════

class InventoryMixin(TenantMixin, PageContextMixin):
    """Inventory module mixin"""
    module_code = "inventory"
    active_page = "inventory"


class HRMMixin(TenantMixin, PageContextMixin):
    """HRM module mixin"""
    module_code = "hrm"
    active_page = "hrm"


class FinanceMixin(TenantMixin, PageContextMixin):
    """Finance module mixin"""
    module_code = "finance"
    active_page = "finance"


class RentalMixin(TenantMixin, PageContextMixin):
    """Rental module mixin"""
    module_code = "rental"
    active_page = "rental"


class SchoolMixin(TenantMixin, PageContextMixin):
    """School module mixin"""
    module_code = "school"
    active_page = "school"


# ═══════════════════════════════════════════════════════════════════════════════
# 🏷️ EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Base mixins
    'TenantMixin',
    'AdminMixin',
    'DashboardMixin',
    'PageContextMixin',
    
    # Module mixins
    'InventoryMixin',
    'HRMMixin',
    'FinanceMixin',
    'RentalMixin',
    'SchoolMixin',
]