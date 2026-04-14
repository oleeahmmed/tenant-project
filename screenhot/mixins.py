from django.contrib import messages
from django.shortcuts import redirect

from foundation.mixins import FoundationAdminMixin, FoundationDashboardAccessMixin


class ScreenhotModuleAdminMixin(FoundationAdminMixin):
    permission_codename_read = "screenhot.view"
    permission_codename_write = "screenhot.manage"
    permission_codename_delete = "screenhot.delete"

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("screenhot"):
            messages.error(request, "Screenhot module is disabled for this tenant.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission for this Screenhot action.")
        return redirect("dashboard")


class ScreenhotDashboardAccessMixin(FoundationDashboardAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("screenhot"):
            messages.error(request, "Screenhot module is disabled for this tenant.")
            return redirect("dashboard")
        return response


class ScreenhotPageContextMixin:
    active_page = "screenhot"
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if getattr(self, "page_title", None):
            ctx.setdefault("page_title", self.page_title)
        return ctx
