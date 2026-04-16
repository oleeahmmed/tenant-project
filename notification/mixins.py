from django.contrib import messages
from django.shortcuts import redirect

from foundation.mixins import FoundationDashboardAccessMixin


class NotificationDashboardAccessMixin(FoundationDashboardAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("notification"):
            messages.error(request, "Notifications module is disabled for this tenant.")
            return redirect("dashboard")
        if (
            getattr(request.user, "role", None) in ("staff", "tenant_admin")
            and tenant is not None
            and not request.user.has_tenant_permission("notification.view")
        ):
            messages.error(request, "You do not have permission to view notifications.")
            return redirect("dashboard")
        return response


class NotificationPageContextMixin:
    active_page = "notification"
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if self.page_title:
            ctx.setdefault("page_title", self.page_title)
        return ctx
