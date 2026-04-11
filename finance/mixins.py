from urllib.parse import urlencode

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect

from foundation.mixins import FoundationAdminMixin, FoundationDashboardAccessMixin


class FinanceAdminMixin(FoundationAdminMixin):
    """Finance admin pages follow same tenant guard as foundation/hrm."""
    permission_codename_read = "finance.view"
    permission_codename_write = "finance.manage"
    permission_codename_delete = "finance.delete"

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("finance"):
            messages.error(request, "Finance module is disabled for this tenant.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class FinanceDashboardAccessMixin(FoundationDashboardAccessMixin):
    """Finance dashboard keeps same access behavior as HRM/Foundation."""

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("finance"):
            messages.error(request, "Finance module is disabled for this tenant.")
            return redirect("dashboard")
        if (
            getattr(request.user, "role", None) in ("staff", "tenant_admin")
            and tenant is not None
            and not request.user.has_tenant_permission("finance.view")
        ):
            messages.error(request, "You do not have permission for this Finance action.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class FinancePageContextMixin:
    active_page = "finance"
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        if self.page_title:
            ctx.setdefault("page_title", self.page_title)
        return ctx


class FinancePostOnlyMixin:
    http_method_names = ["post"]

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect("dashboard")


class FinancePermissionRequiredMixin:
    permission_codename = ""

    def dispatch(self, request, *args, **kwargs):
        if self.permission_codename and not request.user.has_tenant_permission(self.permission_codename):
            messages.error(request, "You do not have permission for this action.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class FinanceMasterListMixin:
    """Search, optional active flag, sort whitelist, pagination, print template for finance master lists."""

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
            return ["finance/print_master_list.html"]
        return super().get_template_names()

