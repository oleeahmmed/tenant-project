from django.contrib import messages
from django.shortcuts import redirect

from foundation.mixins import FoundationDashboardAccessMixin


class ChatDashboardAccessMixin(FoundationDashboardAccessMixin):
    """Workspace tenant + optional chat.view for staff (super_admin always)."""

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("chat"):
            messages.error(request, "Chat is disabled for this tenant.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        if not super().test_func():
            return False
        u = self.request.user
        if u.role == "super_admin":
            return True
        t = getattr(self.request, "hrm_tenant", None)
        if t is None:
            return False
        if u.role in ("staff", "tenant_admin") and not u.has_tenant_permission("chat.view"):
            return False
        return True

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to open Chat.")
        return redirect("dashboard")


class ChatPageContextMixin:
    active_page = "chat"
    page_title = "Chat"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        ctx.setdefault("page_title", getattr(self, "page_title", "Chat"))
        return ctx
