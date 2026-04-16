from django.contrib import messages
from django.shortcuts import redirect

from foundation.mixins import FoundationAdminMixin, FoundationDashboardAccessMixin


class VaultAdminMixin(FoundationAdminMixin):
    permission_codename_read = "vault.view"
    permission_codename_write = "vault.manage"
    permission_codename_delete = "vault.delete"

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("vault"):
            messages.error(request, "Credential Vault module is disabled for this tenant.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission for this Credential Vault action.")
        return redirect("dashboard")


class VaultDashboardAccessMixin(FoundationDashboardAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("vault"):
            messages.error(request, "Credential Vault module is disabled for this tenant.")
            return redirect("dashboard")
        return response


class VaultPageContextMixin:
    active_page = "vault"
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if self.page_title:
            ctx.setdefault("page_title", self.page_title)
        return ctx
