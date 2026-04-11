from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from foundation.models import Customer

from .forms import (
    DeliveryNoteForm,
    DeliveryNoteLineFormSet,
    SalesOrderForm,
    SalesOrderLineFormSet,
    SalesQuotationForm,
    SalesQuotationLineFormSet,
    SalesReturnForm,
    SalesReturnLineFormSet,
)
from .mixins import SalesAdminMixin, SalesDashboardAccessMixin, SalesPageContextMixin
from .models import DeliveryNote, SalesOrder, SalesQuotation, SalesReturn
from .services.integrations import sync_delivery_to_finance_ar_invoice


def _render_doc_form(request, *, form, formset, page_title, action_url, list_url):
    return render(
        request,
        "sales/document_form.html",
        {
            "form": form,
            "formset": formset,
            "page_title": page_title,
            "action_url": action_url,
            "list_url": list_url,
            "active_page": "sales",
        },
    )


class SalesDashboardView(SalesDashboardAccessMixin, SalesPageContextMixin, TemplateView):
    template_name = "sales/dashboard.html"
    page_title = "Sales"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = self.request.hrm_tenant
        ctx["quotation_count"] = SalesQuotation.objects.filter(tenant=t).count()
        ctx["order_count"] = SalesOrder.objects.filter(tenant=t).count()
        ctx["delivery_count"] = DeliveryNote.objects.filter(tenant=t).count()
        ctx["return_count"] = SalesReturn.objects.filter(tenant=t).count()
        return ctx


class _BaseList(SalesAdminMixin, SalesPageContextMixin, ListView):
    template_name = "sales/document_list.html"
    context_object_name = "object_list"
    page_title = ""
    create_url = ""
    paginate_by = 20
    date_field = ""

    def get_queryset(self):
        qs = self.model.objects.filter(tenant=self.request.hrm_tenant)
        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        customer_id = (self.request.GET.get("customer") or "").strip()
        ordering = (self.request.GET.get("sort") or (f"-{self.date_field}" if self.date_field else "-id")).strip()

        if q:
            filters = Q(doc_no__icontains=q) | Q(notes__icontains=q)
            if hasattr(self.model, "reference"):
                filters = filters | Q(reference__icontains=q)
            qs = qs.filter(filters)
        if status:
            qs = qs.filter(status=status)
        if customer_id.isdigit():
            qs = qs.filter(customer_id=int(customer_id))

        allowed = {"-id", "id"}
        if self.date_field:
            allowed.update({self.date_field, f"-{self.date_field}"})
        if ordering not in allowed:
            ordering = f"-{self.date_field}" if self.date_field else "-id"
        return qs.select_related("customer").order_by(ordering, "-id")

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
        customer_id = (self.request.GET.get("customer") or "").strip()
        filtered_customer = None
        if customer_id.isdigit():
            filtered_customer = Customer.objects.filter(
                tenant=self.request.hrm_tenant, pk=int(customer_id)
            ).only("id", "customer_code", "name").first()
        ctx.update(
            {
                "create_url": self.create_url,
                "qs_no_page": params.urlencode(),
                "selected": {
                    "q": self.request.GET.get("q", ""),
                    "status": self.request.GET.get("status", ""),
                    "customer": customer_id,
                    "sort": self.request.GET.get("sort", f"-{self.date_field}" if self.date_field else "-id"),
                    "page_size": self.request.GET.get("page_size", str(self.paginate_by)),
                },
                "sort_newest": f"-{self.date_field}" if self.date_field else "-id",
                "sort_oldest": self.date_field if self.date_field else "id",
                "status_choices": getattr(self.model, "Status", None).choices if hasattr(self.model, "Status") else [],
                "filtered_customer": filtered_customer,
            }
        )
        return ctx


class SalesQuotationListView(_BaseList):
    model = SalesQuotation
    page_title = "Sales quotations"
    create_url = "sales:quotation_create"
    date_field = "quote_date"


class SalesOrderListView(_BaseList):
    model = SalesOrder
    page_title = "Sales orders"
    create_url = "sales:order_create"
    date_field = "order_date"


class DeliveryNoteListView(_BaseList):
    model = DeliveryNote
    page_title = "Delivery notes"
    create_url = "sales:delivery_create"
    date_field = "delivery_date"


class SalesReturnListView(_BaseList):
    model = SalesReturn
    page_title = "Sales returns"
    create_url = "sales:return_create"
    date_field = "return_date"


