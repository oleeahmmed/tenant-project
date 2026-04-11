from django.contrib import messages
from django.shortcuts import redirect

from foundation.mixins import FoundationAdminMixin, FoundationDashboardAccessMixin


class FinanceAdminMixin(FoundationAdminMixin):
    """Finance admin pages follow same tenant guard as foundation/hrm."""
    permission_codename_read = "finance.view"
    permission_codename_write = "finance.manage"
    permission_codename_delete = "finance.delete"

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("finance"):
            messages.error(request, "Finance module is disabled for this tenant.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class FinanceDashboardAccessMixin(FoundationDashboardAccessMixin):
    """Finance dashboard keeps same access behavior as HRM/Foundation."""

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("finance"):
            messages.error(request, "Finance module is disabled for this tenant.")
            return redirect("dashboard")
        if (
            getattr(request.user, "role", None) in ("staff", "tenant_admin")
            and tenant is not None
            and not request.user.has_tenant_permission("finance.view")
        ):
            messages.error(request, "You do not have permission for this Finance action.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class FinancePageContextMixin:
    active_page = "finance"
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if self.page_title:
            ctx.setdefault("page_title", self.page_title)
        return ctx


class FinancePostOnlyMixin:
    http_method_names = ["post"]

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect("dashboard")


class FinancePermissionRequiredMixin:
    permission_codename = ""

    def dispatch(self, request, *args, **kwargs):
        if self.permission_codename and not request.user.has_tenant_permission(self.permission_codename):
            messages.error(request, "You do not have permission for this action.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

