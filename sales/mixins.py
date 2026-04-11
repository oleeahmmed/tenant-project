from django.contrib import messages
from django.shortcuts import redirect

from foundation.mixins import FoundationAdminMixin, FoundationDashboardAccessMixin


class SalesAdminMixin(FoundationAdminMixin):
    permission_codename_read = "sales.view"
    permission_codename_write = "sales.manage"
    permission_codename_delete = "sales.delete"

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("sales"):
            messages.error(request, "Sales module is disabled for this tenant.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class SalesDashboardAccessMixin(FoundationDashboardAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("sales"):
            messages.error(request, "Sales module is disabled for this tenant.")
            return redirect("dashboard")
        if (
            getattr(request.user, "role", None) in ("staff", "tenant_admin")
            and tenant is not None
            and not request.user.has_tenant_permission("sales.view")
        ):
            messages.error(request, "You do not have permission for this Sales action.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class SalesPageContextMixin:
    active_page = "sales"
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if self.page_title:
            ctx.setdefault("page_title", self.page_title)
        return ctx

