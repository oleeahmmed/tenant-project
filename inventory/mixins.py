from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from hrm.tenant_scope import get_hrm_tenant, user_belongs_to_workspace_tenant


class InventoryAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Same tenant gate as Foundation / HRM admin."""

    def dispatch(self, request, *args, **kwargs):
        request.hrm_tenant = get_hrm_tenant(request)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        u = self.request.user
        t = getattr(self.request, "hrm_tenant", None)
        if not u.is_authenticated or t is None:
            return False
        if u.role == "super_admin":
            return True
        return user_belongs_to_workspace_tenant(u, t)

    def handle_no_permission(self):
        u = self.request.user
        if (
            u.is_authenticated
            and getattr(u, "role", None) == "super_admin"
            and getattr(self.request, "hrm_tenant", None) is None
        ):
            messages.warning(
                self.request,
                "Choose a workspace tenant on the HRM dashboard before opening this page.",
            )
        else:
            messages.error(self.request, "No tenant is assigned to your account.")
        return redirect("dashboard")


class InventoryPageContextMixin:
    active_page = "inventory"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if getattr(self, "page_title", None):
            ctx.setdefault("page_title", self.page_title)
        return ctx


class InventoryDashboardAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Dashboard: super_admin may open without tenant (pick workspace)."""

    def dispatch(self, request, *args, **kwargs):
        request.hrm_tenant = get_hrm_tenant(request)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        u = self.request.user
        if not u.is_authenticated:
            return False
        if u.role == "super_admin":
            return True
        t = getattr(self.request, "hrm_tenant", None)
        if t is None:
            return False
        return user_belongs_to_workspace_tenant(u, t)

    def handle_no_permission(self):
        messages.error(self.request, "No tenant is assigned to your account.")
        return redirect("dashboard")
