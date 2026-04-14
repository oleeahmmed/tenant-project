from django.contrib import messages
from django.shortcuts import redirect

from foundation.mixins import FoundationAdminMixin, FoundationDashboardAccessMixin


class SupportModuleAdminMixin(FoundationAdminMixin):
    permission_codename_read = "support.view"
    permission_codename_write = "support.manage"
    permission_codename_delete = "support.delete"

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("support"):
            messages.error(request, "Support module is disabled for this tenant.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission for this Support action.")
        return redirect("dashboard")


class SupportDashboardAccessMixin(FoundationDashboardAccessMixin):
    """Logged-in users with a workspace tenant may open Support (stricter actions use SupportModuleAdminMixin)."""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("support"):
            messages.error(request, "Support module is disabled for this tenant.")
            return redirect("dashboard")
        return response

    def test_func(self):
        if not super().test_func():
            return False
        u = self.request.user
        if u.role == "super_admin":
            return True
        t = getattr(self.request, "hrm_tenant", None)
        if t is None:
            return False
        if u.role in ("staff", "tenant_admin") and not u.has_tenant_permission("support.view"):
            return False
        return True


class SupportPageContextMixin:
    active_page = "support"
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if getattr(self, "page_title", None):
            ctx.setdefault("page_title", self.page_title)
        return ctx
