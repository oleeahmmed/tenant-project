from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from hrm.mixins import WorkspaceTenantDashboardMixin
from hrm.tenant_scope import get_hrm_tenant, user_belongs_to_workspace_tenant


class FoundationAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Same tenant resolution as HRM admin pages."""

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


class FoundationPageContextMixin:
    active_page = "foundation"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if getattr(self, "page_title", None):
            ctx.setdefault("page_title", self.page_title)
        return ctx


# Re-export for foundation dashboard (same access rules as HRM dashboard).
FoundationDashboardAccessMixin = WorkspaceTenantDashboardMixin
