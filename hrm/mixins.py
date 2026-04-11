from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from .models import Employee
from .tenant_scope import get_hrm_tenant, user_belongs_to_workspace_tenant


class WorkspaceTenantDashboardMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    HRM / Foundation dashboard: super_admin may open without a resolved tenant (to pick one);
    tenant_admin and staff need a resolved workspace tenant.
    """

    def dispatch(self, request, *args, **kwargs):
        request.hrm_tenant = get_hrm_tenant(request)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        u = self.request.user
        if not u.is_authenticated:
            return False
        if u.role == "super_admin":
            return True
        t = getattr(self.request, "hrm_tenant", None)
        if t is None:
            return False
        return user_belongs_to_workspace_tenant(u, t)

    def handle_no_permission(self):
        messages.error(self.request, "No tenant is assigned to your account.")
        return redirect("dashboard")


class HrmAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """CRUD / admin HRM pages: only tenant_admin / super_admin on resolved tenant."""
    permission_codename = ""
    permission_codename_read = "hrm.view"
    permission_codename_write = "hrm.manage"
    permission_codename_delete = "hrm.delete"

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
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("hrm"):
            messages.error(request, "HRM module is disabled for this tenant.")
            return redirect("dashboard")
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
            messages.error(self.request, "You do not have permission for this HRM action.")
        return redirect("dashboard")


class HrmPageContextMixin:
    """Sets active_page for shell; optional page_title on the class."""

    active_page = "hrm"
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if self.page_title:
            ctx.setdefault("page_title", self.page_title)
        return ctx


class PostOnlyMixin:
    http_method_names = ["post"]


class EmployeePortalMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Access: (1) Employee linked to this user on the resolved tenant, or
    (2) tenant_admin / super_admin — open the page in preview (map/policy) until an Employee is linked.
    """

    def dispatch(self, request, *args, **kwargs):
        request.hrm_tenant = get_hrm_tenant(request)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        u = self.request.user
        if not u.is_authenticated:
            return False
        t = getattr(self.request, "hrm_tenant", None)
        if t is None:
            return False
        emp = Employee.objects.filter(user_id=u.pk).first()
        if emp is not None and emp.tenant_id == t.id:
            return True
        if getattr(u, "role", None) == "tenant_admin" and getattr(u, "tenant_id", None) == t.id:
            return True
        if getattr(u, "role", None) == "super_admin":
            return True
        return False

    def handle_no_permission(self):
        messages.error(
            self.request,
            "Open Human Resources, select this workspace, or link your login to an employee profile.",
        )
        return redirect("dashboard")
