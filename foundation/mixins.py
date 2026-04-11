from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from hrm.mixins import WorkspaceTenantDashboardMixin
from hrm.tenant_scope import get_hrm_tenant, user_belongs_to_workspace_tenant


class FoundationAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Same tenant resolution as HRM admin pages."""
    permission_codename = ""
    permission_codename_read = "foundation.view"
    permission_codename_write = "foundation.manage"
    permission_codename_delete = "foundation.delete"

    def _resolve_permission_codename(self):
        explicit = getattr(self, "permission_codename", "") or ""
        if explicit:
            return explicit

        method = (self.request.method or "GET").upper()
        model = getattr(self, "model", None)
        if model is not None and hasattr(model, "_meta"):
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            action = "view"
            if method == "DELETE":
                action = "delete"
            elif method in ("POST", "PUT", "PATCH"):
                if "Create" in self.__class__.__name__:
                    action = "add"
                elif "Delete" in self.__class__.__name__:
                    action = "delete"
                elif "Update" in self.__class__.__name__:
                    action = "change"
                else:
                    action = "change"
            return f"{app_label}.{model_name}.{action}"

        if method == "DELETE":
            return self.permission_codename_delete
        if method in ("POST", "PUT", "PATCH"):
            return self.permission_codename_write
        return self.permission_codename_read

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
        if not user_belongs_to_workspace_tenant(u, t):
            return False
        if u.role not in ("tenant_admin", "staff"):
            return False

        perm = self._resolve_permission_codename()
        return bool(perm) and u.has_tenant_permission(perm)

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
            messages.error(self.request, "You do not have permission for this Foundation action.")
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
