from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .forms import (
    GoodsIssueForm,
    GoodsIssueItemFormSet,
    InventoryTransferForm,
    InventoryTransferItemFormSet,
    StockAdjustmentForm,
    StockAdjustmentItemFormSet,
)
from .mixins import InventoryAdminMixin, InventoryDashboardAccessMixin, InventoryPageContextMixin
from .models import (
    GoodsIssue,
    InventoryTransfer,
    StockAdjustment,
    StockTransaction,
    WarehouseStock,
)
from .services.stock import (
    post_goods_issue,
    post_inventory_transfer,
    post_stock_adjustment,
    purge_empty_stock_adjustment_lines,
    recalculate_adjustment_totals,
)


class InventoryDashboardView(
    InventoryDashboardAccessMixin, InventoryPageContextMixin, TemplateView
):
    template_name = "inventory/dashboard.html"
    page_title = "Inventory"
    active_page = "inventory"


# ── Stock adjustments ───────────────────────────────────────────────────────────


class StockAdjustmentListView(InventoryAdminMixin, InventoryPageContextMixin, ListView):
    model = StockAdjustment
    template_name = "inventory/stock_adjustment_list.html"
    context_object_name = "documents"
    page_title = "Stock adjustments"
    paginate_by = 15

    def get_queryset(self):
        qs = StockAdjustment.objects.filter(tenant=self.request.hrm_tenant)

        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        adj_type = (self.request.GET.get("adjustment_type") or "").strip()
        warehouse = (self.request.GET.get("warehouse") or "").strip()
        date_from = (self.request.GET.get("date_from") or "").strip()
        date_to = (self.request.GET.get("date_to") or "").strip()
        ordering = (self.request.GET.get("sort") or "-adjustment_date").strip()

        if q:
            qs = qs.filter(
                Q(adjustment_number__icontains=q)
                | Q(warehouse_code__icontains=q)
                | Q(warehouse_name__icontains=q)
                | Q(requested_by__icontains=q)
                | Q(reason__icontains=q)
                | Q(notes__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if adj_type:
            qs = qs.filter(adjustment_type=adj_type)
        if warehouse:
            qs = qs.filter(warehouse_code__icontains=warehouse)
        if date_from:
            qs = qs.filter(adjustment_date__gte=date_from)
        if date_to:
            qs = qs.filter(adjustment_date__lte=date_to)

        allowed_ordering = {
            "adjustment_date": "adjustment_date",
            "-adjustment_date": "-adjustment_date",
            "adjustment_number": "adjustment_number",
            "-adjustment_number": "-adjustment_number",
            "warehouse_code": "warehouse_code",
            "-warehouse_code": "-warehouse_code",
            "status": "status",
            "-status": "-status",
        }
        qs = qs.order_by(allowed_ordering.get(ordering, "-adjustment_date"), "-id")
        return qs

    def get_paginate_by(self, queryset):
        raw = (self.request.GET.get("page_size") or "").strip()
        try:
            size = int(raw)
        except ValueError:
            size = self.paginate_by
        return 100 if size > 100 else (5 if size < 5 else size)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base_qs = StockAdjustment.objects.filter(tenant=self.request.hrm_tenant)
        ctx["summary"] = {
            "total_docs": base_qs.count(),
            "draft_docs": base_qs.filter(status="draft").count(),
            "posted_docs": base_qs.filter(status="posted").count(),
            "total_amount": base_qs.aggregate(v=Sum("total_amount"))["v"] or 0,
        }
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = params.urlencode()
        ctx["status_choices"] = StockAdjustment.STATUS_CHOICES
        ctx["type_choices"] = StockAdjustment.ADJUSTMENT_TYPES
        ctx["selected"] = {
            "q": self.request.GET.get("q", ""),
            "status": self.request.GET.get("status", ""),
            "adjustment_type": self.request.GET.get("adjustment_type", ""),
            "warehouse": self.request.GET.get("warehouse", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "sort": self.request.GET.get("sort", "-adjustment_date"),
            "page_size": self.request.GET.get("page_size", str(self.paginate_by)),
        }
        return ctx


class StockAdjustmentDetailView(InventoryAdminMixin, InventoryPageContextMixin, DetailView):
    model = StockAdjustment
    template_name = "inventory/stock_adjustment_detail.html"
    context_object_name = "doc"

    def get_queryset(self):
        return StockAdjustment.objects.filter(tenant=self.request.hrm_tenant).prefetch_related("items")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = self.object.adjustment_number
        tenant = getattr(self.request, "hrm_tenant", None)
        ctx["company"] = {
            "name": getattr(tenant, "name", "") or "Company",
            "address": "Address not configured",
            "phone": "Phone not configured",
            "email": "Email not configured",
        }
        return ctx


class StockAdjustmentCreateView(InventoryAdminMixin, InventoryPageContextMixin, View):
    template_name = "inventory/stock_adjustment_form.html"
    page_title = "New stock adjustment"

    def get(self, request):
        form = StockAdjustmentForm(tenant=request.hrm_tenant)
        formset = StockAdjustmentItemFormSet(tenant=request.hrm_tenant)
        return self._render(request, form, formset, None)

    def post(self, request):
        form = StockAdjustmentForm(request.POST, tenant=request.hrm_tenant)
        if not form.is_valid():
            formset = StockAdjustmentItemFormSet(
                request.POST,
                tenant=request.hrm_tenant,
            )
            messages.error(request, "Fix the errors below.")
            return self._render(request, form, formset, None)
        obj = form.save(commit=False)
        obj.tenant = request.hrm_tenant
        obj.save()
        formset = StockAdjustmentItemFormSet(
            request.POST,
            instance=obj,
            tenant=request.hrm_tenant,
        )
        if formset.is_valid():
            formset.save()
            purge_empty_stock_adjustment_lines(obj)
            recalculate_adjustment_totals(obj)
            messages.success(request, "Stock adjustment saved.")
            return redirect("inventory:stock_adjustment_detail", pk=obj.pk)
        messages.error(request, "Fix the errors below.")
        form = StockAdjustmentForm(instance=obj, tenant=request.hrm_tenant)
        return self._render(request, form, formset, obj)

    def _render(self, request, form, formset, obj):
        from django.template.response import TemplateResponse

        return TemplateResponse(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "object": obj,
                "page_title": (f"Edit {obj.adjustment_number}" if obj else self.page_title),
                "active_page": "inventory",
                "is_edit": obj is not None,
            },
        )


class StockAdjustmentUpdateView(InventoryAdminMixin, InventoryPageContextMixin, View):
    template_name = "inventory/stock_adjustment_form.html"

    def _can_override_status(self, request):
        return getattr(request.user, "role", "") == "tenant_admin"

    def get_object(self):
        return get_object_or_404(
            StockAdjustment.objects.filter(tenant=self.request.hrm_tenant),
            pk=self.kwargs["pk"],
        )

    def get(self, request, pk):
        obj = self.get_object()
        if obj.status != "draft" and not self._can_override_status(request):
            messages.warning(request, "Only draft documents can be edited.")
            return redirect("inventory:stock_adjustment_detail", pk=obj.pk)
        form = StockAdjustmentForm(instance=obj, tenant=request.hrm_tenant)
        formset = StockAdjustmentItemFormSet(
            instance=obj,
            tenant=request.hrm_tenant,
        )
        return self._render(request, form, formset, obj)

    def post(self, request, pk):
        obj = self.get_object()
        if obj.status != "draft" and not self._can_override_status(request):
            messages.error(request, "Only draft documents can be edited.")
            return redirect("inventory:stock_adjustment_detail", pk=obj.pk)
        form = StockAdjustmentForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = StockAdjustmentItemFormSet(
            request.POST,
            instance=obj,
            tenant=request.hrm_tenant,
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            purge_empty_stock_adjustment_lines(obj)
            recalculate_adjustment_totals(obj)
            messages.success(request, "Stock adjustment updated.")
            return redirect("inventory:stock_adjustment_detail", pk=obj.pk)
        messages.error(request, "Fix the errors below.")
        return self._render(request, form, formset, obj)

    def _render(self, request, form, formset, obj):
        from django.template.response import TemplateResponse

        return TemplateResponse(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "object": obj,
                "page_title": f"Edit {obj.adjustment_number}",
                "active_page": "inventory",
                "is_edit": True,
            },
        )


class StockAdjustmentPostView(InventoryAdminMixin, View):
    def post(self, request, pk):
        adj = get_object_or_404(
            StockAdjustment.objects.filter(tenant=request.hrm_tenant),
            pk=pk,
        )
        if adj.status != "draft":
            messages.warning(request, "Document is not in draft status.")
            return redirect("inventory:stock_adjustment_detail", pk=pk)
        if not adj.items.exists():
            messages.error(request, "Add at least one line before posting.")
            return redirect("inventory:stock_adjustment_update", pk=pk)
        try:
            post_stock_adjustment(adj)
            messages.success(request, "Adjustment posted. Stock updated.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("inventory:stock_adjustment_detail", pk=pk)


class StockAdjustmentDeleteView(InventoryAdminMixin, View):
    def post(self, request, pk):
        adj = get_object_or_404(
            StockAdjustment.objects.filter(tenant=request.hrm_tenant),
            pk=pk,
        )
        can_override = getattr(request.user, "role", "") == "tenant_admin"
        if adj.status != "draft" and not can_override:
            messages.error(request, "Only draft documents can be deleted.")
            return redirect("inventory:stock_adjustment_detail", pk=pk)
        number = adj.adjustment_number
        adj.delete()
        messages.success(request, f"{number} deleted.")
        return redirect("inventory:stock_adjustment_list")


# ── Goods issues ────────────────────────────────────────────────────────────────


class GoodsIssueListView(InventoryAdminMixin, InventoryPageContextMixin, ListView):
    model = GoodsIssue
    template_name = "inventory/goods_issue_list.html"
    context_object_name = "documents"
    page_title = "Goods issues"
    paginate_by = 15

    def get_queryset(self):
        qs = GoodsIssue.objects.filter(tenant=self.request.hrm_tenant).select_related(
            "warehouse", "customer"
        )
        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        issue_type = (self.request.GET.get("issue_type") or "").strip()
        warehouse = (self.request.GET.get("warehouse") or "").strip()
        date_from = (self.request.GET.get("date_from") or "").strip()
        date_to = (self.request.GET.get("date_to") or "").strip()
        ordering = (self.request.GET.get("sort") or "-issue_date").strip()
        if q:
            qs = qs.filter(
                Q(issue_number__icontains=q)
                | Q(reference__icontains=q)
                | Q(issued_to__icontains=q)
                | Q(notes__icontains=q)
                | Q(warehouse__code__icontains=q)
                | Q(warehouse__name__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if issue_type:
            qs = qs.filter(issue_type=issue_type)
        if warehouse:
            qs = qs.filter(warehouse__code__icontains=warehouse)
        if date_from:
            qs = qs.filter(issue_date__gte=date_from)
        if date_to:
            qs = qs.filter(issue_date__lte=date_to)
        allowed_ordering = {
            "issue_date": "issue_date",
            "-issue_date": "-issue_date",
            "issue_number": "issue_number",
            "-issue_number": "-issue_number",
            "warehouse__code": "warehouse__code",
            "-warehouse__code": "-warehouse__code",
            "status": "status",
            "-status": "-status",
        }
        return qs.order_by(allowed_ordering.get(ordering, "-issue_date"), "-id")

    def get_paginate_by(self, queryset):
        raw = (self.request.GET.get("page_size") or "").strip()
        try:
            size = int(raw)
        except ValueError:
            size = self.paginate_by
        return 100 if size > 100 else (5 if size < 5 else size)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = params.urlencode()
        ctx["status_choices"] = GoodsIssue.STATUS_CHOICES
        ctx["type_choices"] = GoodsIssue.ISSUE_TYPES
        ctx["selected"] = {
            "q": self.request.GET.get("q", ""),
            "status": self.request.GET.get("status", ""),
            "issue_type": self.request.GET.get("issue_type", ""),
            "warehouse": self.request.GET.get("warehouse", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "sort": self.request.GET.get("sort", "-issue_date"),
            "page_size": self.request.GET.get("page_size", str(self.paginate_by)),
        }
        return ctx


class GoodsIssueDetailView(InventoryAdminMixin, InventoryPageContextMixin, DetailView):
    model = GoodsIssue
    template_name = "inventory/goods_issue_detail.html"
    context_object_name = "doc"

    def get_queryset(self):
        return GoodsIssue.objects.filter(tenant=self.request.hrm_tenant).prefetch_related("items__product")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = self.object.issue_number
        ctx["total_amount"] = self.object.items.aggregate(v=Sum("line_total"))["v"] or 0
        return ctx


class GoodsIssueCreateView(InventoryAdminMixin, InventoryPageContextMixin, View):
    template_name = "inventory/goods_issue_form.html"
    page_title = "New goods issue"

    def get(self, request):
        form = GoodsIssueForm(tenant=request.hrm_tenant)
        formset = GoodsIssueItemFormSet(tenant=request.hrm_tenant)
        return self._render(request, form, formset, None)

    def post(self, request):
        form = GoodsIssueForm(request.POST, tenant=request.hrm_tenant)
        if not form.is_valid():
            formset = GoodsIssueItemFormSet(
                request.POST,
                tenant=request.hrm_tenant,
            )
            messages.error(request, "Fix the errors below.")
            return self._render(request, form, formset, None)
        obj = form.save(commit=False)
        obj.tenant = request.hrm_tenant
        obj.save()
        formset = GoodsIssueItemFormSet(
            request.POST,
            instance=obj,
            tenant=request.hrm_tenant,
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, "Goods issue saved.")
            return redirect("inventory:goods_issue_detail", pk=obj.pk)
        messages.error(request, "Fix the errors below.")
        form = GoodsIssueForm(instance=obj, tenant=request.hrm_tenant)
        return self._render(request, form, formset, obj)

    def _render(self, request, form, formset, obj):
        from django.template.response import TemplateResponse

        return TemplateResponse(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "object": obj,
                "page_title": (f"Edit {obj.issue_number}" if obj else self.page_title),
                "active_page": "inventory",
                "is_edit": obj is not None,
            },
        )


class GoodsIssueUpdateView(InventoryAdminMixin, InventoryPageContextMixin, View):
    template_name = "inventory/goods_issue_form.html"

    def _can_override_status(self, request):
        return getattr(request.user, "role", "") == "tenant_admin"

    def get_object(self):
        return get_object_or_404(GoodsIssue.objects.filter(tenant=self.request.hrm_tenant), pk=self.kwargs["pk"])

    def get(self, request, pk):
        obj = self.get_object()
        if (obj.status != "draft" or obj.stock_posted) and not self._can_override_status(request):
            messages.warning(request, "Only draft documents can be edited.")
            return redirect("inventory:goods_issue_detail", pk=obj.pk)
        form = GoodsIssueForm(instance=obj, tenant=request.hrm_tenant)
        formset = GoodsIssueItemFormSet(instance=obj, tenant=request.hrm_tenant)
        return self._render(request, form, formset, obj)

    def post(self, request, pk):
        obj = self.get_object()
        if (obj.status != "draft" or obj.stock_posted) and not self._can_override_status(request):
            messages.error(request, "Only draft documents can be edited.")
            return redirect("inventory:goods_issue_detail", pk=obj.pk)
        form = GoodsIssueForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = GoodsIssueItemFormSet(
            request.POST,
            instance=obj,
            tenant=request.hrm_tenant,
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Goods issue updated.")
            return redirect("inventory:goods_issue_detail", pk=obj.pk)
        messages.error(request, "Fix the errors below.")
        return self._render(request, form, formset, obj)

    def _render(self, request, form, formset, obj):
        from django.template.response import TemplateResponse

        return TemplateResponse(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "object": obj,
                "page_title": f"Edit {obj.issue_number}",
                "active_page": "inventory",
                "is_edit": True,
            },
        )


class GoodsIssuePostView(InventoryAdminMixin, View):
    def post(self, request, pk):
        issue = get_object_or_404(GoodsIssue.objects.filter(tenant=request.hrm_tenant), pk=pk)
        if issue.status != "draft" or issue.stock_posted:
            messages.warning(request, "Document cannot be released.")
            return redirect("inventory:goods_issue_detail", pk=pk)
        if not issue.items.exists():
            messages.error(request, "Add at least one line before release.")
            return redirect("inventory:goods_issue_update", pk=pk)
        try:
            post_goods_issue(issue)
            messages.success(request, "Goods issue released. Stock deducted.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("inventory:goods_issue_detail", pk=pk)


class GoodsIssueDeleteView(InventoryAdminMixin, View):
    def post(self, request, pk):
        issue = get_object_or_404(GoodsIssue.objects.filter(tenant=request.hrm_tenant), pk=pk)
        can_override = getattr(request.user, "role", "") == "tenant_admin"
        if (issue.status != "draft" or issue.stock_posted) and not can_override:
            messages.error(request, "Only draft documents can be deleted.")
            return redirect("inventory:goods_issue_detail", pk=pk)
        number = issue.issue_number
        issue.delete()
        messages.success(request, f"{number} deleted.")
        return redirect("inventory:goods_issue_list")


# ── Inventory transfers ───────────────────────────────────────────────────────────


class InventoryTransferListView(InventoryAdminMixin, InventoryPageContextMixin, ListView):
    model = InventoryTransfer
    template_name = "inventory/inventory_transfer_list.html"
    context_object_name = "documents"
    page_title = "Inventory transfers"
    paginate_by = 15

    def get_queryset(self):
        qs = InventoryTransfer.objects.filter(tenant=self.request.hrm_tenant).select_related(
            "from_warehouse", "to_warehouse"
        )
        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        warehouse = (self.request.GET.get("warehouse") or "").strip()
        date_from = (self.request.GET.get("date_from") or "").strip()
        date_to = (self.request.GET.get("date_to") or "").strip()
        ordering = (self.request.GET.get("sort") or "-transfer_date").strip()
        if q:
            qs = qs.filter(
                Q(transfer_number__icontains=q)
                | Q(reference__icontains=q)
                | Q(notes__icontains=q)
                | Q(from_warehouse__code__icontains=q)
                | Q(to_warehouse__code__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if warehouse:
            qs = qs.filter(
                Q(from_warehouse__code__icontains=warehouse)
                | Q(to_warehouse__code__icontains=warehouse)
            )
        if date_from:
            qs = qs.filter(transfer_date__gte=date_from)
        if date_to:
            qs = qs.filter(transfer_date__lte=date_to)
        allowed_ordering = {
            "transfer_date": "transfer_date",
            "-transfer_date": "-transfer_date",
            "transfer_number": "transfer_number",
            "-transfer_number": "-transfer_number",
            "status": "status",
            "-status": "-status",
        }
        return qs.order_by(allowed_ordering.get(ordering, "-transfer_date"), "-id")

    def get_paginate_by(self, queryset):
        raw = (self.request.GET.get("page_size") or "").strip()
        try:
            size = int(raw)
        except ValueError:
            size = self.paginate_by
        return 100 if size > 100 else (5 if size < 5 else size)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = params.urlencode()
        ctx["status_choices"] = InventoryTransfer.STATUS_CHOICES
        ctx["selected"] = {
            "q": self.request.GET.get("q", ""),
            "status": self.request.GET.get("status", ""),
            "warehouse": self.request.GET.get("warehouse", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "sort": self.request.GET.get("sort", "-transfer_date"),
            "page_size": self.request.GET.get("page_size", str(self.paginate_by)),
        }
        return ctx


class InventoryTransferDetailView(InventoryAdminMixin, InventoryPageContextMixin, DetailView):
    model = InventoryTransfer
    template_name = "inventory/inventory_transfer_detail.html"
    context_object_name = "doc"

    def get_queryset(self):
        return InventoryTransfer.objects.filter(tenant=self.request.hrm_tenant).prefetch_related("items__product")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = self.object.transfer_number
        ctx["total_amount"] = self.object.items.aggregate(v=Sum("line_total"))["v"] or 0
        return ctx


class InventoryTransferCreateView(InventoryAdminMixin, InventoryPageContextMixin, View):
    template_name = "inventory/inventory_transfer_form.html"
    page_title = "New inventory transfer"

    def get(self, request):
        form = InventoryTransferForm(tenant=request.hrm_tenant)
        formset = InventoryTransferItemFormSet(tenant=request.hrm_tenant)
        return self._render(request, form, formset, None)

    def post(self, request):
        form = InventoryTransferForm(request.POST, tenant=request.hrm_tenant)
        if not form.is_valid():
            formset = InventoryTransferItemFormSet(
                request.POST,
                tenant=request.hrm_tenant,
            )
            messages.error(request, "Fix the errors below.")
            return self._render(request, form, formset, None)
        obj = form.save(commit=False)
        obj.tenant = request.hrm_tenant
        obj.save()
        formset = InventoryTransferItemFormSet(
            request.POST,
            instance=obj,
            tenant=request.hrm_tenant,
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, "Transfer saved.")
            return redirect("inventory:inventory_transfer_detail", pk=obj.pk)
        messages.error(request, "Fix the errors below.")
        form = InventoryTransferForm(instance=obj, tenant=request.hrm_tenant)
        return self._render(request, form, formset, obj)

    def _render(self, request, form, formset, obj):
        from django.template.response import TemplateResponse

        return TemplateResponse(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "object": obj,
                "page_title": (f"Edit {obj.transfer_number}" if obj else self.page_title),
                "active_page": "inventory",
                "is_edit": obj is not None,
            },
        )


class InventoryTransferUpdateView(InventoryAdminMixin, InventoryPageContextMixin, View):
    template_name = "inventory/inventory_transfer_form.html"

    def _can_override_status(self, request):
        return getattr(request.user, "role", "") == "tenant_admin"

    def get_object(self):
        return get_object_or_404(
            InventoryTransfer.objects.filter(tenant=self.request.hrm_tenant),
            pk=self.kwargs["pk"],
        )

    def get(self, request, pk):
        obj = self.get_object()
        if (obj.status != "draft" or obj.stock_posted) and not self._can_override_status(request):
            messages.warning(request, "Only draft documents can be edited.")
            return redirect("inventory:inventory_transfer_detail", pk=obj.pk)
        form = InventoryTransferForm(instance=obj, tenant=request.hrm_tenant)
        formset = InventoryTransferItemFormSet(instance=obj, tenant=request.hrm_tenant)
        return self._render(request, form, formset, obj)

    def post(self, request, pk):
        obj = self.get_object()
        if (obj.status != "draft" or obj.stock_posted) and not self._can_override_status(request):
            messages.error(request, "Only draft documents can be edited.")
            return redirect("inventory:inventory_transfer_detail", pk=obj.pk)
        form = InventoryTransferForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = InventoryTransferItemFormSet(
            request.POST,
            instance=obj,
            tenant=request.hrm_tenant,
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Transfer updated.")
            return redirect("inventory:inventory_transfer_detail", pk=obj.pk)
        messages.error(request, "Fix the errors below.")
        return self._render(request, form, formset, obj)

    def _render(self, request, form, formset, obj):
        from django.template.response import TemplateResponse

        return TemplateResponse(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "object": obj,
                "page_title": f"Edit {obj.transfer_number}",
                "active_page": "inventory",
                "is_edit": True,
            },
        )


class InventoryTransferPostView(InventoryAdminMixin, View):
    def post(self, request, pk):
        tr = get_object_or_404(
            InventoryTransfer.objects.filter(tenant=request.hrm_tenant),
            pk=pk,
        )
        if tr.status != "draft" or tr.stock_posted:
            messages.warning(request, "Document cannot be completed.")
            return redirect("inventory:inventory_transfer_detail", pk=pk)
        if not tr.items.exists():
            messages.error(request, "Add at least one line before completing.")
            return redirect("inventory:inventory_transfer_update", pk=pk)
        try:
            post_inventory_transfer(tr)
            messages.success(request, "Transfer completed. Stock moved.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("inventory:inventory_transfer_detail", pk=pk)


# ── Stock reports (read-only) ───────────────────────────────────────────────────


class WarehouseStockListView(InventoryAdminMixin, InventoryPageContextMixin, ListView):
    model = WarehouseStock
    template_name = "inventory/warehouse_stock_list.html"
    context_object_name = "rows"
    page_title = "Warehouse stock"
    paginate_by = 50

    def get_queryset(self):
        return (
            WarehouseStock.objects.filter(tenant=self.request.hrm_tenant)
            .select_related("product", "warehouse")
            .filter(quantity__gt=0)
            .order_by("warehouse", "product")
        )


class InventoryTransferDeleteView(InventoryAdminMixin, View):
    def post(self, request, pk):
        tr = get_object_or_404(
            InventoryTransfer.objects.filter(tenant=request.hrm_tenant),
            pk=pk,
        )
        can_override = getattr(request.user, "role", "") == "tenant_admin"
        if (tr.status != "draft" or tr.stock_posted) and not can_override:
            messages.error(request, "Only draft documents can be deleted.")
            return redirect("inventory:inventory_transfer_detail", pk=pk)
        number = tr.transfer_number
        tr.delete()
        messages.success(request, f"{number} deleted.")
        return redirect("inventory:inventory_transfer_list")


class StockTransactionListView(InventoryAdminMixin, InventoryPageContextMixin, ListView):
    model = StockTransaction
    template_name = "inventory/stock_transaction_list.html"
    context_object_name = "rows"
    page_title = "Stock transactions"
    paginate_by = 50

    def get_queryset(self):
        qs = StockTransaction.objects.filter(tenant=self.request.hrm_tenant).select_related(
            "product", "warehouse", "product_variant"
        )
        q = (self.request.GET.get("q") or "").strip()
        tx_type = (self.request.GET.get("transaction_type") or "").strip()
        warehouse = (self.request.GET.get("warehouse") or "").strip()
        date_from = (self.request.GET.get("date_from") or "").strip()
        date_to = (self.request.GET.get("date_to") or "").strip()
        ordering = (self.request.GET.get("sort") or "-created_at").strip()

        raw_pid = (self.request.GET.get("product_id") or "").strip()
        if raw_pid:
            try:
                pid = int(raw_pid)
                qs = qs.filter(product_id=pid)
            except ValueError:
                pass
        if q:
            qs = qs.filter(
                Q(reference__icontains=q)
                | Q(notes__icontains=q)
                | Q(product__sku__icontains=q)
                | Q(product__name__icontains=q)
                | Q(warehouse__code__icontains=q)
                | Q(warehouse__name__icontains=q)
            )
        if tx_type:
            qs = qs.filter(transaction_type=tx_type)
        if warehouse:
            qs = qs.filter(warehouse__code__icontains=warehouse)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        allowed_ordering = {
            "created_at": "created_at",
            "-created_at": "-created_at",
            "transaction_type": "transaction_type",
            "-transaction_type": "-transaction_type",
            "warehouse__code": "warehouse__code",
            "-warehouse__code": "-warehouse__code",
            "product__sku": "product__sku",
            "-product__sku": "-product__sku",
            "qty_signed": "qty_signed",
            "-qty_signed": "-qty_signed",
        }
        return qs.order_by(allowed_ordering.get(ordering, "-created_at"), "-id")

    def get_paginate_by(self, queryset):
        raw = (self.request.GET.get("page_size") or "").strip()
        try:
            size = int(raw)
        except ValueError:
            size = self.paginate_by
        return 100 if size > 100 else (10 if size < 10 else size)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = params.urlencode()
        ctx["transaction_type_choices"] = StockTransaction.TRANSACTION_TYPES
        ctx["selected"] = {
            "q": self.request.GET.get("q", ""),
            "transaction_type": self.request.GET.get("transaction_type", ""),
            "warehouse": self.request.GET.get("warehouse", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "sort": self.request.GET.get("sort", "-created_at"),
            "page_size": self.request.GET.get("page_size", str(self.paginate_by)),
        }
        raw_pid = (self.request.GET.get("product_id") or "").strip()
        if raw_pid.isdigit():
            from foundation.models import Product

            prod = Product.objects.filter(
                tenant=self.request.hrm_tenant,
                pk=int(raw_pid),
            ).only("pk", "sku", "name").first()
            ctx["filtered_product"] = prod
        return ctx
