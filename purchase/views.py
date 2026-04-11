from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .forms import (
    GoodsReceiptForm,
    GoodsReceiptLineFormSet,
    PurchaseOrderForm,
    PurchaseOrderLineFormSet,
    PurchaseRequestForm,
    PurchaseRequestLineFormSet,
    PurchaseReturnForm,
    PurchaseReturnLineFormSet,
)
from .mixins import PurchaseAdminMixin, PurchaseDashboardAccessMixin, PurchasePageContextMixin
from .models import GoodsReceipt, PurchaseOrder, PurchaseRequest, PurchaseReturn
from .services.integrations import sync_grn_to_finance_ap_invoice


def _render_doc_form(request, *, form, formset, page_title, action_url, list_url):
    return render(
        request,
        "purchase/document_form.html",
        {
            "form": form,
            "formset": formset,
            "page_title": page_title,
            "action_url": action_url,
            "list_url": list_url,
            "active_page": "purchase",
        },
    )


class PurchaseDashboardView(PurchaseDashboardAccessMixin, PurchasePageContextMixin, TemplateView):
    template_name = "purchase/dashboard.html"
    page_title = "Purchase"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = self.request.hrm_tenant
        ctx["pr_count"] = PurchaseRequest.objects.filter(tenant=t).count()
        ctx["po_count"] = PurchaseOrder.objects.filter(tenant=t).count()
        ctx["grn_count"] = GoodsReceipt.objects.filter(tenant=t).count()
        ctx["return_count"] = PurchaseReturn.objects.filter(tenant=t).count()
        return ctx


class PurchaseGuideView(PurchaseAdminMixin, PurchasePageContextMixin, TemplateView):
    template_name = "purchase/purchase_guide_bn.html"
    page_title = "Purchase Guide (Bangla)"


class _BaseList(PurchaseAdminMixin, PurchasePageContextMixin, ListView):
    template_name = "purchase/document_list.html"
    context_object_name = "object_list"
    page_title = ""
    create_url = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["create_url"] = self.create_url
        return ctx


class PurchaseRequestListView(_BaseList):
    model = PurchaseRequest
    page_title = "Purchase requests"
    create_url = "purchase:purchase_request_create"

    def get_queryset(self):
        return PurchaseRequest.objects.filter(tenant=self.request.hrm_tenant).order_by("-request_date", "-id")


class PurchaseOrderListView(_BaseList):
    model = PurchaseOrder
    page_title = "Purchase orders"
    create_url = "purchase:purchase_order_create"

    def get_queryset(self):
        return PurchaseOrder.objects.filter(tenant=self.request.hrm_tenant).select_related("supplier").order_by("-order_date", "-id")


class GoodsReceiptListView(_BaseList):
    model = GoodsReceipt
    page_title = "Goods receipts"
    create_url = "purchase:goods_receipt_create"

    def get_queryset(self):
        return GoodsReceipt.objects.filter(tenant=self.request.hrm_tenant).select_related("supplier", "purchase_order").order_by("-receipt_date", "-id")


class PurchaseReturnListView(_BaseList):
    model = PurchaseReturn
    page_title = "Purchase returns"
    create_url = "purchase:purchase_return_create"

    def get_queryset(self):
        return PurchaseReturn.objects.filter(tenant=self.request.hrm_tenant).select_related("supplier", "goods_receipt").order_by("-return_date", "-id")


class _BaseDetail(PurchaseAdminMixin, PurchasePageContextMixin, DetailView):
    template_name = "purchase/document_detail.html"
    context_object_name = "object"
    page_title = ""
    list_url = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url"] = self.list_url
        return ctx


class PurchaseRequestDetailView(_BaseDetail):
    model = PurchaseRequest
    page_title = "Purchase request details"
    list_url = "purchase:purchase_request_list"

    def get_queryset(self):
        return PurchaseRequest.objects.filter(tenant=self.request.hrm_tenant).prefetch_related("lines__product")


class PurchaseOrderDetailView(_BaseDetail):
    model = PurchaseOrder
    page_title = "Purchase order details"
    list_url = "purchase:purchase_order_list"

    def get_queryset(self):
        return PurchaseOrder.objects.filter(tenant=self.request.hrm_tenant).select_related("supplier", "purchase_request").prefetch_related("lines__product", "lines__warehouse")


class GoodsReceiptDetailView(_BaseDetail):
    model = GoodsReceipt
    page_title = "Goods receipt details"
    list_url = "purchase:goods_receipt_list"

    def get_queryset(self):
        return GoodsReceipt.objects.filter(tenant=self.request.hrm_tenant).select_related("supplier", "purchase_order").prefetch_related("lines__product", "lines__warehouse")


