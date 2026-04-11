from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
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


class FoundationMasterListMixin:
    """Search, optional active flag, sort whitelist, pagination, print template switch."""

    search_fields = []
    sort_allowlist = []
    default_sort = "name"
    has_is_active = True

    def get_paginate_by(self, queryset):
        if self.request.GET.get("print") == "1":
            return None
        try:
            n = int(self.request.GET.get("page_size", "20"))
        except (TypeError, ValueError):
            n = 20
        return max(5, min(n, 100))

    def _apply_search(self, qs):
        q = (self.request.GET.get("q") or "").strip()
        if not q or not self.search_fields:
            return qs
        combined = Q()
        for f in self.search_fields:
            combined |= Q(**{f"{f}__icontains": q})
        return qs.filter(combined)

    def _apply_active_filter(self, qs):
        if not getattr(self, "has_is_active", True):
            return qs
        v = (self.request.GET.get("active") or "").strip().lower()
        if v == "yes":
            return qs.filter(is_active=True)
        if v == "no":
            return qs.filter(is_active=False)
        return qs

    def _apply_sort(self, qs):
        sort = (self.request.GET.get("sort") or "").strip() or self.default_sort
        allow = getattr(self, "sort_allowlist", None) or []
        if allow and sort in allow:
            return qs.order_by(sort)
        return qs.order_by(self.default_sort)

    def _apply_print_pk(self, qs):
        if self.request.GET.get("print") == "1" and self.request.GET.get("pk"):
            try:
                pk = int(self.request.GET["pk"])
            except (TypeError, ValueError):
                return qs
            return qs.filter(pk=pk)
        return qs

    def apply_master_filters(self, qs):
        qs = self._apply_search(qs)
        qs = self._apply_active_filter(qs)
        qs = self._apply_sort(qs)
        qs = self._apply_print_pk(qs)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = urlencode(params)
        try:
            pg = int(self.request.GET.get("page_size", "20"))
        except (TypeError, ValueError):
            pg = 20
        pg = max(5, min(pg, 100))
        ctx["selected"] = {
            "q": self.request.GET.get("q", ""),
            "sort": self.request.GET.get("sort", getattr(self, "default_sort", "name")),
            "page_size": str(pg),
            "active": self.request.GET.get("active", ""),
        }
        ctx["sort_choices"] = getattr(self, "sort_choices", [])
        ctx["is_print"] = self.request.GET.get("print") == "1"
        return ctx

    def get_template_names(self):
        if self.request.GET.get("print") == "1":
            return ["foundation/print_master_list.html"]
        return super().get_template_names()


# Re-export for foundation dashboard (same access rules as HRM dashboard).
FoundationDashboardAccessMixin = WorkspaceTenantDashboardMixin
