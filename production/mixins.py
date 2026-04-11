from django.contrib import messages
from django.shortcuts import redirect

from foundation.mixins import FoundationAdminMixin, FoundationDashboardAccessMixin


class ProductionAdminMixin(FoundationAdminMixin):
    permission_codename_read = "production.view"
    permission_codename_write = "production.manage"
    permission_codename_delete = "production.delete"

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("production"):
            messages.error(request, "Production module is disabled for this tenant.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class ProductionDashboardAccessMixin(FoundationDashboardAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("production"):
            messages.error(request, "Production module is disabled for this tenant.")
            return redirect("dashboard")
        if (
            getattr(request.user, "role", None) in ("staff", "tenant_admin")
            and tenant is not None
            and not request.user.has_tenant_permission("production.view")
        ):
            messages.error(request, "You do not have permission for this Production action.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class ProductionPageContextMixin:
    active_page = "production"
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if self.page_title:
            ctx.setdefault("page_title", self.page_title)
        return ctx