class _BaseDetail(SalesAdminMixin, SalesPageContextMixin, DetailView):
    template_name = "sales/document_detail.html"
    context_object_name = "object"
    page_title = ""
    list_url = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url"] = self.list_url
        return ctx


class SalesQuotationDetailView(_BaseDetail):
    model = SalesQuotation
    page_title = "Sales quotation details"
    list_url = "sales:quotation_list"

    def get_queryset(self):
        return SalesQuotation.objects.filter(tenant=self.request.hrm_tenant).select_related("customer").prefetch_related("lines__product")


class SalesOrderDetailView(_BaseDetail):
    model = SalesOrder
    page_title = "Sales order details"
    list_url = "sales:order_list"

    def get_queryset(self):
        return SalesOrder.objects.filter(tenant=self.request.hrm_tenant).select_related("customer", "quotation").prefetch_related("lines__product")


class DeliveryNoteDetailView(_BaseDetail):
    model = DeliveryNote
    page_title = "Delivery note details"
    list_url = "sales:delivery_list"

    def get_queryset(self):
        return DeliveryNote.objects.filter(tenant=self.request.hrm_tenant).select_related("customer", "order").prefetch_related("lines__product")


class SalesReturnDetailView(_BaseDetail):
    model = SalesReturn
    page_title = "Sales return details"
    list_url = "sales:return_list"

    def get_queryset(self):
        return SalesReturn.objects.filter(tenant=self.request.hrm_tenant).select_related("customer", "delivery").prefetch_related("lines__product")


class SalesQuotationCreateView(SalesAdminMixin, View):
    def get(self, request):
        form = SalesQuotationForm(tenant=request.hrm_tenant)
        formset = SalesQuotationLineFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add sales quotation", action_url=reverse_lazy("sales:quotation_create"), list_url=reverse_lazy("sales:quotation_list"))

    def post(self, request):
        form = SalesQuotationForm(request.POST, tenant=request.hrm_tenant)
        formset = SalesQuotationLineFormSet(request.POST, prefix="lines")
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
            messages.success(request, "Sales quotation created.")
            return redirect("sales:quotation_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add sales quotation", action_url=reverse_lazy("sales:quotation_create"), list_url=reverse_lazy("sales:quotation_list"))