class PurchaseReturnDetailView(_BaseDetail):
    model = PurchaseReturn
    page_title = "Purchase return details"
    list_url = "purchase:purchase_return_list"

    def get_queryset(self):
        return PurchaseReturn.objects.filter(tenant=self.request.hrm_tenant).select_related("supplier", "goods_receipt").prefetch_related("lines__product", "lines__warehouse")


class PurchaseRequestCreateView(PurchaseAdminMixin, View):
    def get(self, request):
        form = PurchaseRequestForm()
        formset = PurchaseRequestLineFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add purchase request", action_url=reverse_lazy("purchase:purchase_request_create"), list_url=reverse_lazy("purchase:purchase_request_list"))

    def post(self, request):
        form = PurchaseRequestForm(request.POST)
        formset = PurchaseRequestLineFormSet(request.POST, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.tenant = request.hrm_tenant
                obj.save()
                formset.instance = obj
                formset.save()
            messages.success(request, "Purchase request created.")
            return redirect("purchase:purchase_request_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add purchase request", action_url=reverse_lazy("purchase:purchase_request_create"), list_url=reverse_lazy("purchase:purchase_request_list"))


class PurchaseRequestUpdateView(PurchaseAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(PurchaseRequest, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != PurchaseRequest.Status.DRAFT:
            messages.error(request, "Only draft purchase requests are editable.")
            return redirect("purchase:purchase_request_list")
        form = PurchaseRequestForm(instance=obj)
        formset = PurchaseRequestLineFormSet(instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit purchase request", action_url=reverse_lazy("purchase:purchase_request_edit", kwargs={"pk": pk}), list_url=reverse_lazy("purchase:purchase_request_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = PurchaseRequestForm(request.POST, instance=obj)
        formset = PurchaseRequestLineFormSet(request.POST, instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, "Purchase request updated.")
            return redirect("purchase:purchase_request_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit purchase request", action_url=reverse_lazy("purchase:purchase_request_edit", kwargs={"pk": pk}), list_url=reverse_lazy("purchase:purchase_request_list"))


class PurchaseOrderCreateView(PurchaseAdminMixin, View):
    def get(self, request):
        form = PurchaseOrderForm(tenant=request.hrm_tenant)
        formset = PurchaseOrderLineFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add purchase order", action_url=reverse_lazy("purchase:purchase_order_create"), list_url=reverse_lazy("purchase:purchase_order_list"))

    def post(self, request):
        form = PurchaseOrderForm(request.POST, tenant=request.hrm_tenant)
        formset = PurchaseOrderLineFormSet(request.POST, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.tenant = request.hrm_tenant
                obj.save()
                formset.instance = obj
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["subtotal", "total_amount", "updated_at"])
            messages.success(request, "Purchase order created.")
            return redirect("purchase:purchase_order_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add purchase order", action_url=reverse_lazy("purchase:purchase_order_create"), list_url=reverse_lazy("purchase:purchase_order_list"))


class PurchaseOrderUpdateView(PurchaseAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(PurchaseOrder, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != PurchaseOrder.Status.DRAFT:
            messages.error(request, "Only draft purchase orders are editable.")
            return redirect("purchase:purchase_order_list")
        form = PurchaseOrderForm(instance=obj, tenant=request.hrm_tenant)
        formset = PurchaseOrderLineFormSet(instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit purchase order", action_url=reverse_lazy("purchase:purchase_order_edit", kwargs={"pk": pk}), list_url=reverse_lazy("purchase:purchase_order_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = PurchaseOrderForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = PurchaseOrderLineFormSet(request.POST, instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save()
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["subtotal", "total_amount", "updated_at"])
            messages.success(request, "Purchase order updated.")
            return redirect("purchase:purchase_order_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit purchase order", action_url=reverse_lazy("purchase:purchase_order_edit", kwargs={"pk": pk}), list_url=reverse_lazy("purchase:purchase_order_list"))


class GoodsReceiptCreateView(PurchaseAdminMixin, View):
    def get(self, request):
        form = GoodsReceiptForm(tenant=request.hrm_tenant)
        formset = GoodsReceiptLineFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            f.fields["purchase_order_line"].queryset = f.fields["purchase_order_line"].queryset.model.objects.filter(purchase_order__tenant=request.hrm_tenant)
        return _render_doc_form(request, form=form, formset=formset, page_title="Add goods receipt", action_url=reverse_lazy("purchase:goods_receipt_create"), list_url=reverse_lazy("purchase:goods_receipt_list"))

    def post(self, request):
        form = GoodsReceiptForm(request.POST, tenant=request.hrm_tenant)
        po = None
        if form.is_valid():
            po = form.cleaned_data.get("purchase_order")
        formset = GoodsReceiptLineFormSet(request.POST, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            qs = f.fields["purchase_order_line"].queryset.model.objects.filter(purchase_order__tenant=request.hrm_tenant)
            if po:
                qs = qs.filter(purchase_order=po)
            f.fields["purchase_order_line"].queryset = qs
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.tenant = request.hrm_tenant
                obj.save()
                formset.instance = obj
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_amount", "updated_at"])
            messages.success(request, "Goods receipt created.")
            return redirect("purchase:goods_receipt_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add goods receipt", action_url=reverse_lazy("purchase:goods_receipt_create"), list_url=reverse_lazy("purchase:goods_receipt_list"))


class GoodsReceiptUpdateView(PurchaseAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(GoodsReceipt, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != GoodsReceipt.Status.DRAFT:
            messages.error(request, "Only draft goods receipts are editable.")
            return redirect("purchase:goods_receipt_list")
        form = GoodsReceiptForm(instance=obj, tenant=request.hrm_tenant)
        formset = GoodsReceiptLineFormSet(instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            f.fields["purchase_order_line"].queryset = f.fields["purchase_order_line"].queryset.model.objects.filter(purchase_order=obj.purchase_order)
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit goods receipt", action_url=reverse_lazy("purchase:goods_receipt_edit", kwargs={"pk": pk}), list_url=reverse_lazy("purchase:goods_receipt_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = GoodsReceiptForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        po = None
        if form.is_valid():
            po = form.cleaned_data.get("purchase_order")
        formset = GoodsReceiptLineFormSet(request.POST, instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            qs = f.fields["purchase_order_line"].queryset.model.objects.filter(purchase_order__tenant=request.hrm_tenant)
            if po:
                qs = qs.filter(purchase_order=po)
            f.fields["purchase_order_line"].queryset = qs
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save()
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_amount", "updated_at"])
            messages.success(request, "Goods receipt updated.")
            return redirect("purchase:goods_receipt_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit goods receipt", action_url=reverse_lazy("purchase:goods_receipt_edit", kwargs={"pk": pk}), list_url=reverse_lazy("purchase:goods_receipt_list"))


class PurchaseReturnCreateView(PurchaseAdminMixin, View):
    def get(self, request):
        form = PurchaseReturnForm(tenant=request.hrm_tenant)
        formset = PurchaseReturnLineFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            f.fields["goods_receipt_line"].queryset = f.fields["goods_receipt_line"].queryset.model.objects.filter(receipt__tenant=request.hrm_tenant)
        return _render_doc_form(request, form=form, formset=formset, page_title="Add purchase return", action_url=reverse_lazy("purchase:purchase_return_create"), list_url=reverse_lazy("purchase:purchase_return_list"))

    def post(self, request):
        form = PurchaseReturnForm(request.POST, tenant=request.hrm_tenant)
        goods_receipt = None
        if form.is_valid():
            goods_receipt = form.cleaned_data.get("goods_receipt")
        formset = PurchaseReturnLineFormSet(request.POST, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            qs = f.fields["goods_receipt_line"].queryset.model.objects.filter(receipt__tenant=request.hrm_tenant)
            if goods_receipt:
                qs = qs.filter(receipt=goods_receipt)
            f.fields["goods_receipt_line"].queryset = qs
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.tenant = request.hrm_tenant
                obj.save()
                formset.instance = obj
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_amount", "updated_at"])
            messages.success(request, "Purchase return created.")
            return redirect("purchase:purchase_return_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add purchase return", action_url=reverse_lazy("purchase:purchase_return_create"), list_url=reverse_lazy("purchase:purchase_return_list"))


class PurchaseReturnUpdateView(PurchaseAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(PurchaseReturn, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != PurchaseReturn.Status.DRAFT:
            messages.error(request, "Only draft purchase returns are editable.")
            return redirect("purchase:purchase_return_list")
        form = PurchaseReturnForm(instance=obj, tenant=request.hrm_tenant)
        formset = PurchaseReturnLineFormSet(instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            f.fields["goods_receipt_line"].queryset = f.fields["goods_receipt_line"].queryset.model.objects.filter(receipt__tenant=request.hrm_tenant)
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit purchase return", action_url=reverse_lazy("purchase:purchase_return_edit", kwargs={"pk": pk}), list_url=reverse_lazy("purchase:purchase_return_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = PurchaseReturnForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        goods_receipt = None
        if form.is_valid():
            goods_receipt = form.cleaned_data.get("goods_receipt")
        formset = PurchaseReturnLineFormSet(request.POST, instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            qs = f.fields["goods_receipt_line"].queryset.model.objects.filter(receipt__tenant=request.hrm_tenant)
            if goods_receipt:
                qs = qs.filter(receipt=goods_receipt)
            f.fields["goods_receipt_line"].queryset = qs
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save()
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_amount", "updated_at"])
            messages.success(request, "Purchase return updated.")
            return redirect("purchase:purchase_return_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit purchase return", action_url=reverse_lazy("purchase:purchase_return_edit", kwargs={"pk": pk}), list_url=reverse_lazy("purchase:purchase_return_list"))


class _DocDeleteView(PurchaseAdminMixin, View):
    model = None
    list_url_name = ""
    label = "Document"

    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk, tenant=request.hrm_tenant)
        if getattr(obj, "status", "") != "draft":
            messages.error(request, f"Only draft {self.label.lower()} can be deleted.")
            return redirect(self.list_url_name)
        obj.delete()
        messages.success(request, f"{self.label} deleted.")
        return redirect(self.list_url_name)


class PurchaseRequestDeleteView(_DocDeleteView):
    model = PurchaseRequest
    list_url_name = "purchase:purchase_request_list"
    label = "Purchase request"


class PurchaseOrderDeleteView(_DocDeleteView):
    model = PurchaseOrder
    list_url_name = "purchase:purchase_order_list"
    label = "Purchase order"


class GoodsReceiptDeleteView(_DocDeleteView):
    model = GoodsReceipt
    list_url_name = "purchase:goods_receipt_list"
    label = "Goods receipt"


class PurchaseReturnDeleteView(_DocDeleteView):
    model = PurchaseReturn
    list_url_name = "purchase:purchase_return_list"
    label = "Purchase return"


class PurchaseRequestApproveView(PurchaseAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(PurchaseRequest, pk=pk, tenant=request.hrm_tenant)
        if obj.status != PurchaseRequest.Status.DRAFT:
            messages.warning(request, "Only draft requests can be approved.")
            return redirect("purchase:purchase_request_list")
        obj.status = PurchaseRequest.Status.APPROVED
        obj.save(update_fields=["status", "updated_at"])
        messages.success(request, "Purchase request approved.")
        return redirect("purchase:purchase_request_list")


class PurchaseOrderApproveView(PurchaseAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(PurchaseOrder, pk=pk, tenant=request.hrm_tenant)
        if obj.status != PurchaseOrder.Status.DRAFT:
            messages.warning(request, "Only draft purchase orders can be approved.")
            return redirect("purchase:purchase_order_list")
        obj.status = PurchaseOrder.Status.APPROVED
        obj.save(update_fields=["status", "updated_at"])
        messages.success(request, "Purchase order approved.")
        return redirect("purchase:purchase_order_list")


class GoodsReceiptPostView(PurchaseAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(GoodsReceipt, pk=pk, tenant=request.hrm_tenant)
        if obj.status != GoodsReceipt.Status.DRAFT:
            messages.warning(request, "Only draft goods receipts can be posted.")
            return redirect("purchase:goods_receipt_list")
        obj.status = GoodsReceipt.Status.POSTED
        obj.save(update_fields=["status", "updated_at"])

        status, note = sync_grn_to_finance_ap_invoice(receipt=obj)
        if status == "synced":
            messages.success(request, f"Goods receipt posted. {note}")
        elif status == "skipped":
            obj.finance_sync_status = GoodsReceipt.FinanceSyncStatus.SKIPPED
            obj.finance_sync_note = note
            obj.save(update_fields=["finance_sync_status", "finance_sync_note", "updated_at"])
            messages.success(request, f"Goods receipt posted. Finance sync skipped: {note}")
        else:
            obj.finance_sync_status = GoodsReceipt.FinanceSyncStatus.ERROR
            obj.finance_sync_note = note
            obj.save(update_fields=["finance_sync_status", "finance_sync_note", "updated_at"])
            messages.warning(request, f"Goods receipt posted, but finance sync issue: {note}")
        return redirect("purchase:goods_receipt_list")


class PurchaseReturnPostView(PurchaseAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(PurchaseReturn, pk=pk, tenant=request.hrm_tenant)
        if obj.status != PurchaseReturn.Status.DRAFT:
            messages.warning(request, "Only draft purchase returns can be posted.")
            return redirect("purchase:purchase_return_list")
        obj.status = PurchaseReturn.Status.POSTED
        obj.save(update_fields=["status", "updated_at"])
        messages.success(request, "Purchase return posted.")
        return redirect("purchase:purchase_return_list")

