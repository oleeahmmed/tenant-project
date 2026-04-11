from django.contrib import messages
from django.shortcuts import redirect

from foundation.mixins import FoundationAdminMixin, FoundationDashboardAccessMixin


class PurchaseAdminMixin(FoundationAdminMixin):
    """Purchase follows the same tenant and role rules as Foundation."""
    permission_codename_read = "purchase.view"
    permission_codename_write = "purchase.manage"
    permission_codename_delete = "purchase.delete"

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("purchase"):
            messages.error(request, "Purchase module is disabled for this tenant.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class PurchaseDashboardAccessMixin(FoundationDashboardAccessMixin):
    """Purchase dashboard access mirrors other tenant apps."""

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("purchase"):
            messages.error(request, "Purchase module is disabled for this tenant.")
            return redirect("dashboard")
        if (
            getattr(request.user, "role", None) in ("staff", "tenant_admin")
            and tenant is not None
            and not request.user.has_tenant_permission("purchase.view")
        ):
            messages.error(request, "You do not have permission for this Purchase action.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class PurchasePageContextMixin:
    active_page = "purchase"
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if self.page_title:
            ctx.setdefault("page_title", self.page_title)
        return ctx