class SalesQuotationUpdateView(SalesAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(SalesQuotation, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != SalesQuotation.Status.DRAFT:
            messages.error(request, "Only draft sales quotations are editable.")
            return redirect("sales:quotation_list")
        form = SalesQuotationForm(instance=obj, tenant=request.hrm_tenant)
        formset = SalesQuotationLineFormSet(instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit sales quotation", action_url=reverse_lazy("sales:quotation_edit", kwargs={"pk": pk}), list_url=reverse_lazy("sales:quotation_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = SalesQuotationForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = SalesQuotationLineFormSet(request.POST, instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save()
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["subtotal", "total_amount", "updated_at"])
            messages.success(request, "Sales quotation updated.")
            return redirect("sales:quotation_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit sales quotation", action_url=reverse_lazy("sales:quotation_edit", kwargs={"pk": pk}), list_url=reverse_lazy("sales:quotation_list"))


class SalesOrderCreateView(SalesAdminMixin, View):
    def get(self, request):
        form = SalesOrderForm(tenant=request.hrm_tenant)
        formset = SalesOrderLineFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add sales order", action_url=reverse_lazy("sales:order_create"), list_url=reverse_lazy("sales:order_list"))

    def post(self, request):
        form = SalesOrderForm(request.POST, tenant=request.hrm_tenant)
        formset = SalesOrderLineFormSet(request.POST, prefix="lines")
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
            messages.success(request, "Sales order created.")
            return redirect("sales:order_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add sales order", action_url=reverse_lazy("sales:order_create"), list_url=reverse_lazy("sales:order_list"))


class SalesOrderUpdateView(SalesAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(SalesOrder, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != SalesOrder.Status.DRAFT:
            messages.error(request, "Only draft sales orders are editable.")
            return redirect("sales:order_list")
        form = SalesOrderForm(instance=obj, tenant=request.hrm_tenant)
        formset = SalesOrderLineFormSet(instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit sales order", action_url=reverse_lazy("sales:order_edit", kwargs={"pk": pk}), list_url=reverse_lazy("sales:order_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = SalesOrderForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = SalesOrderLineFormSet(request.POST, instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save()
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["subtotal", "total_amount", "updated_at"])
            messages.success(request, "Sales order updated.")
            return redirect("sales:order_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit sales order", action_url=reverse_lazy("sales:order_edit", kwargs={"pk": pk}), list_url=reverse_lazy("sales:order_list"))


class DeliveryNoteCreateView(SalesAdminMixin, View):
    def get(self, request):
        form = DeliveryNoteForm(tenant=request.hrm_tenant)
        formset = DeliveryNoteLineFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            f.fields["order_line"].queryset = f.fields["order_line"].queryset.model.objects.filter(order__tenant=request.hrm_tenant)
        return _render_doc_form(request, form=form, formset=formset, page_title="Add delivery note", action_url=reverse_lazy("sales:delivery_create"), list_url=reverse_lazy("sales:delivery_list"))

    def post(self, request):
        form = DeliveryNoteForm(request.POST, tenant=request.hrm_tenant)
        order = None
        if form.is_valid():
            order = form.cleaned_data.get("order")
        formset = DeliveryNoteLineFormSet(request.POST, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            qs = f.fields["order_line"].queryset.model.objects.filter(order__tenant=request.hrm_tenant)
            if order:
                qs = qs.filter(order=order)
            f.fields["order_line"].queryset = qs
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.tenant = request.hrm_tenant
                obj.save()
                formset.instance = obj
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_amount", "updated_at"])
            messages.success(request, "Delivery note created.")
            return redirect("sales:delivery_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add delivery note", action_url=reverse_lazy("sales:delivery_create"), list_url=reverse_lazy("sales:delivery_list"))


class DeliveryNoteUpdateView(SalesAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(DeliveryNote, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != DeliveryNote.Status.DRAFT:
            messages.error(request, "Only draft delivery notes are editable.")
            return redirect("sales:delivery_list")
        form = DeliveryNoteForm(instance=obj, tenant=request.hrm_tenant)
        formset = DeliveryNoteLineFormSet(instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            f.fields["order_line"].queryset = f.fields["order_line"].queryset.model.objects.filter(order=obj.order)
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit delivery note", action_url=reverse_lazy("sales:delivery_edit", kwargs={"pk": pk}), list_url=reverse_lazy("sales:delivery_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = DeliveryNoteForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        order = None
        if form.is_valid():
            order = form.cleaned_data.get("order")
        formset = DeliveryNoteLineFormSet(request.POST, instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            qs = f.fields["order_line"].queryset.model.objects.filter(order__tenant=request.hrm_tenant)
            if order:
                qs = qs.filter(order=order)
            f.fields["order_line"].queryset = qs
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save()
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_amount", "updated_at"])
            messages.success(request, "Delivery note updated.")
            return redirect("sales:delivery_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit delivery note", action_url=reverse_lazy("sales:delivery_edit", kwargs={"pk": pk}), list_url=reverse_lazy("sales:delivery_list"))


class SalesReturnCreateView(SalesAdminMixin, View):
    def get(self, request):
        form = SalesReturnForm(tenant=request.hrm_tenant)
        formset = SalesReturnLineFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            f.fields["delivery_line"].queryset = f.fields["delivery_line"].queryset.model.objects.filter(delivery__tenant=request.hrm_tenant)
        return _render_doc_form(request, form=form, formset=formset, page_title="Add sales return", action_url=reverse_lazy("sales:return_create"), list_url=reverse_lazy("sales:return_list"))

    def post(self, request):
        form = SalesReturnForm(request.POST, tenant=request.hrm_tenant)
        delivery = None
        if form.is_valid():
            delivery = form.cleaned_data.get("delivery")
        formset = SalesReturnLineFormSet(request.POST, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            qs = f.fields["delivery_line"].queryset.model.objects.filter(delivery__tenant=request.hrm_tenant)
            if delivery:
                qs = qs.filter(delivery=delivery)
            f.fields["delivery_line"].queryset = qs
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.tenant = request.hrm_tenant
                obj.save()
                formset.instance = obj
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_amount", "updated_at"])
            messages.success(request, "Sales return created.")
            return redirect("sales:return_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add sales return", action_url=reverse_lazy("sales:return_create"), list_url=reverse_lazy("sales:return_list"))


class SalesReturnUpdateView(SalesAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(SalesReturn, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != SalesReturn.Status.DRAFT:
            messages.error(request, "Only draft sales returns are editable.")
            return redirect("sales:return_list")
        form = SalesReturnForm(instance=obj, tenant=request.hrm_tenant)
        formset = SalesReturnLineFormSet(instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            f.fields["delivery_line"].queryset = f.fields["delivery_line"].queryset.model.objects.filter(delivery__tenant=request.hrm_tenant)
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit sales return", action_url=reverse_lazy("sales:return_edit", kwargs={"pk": pk}), list_url=reverse_lazy("sales:return_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = SalesReturnForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        delivery = None
        if form.is_valid():
            delivery = form.cleaned_data.get("delivery")
        formset = SalesReturnLineFormSet(request.POST, instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["product"].queryset = f.fields["product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
            qs = f.fields["delivery_line"].queryset.model.objects.filter(delivery__tenant=request.hrm_tenant)
            if delivery:
                qs = qs.filter(delivery=delivery)
            f.fields["delivery_line"].queryset = qs
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save()
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_amount", "updated_at"])
            messages.success(request, "Sales return updated.")
            return redirect("sales:return_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit sales return", action_url=reverse_lazy("sales:return_edit", kwargs={"pk": pk}), list_url=reverse_lazy("sales:return_list"))


class _DocDeleteView(SalesAdminMixin, View):
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


class SalesQuotationDeleteView(_DocDeleteView):
    model = SalesQuotation
    list_url_name = "sales:quotation_list"
    label = "Sales quotation"


class SalesOrderDeleteView(_DocDeleteView):
    model = SalesOrder
    list_url_name = "sales:order_list"
    label = "Sales order"


class DeliveryNoteDeleteView(_DocDeleteView):
    model = DeliveryNote
    list_url_name = "sales:delivery_list"
    label = "Delivery note"


class SalesReturnDeleteView(_DocDeleteView):
    model = SalesReturn
    list_url_name = "sales:return_list"
    label = "Sales return"


class SalesQuotationApproveView(SalesAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(SalesQuotation, pk=pk, tenant=request.hrm_tenant)
        if obj.status != SalesQuotation.Status.DRAFT:
            messages.warning(request, "Only draft sales quotations can be approved.")
            return redirect("sales:quotation_list")
        obj.status = SalesQuotation.Status.APPROVED
        obj.save(update_fields=["status", "updated_at"])
        messages.success(request, "Sales quotation approved.")
        return redirect("sales:quotation_list")


class SalesOrderApproveView(SalesAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(SalesOrder, pk=pk, tenant=request.hrm_tenant)
        if obj.status != SalesOrder.Status.DRAFT:
            messages.warning(request, "Only draft sales orders can be approved.")
            return redirect("sales:order_list")
        obj.status = SalesOrder.Status.APPROVED
        obj.save(update_fields=["status", "updated_at"])
        messages.success(request, "Sales order approved.")
        return redirect("sales:order_list")


class DeliveryNotePostView(SalesAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(DeliveryNote, pk=pk, tenant=request.hrm_tenant)
        if obj.status != DeliveryNote.Status.DRAFT:
            messages.warning(request, "Only draft delivery notes can be posted.")
            return redirect("sales:delivery_list")
        obj.status = DeliveryNote.Status.POSTED
        obj.save(update_fields=["status", "updated_at"])

        status, note = sync_delivery_to_finance_ar_invoice(delivery=obj)
        if status == "synced":
            messages.success(request, f"Delivery note posted. {note}")
        elif status == "skipped":
            obj.finance_sync_status = DeliveryNote.FinanceSyncStatus.SKIPPED
            obj.finance_sync_note = note
            obj.save(update_fields=["finance_sync_status", "finance_sync_note", "updated_at"])
            messages.success(request, f"Delivery note posted. Finance sync skipped: {note}")
        else:
            obj.finance_sync_status = DeliveryNote.FinanceSyncStatus.ERROR
            obj.finance_sync_note = note
            obj.save(update_fields=["finance_sync_status", "finance_sync_note", "updated_at"])
            messages.warning(request, f"Delivery note posted, but finance sync issue: {note}")
        return redirect("sales:delivery_list")


class SalesReturnPostView(SalesAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(SalesReturn, pk=pk, tenant=request.hrm_tenant)
        if obj.status != SalesReturn.Status.DRAFT:
            messages.warning(request, "Only draft sales returns can be posted.")
            return redirect("sales:return_list")
        obj.status = SalesReturn.Status.POSTED
        obj.save(update_fields=["status", "updated_at"])
        messages.success(request, "Sales return posted.")
        return redirect("sales:return_list")

