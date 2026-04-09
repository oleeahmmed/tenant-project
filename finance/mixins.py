from django.contrib import messages
from django.shortcuts import redirect

from foundation.mixins import FoundationAdminMixin, FoundationDashboardAccessMixin


class FinanceAdminMixin(FoundationAdminMixin):
    """Finance admin pages follow same tenant guard as foundation/hrm."""


class FinanceDashboardAccessMixin(FoundationDashboardAccessMixin):
    """Finance dashboard keeps same access behavior as HRM/Foundation."""


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

