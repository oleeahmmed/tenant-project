from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .forms import (
    BillOfMaterialForm,
    BillOfMaterialLineFormSet,
    IssueForProductionForm,
    IssueForProductionLineFormSet,
    ProductionOrderForm,
    ProductionOrderMaterialFormSet,
    ReceiptFromProductionForm,
)
from .mixins import ProductionAdminMixin, ProductionDashboardAccessMixin, ProductionPageContextMixin
from .models import BillOfMaterial, IssueForProduction, ProductionOrder, ReceiptFromProduction


def _render_doc_form(request, *, form, formset, page_title, action_url, list_url):
    return render(
        request,
        "production/document_form.html",
        {
            "form": form,
            "formset": formset,
            "page_title": page_title,
            "action_url": action_url,
            "list_url": list_url,
            "active_page": "production",
        },
    )


def _render_single_form(request, *, form, page_title, action_url, list_url):
    return render(
        request,
        "production/document_form_single.html",
        {
            "form": form,
            "page_title": page_title,
            "action_url": action_url,
            "list_url": list_url,
            "active_page": "production",
        },
    )


class ProductionDashboardView(ProductionDashboardAccessMixin, ProductionPageContextMixin, TemplateView):
    template_name = "production/dashboard.html"
    page_title = "Production"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = self.request.hrm_tenant
        ctx["bom_count"] = BillOfMaterial.objects.filter(tenant=t).count()
        ctx["order_count"] = ProductionOrder.objects.filter(tenant=t).count()
        ctx["issue_count"] = IssueForProduction.objects.filter(tenant=t).count()
        ctx["receipt_count"] = ReceiptFromProduction.objects.filter(tenant=t).count()
        return ctx


class _BaseList(ProductionAdminMixin, ProductionPageContextMixin, ListView):
    template_name = "production/document_list.html"
    context_object_name = "object_list"
    page_title = ""
    create_url = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["create_url"] = self.create_url
        return ctx


class BillOfMaterialListView(_BaseList):
    model = BillOfMaterial
    page_title = "Bill of materials"
    create_url = "production:bom_create"

    def get_queryset(self):
        return BillOfMaterial.objects.filter(tenant=self.request.hrm_tenant).select_related("product").order_by("-bom_date", "-id")


class ProductionOrderListView(_BaseList):
    model = ProductionOrder
    page_title = "Production orders"
    create_url = "production:order_create"

    def get_queryset(self):
        return ProductionOrder.objects.filter(tenant=self.request.hrm_tenant).select_related("product", "warehouse", "bom").order_by("-order_date", "-id")


class IssueForProductionListView(_BaseList):
    model = IssueForProduction
    page_title = "Issue for production"
    create_url = "production:issue_create"

    def get_queryset(self):
        return IssueForProduction.objects.filter(tenant=self.request.hrm_tenant).select_related("production_order", "warehouse").order_by("-issue_date", "-id")


class ReceiptFromProductionListView(_BaseList):
    model = ReceiptFromProduction
    page_title = "Receipt from production"
    create_url = "production:receipt_create"

    def get_queryset(self):
        return ReceiptFromProduction.objects.filter(tenant=self.request.hrm_tenant).select_related("production_order", "warehouse").order_by("-receipt_date", "-id")


class _BaseDetail(ProductionAdminMixin, ProductionPageContextMixin, DetailView):
    template_name = "production/document_detail.html"
    context_object_name = "object"
    page_title = ""
    list_url = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url"] = self.list_url
        return ctx


class BillOfMaterialDetailView(_BaseDetail):
    model = BillOfMaterial
    page_title = "BOM details"
    list_url = "production:bom_list"

    def get_queryset(self):
        return BillOfMaterial.objects.filter(tenant=self.request.hrm_tenant).select_related("product").prefetch_related("lines__component_product", "lines__warehouse")


class ProductionOrderDetailView(_BaseDetail):
    model = ProductionOrder
    page_title = "Production order details"
    list_url = "production:order_list"

    def get_queryset(self):
        return ProductionOrder.objects.filter(tenant=self.request.hrm_tenant).select_related("product", "warehouse", "bom").prefetch_related("materials__component_product", "materials__warehouse")


class IssueForProductionDetailView(_BaseDetail):
    model = IssueForProduction
    page_title = "Issue details"
    list_url = "production:issue_list"

    def get_queryset(self):
        return IssueForProduction.objects.filter(tenant=self.request.hrm_tenant).select_related("production_order", "warehouse").prefetch_related("lines__component_product", "lines__order_material")


class ReceiptFromProductionDetailView(_BaseDetail):
    model = ReceiptFromProduction
    page_title = "Receipt details"
    list_url = "production:receipt_list"

    def get_queryset(self):
        return ReceiptFromProduction.objects.filter(tenant=self.request.hrm_tenant).select_related("production_order", "warehouse")


class BillOfMaterialCreateView(ProductionAdminMixin, View):
    def get(self, request):
        form = BillOfMaterialForm(tenant=request.hrm_tenant)
        formset = BillOfMaterialLineFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add BOM", action_url=reverse_lazy("production:bom_create"), list_url=reverse_lazy("production:bom_list"))

    def post(self, request):
        form = BillOfMaterialForm(request.POST, tenant=request.hrm_tenant)
        formset = BillOfMaterialLineFormSet(request.POST, prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.tenant = request.hrm_tenant
                obj.save()
                formset.instance = obj
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_component_cost", "updated_at"])
            messages.success(request, "BOM created.")
            return redirect("production:bom_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add BOM", action_url=reverse_lazy("production:bom_create"), list_url=reverse_lazy("production:bom_list"))


class BillOfMaterialUpdateView(ProductionAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(BillOfMaterial, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != BillOfMaterial.Status.DRAFT:
            messages.error(request, "Only draft BOM can be edited.")
            return redirect("production:bom_list")
        form = BillOfMaterialForm(instance=obj, tenant=request.hrm_tenant)
        formset = BillOfMaterialLineFormSet(instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit BOM", action_url=reverse_lazy("production:bom_edit", kwargs={"pk": pk}), list_url=reverse_lazy("production:bom_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = BillOfMaterialForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = BillOfMaterialLineFormSet(request.POST, instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save()
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_component_cost", "updated_at"])
            messages.success(request, "BOM updated.")
            return redirect("production:bom_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit BOM", action_url=reverse_lazy("production:bom_edit", kwargs={"pk": pk}), list_url=reverse_lazy("production:bom_list"))


class ProductionOrderCreateView(ProductionAdminMixin, View):
    def get(self, request):
        form = ProductionOrderForm(tenant=request.hrm_tenant)
        formset = ProductionOrderMaterialFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add production order", action_url=reverse_lazy("production:order_create"), list_url=reverse_lazy("production:order_list"))

    def post(self, request):
        form = ProductionOrderForm(request.POST, tenant=request.hrm_tenant)
        formset = ProductionOrderMaterialFormSet(request.POST, prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.tenant = request.hrm_tenant
                obj.save()
                formset.instance = obj
                formset.save()
            messages.success(request, "Production order created.")
            return redirect("production:order_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add production order", action_url=reverse_lazy("production:order_create"), list_url=reverse_lazy("production:order_list"))


class ProductionOrderUpdateView(ProductionAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(ProductionOrder, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != ProductionOrder.Status.DRAFT:
            messages.error(request, "Only draft production orders are editable.")
            return redirect("production:order_list")
        form = ProductionOrderForm(instance=obj, tenant=request.hrm_tenant)
        formset = ProductionOrderMaterialFormSet(instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit production order", action_url=reverse_lazy("production:order_edit", kwargs={"pk": pk}), list_url=reverse_lazy("production:order_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = ProductionOrderForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = ProductionOrderMaterialFormSet(request.POST, instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["warehouse"].queryset = f.fields["warehouse"].queryset.model.objects.filter(tenant=request.hrm_tenant, is_active=True).order_by("name")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, "Production order updated.")
            return redirect("production:order_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit production order", action_url=reverse_lazy("production:order_edit", kwargs={"pk": pk}), list_url=reverse_lazy("production:order_list"))


class IssueForProductionCreateView(ProductionAdminMixin, View):
    def get(self, request):
        form = IssueForProductionForm(tenant=request.hrm_tenant)
        formset = IssueForProductionLineFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["order_material"].queryset = f.fields["order_material"].queryset.model.objects.filter(production_order__tenant=request.hrm_tenant)
        return _render_doc_form(request, form=form, formset=formset, page_title="Add issue for production", action_url=reverse_lazy("production:issue_create"), list_url=reverse_lazy("production:issue_list"))

    def post(self, request):
        form = IssueForProductionForm(request.POST, tenant=request.hrm_tenant)
        order = None
        if form.is_valid():
            order = form.cleaned_data.get("production_order")
        formset = IssueForProductionLineFormSet(request.POST, prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            qs = f.fields["order_material"].queryset.model.objects.filter(production_order__tenant=request.hrm_tenant)
            if order:
                qs = qs.filter(production_order=order)
            f.fields["order_material"].queryset = qs
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.tenant = request.hrm_tenant
                obj.save()
                formset.instance = obj
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_amount", "updated_at"])
            messages.success(request, "Issue document created.")
            return redirect("production:issue_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Add issue for production", action_url=reverse_lazy("production:issue_create"), list_url=reverse_lazy("production:issue_list"))


class IssueForProductionUpdateView(ProductionAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(IssueForProduction, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != IssueForProduction.Status.DRAFT:
            messages.error(request, "Only draft issue documents are editable.")
            return redirect("production:issue_list")
        form = IssueForProductionForm(instance=obj, tenant=request.hrm_tenant)
        formset = IssueForProductionLineFormSet(instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            f.fields["order_material"].queryset = f.fields["order_material"].queryset.model.objects.filter(production_order=obj.production_order)
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit issue for production", action_url=reverse_lazy("production:issue_edit", kwargs={"pk": pk}), list_url=reverse_lazy("production:issue_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = IssueForProductionForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        order = None
        if form.is_valid():
            order = form.cleaned_data.get("production_order")
        formset = IssueForProductionLineFormSet(request.POST, instance=obj, prefix="lines")
        for f in formset.forms:
            f.fields["component_product"].queryset = f.fields["component_product"].queryset.model.objects.filter(tenant=request.hrm_tenant).order_by("name")
            qs = f.fields["order_material"].queryset.model.objects.filter(production_order__tenant=request.hrm_tenant)
            if order:
                qs = qs.filter(production_order=order)
            f.fields["order_material"].queryset = qs
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                obj = form.save()
                formset.save()
                obj.recalc_totals()
                obj.save(update_fields=["total_amount", "updated_at"])
            messages.success(request, "Issue document updated.")
            return redirect("production:issue_list")
        return _render_doc_form(request, form=form, formset=formset, page_title="Edit issue for production", action_url=reverse_lazy("production:issue_edit", kwargs={"pk": pk}), list_url=reverse_lazy("production:issue_list"))


class ReceiptFromProductionCreateView(ProductionAdminMixin, View):
    def get(self, request):
        form = ReceiptFromProductionForm(tenant=request.hrm_tenant)
        return _render_single_form(request, form=form, page_title="Add receipt from production", action_url=reverse_lazy("production:receipt_create"), list_url=reverse_lazy("production:receipt_list"))

    def post(self, request):
        form = ReceiptFromProductionForm(request.POST, tenant=request.hrm_tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.hrm_tenant
            obj.save()
            messages.success(request, "Receipt document created.")
            return redirect("production:receipt_list")
        return _render_single_form(request, form=form, page_title="Add receipt from production", action_url=reverse_lazy("production:receipt_create"), list_url=reverse_lazy("production:receipt_list"))


class ReceiptFromProductionUpdateView(ProductionAdminMixin, View):
    def _obj(self, request, pk):
        return get_object_or_404(ReceiptFromProduction, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self._obj(request, pk)
        if obj.status != ReceiptFromProduction.Status.DRAFT:
            messages.error(request, "Only draft receipt documents are editable.")
            return redirect("production:receipt_list")
        form = ReceiptFromProductionForm(instance=obj, tenant=request.hrm_tenant)
        return _render_single_form(request, form=form, page_title="Edit receipt from production", action_url=reverse_lazy("production:receipt_edit", kwargs={"pk": pk}), list_url=reverse_lazy("production:receipt_list"))

    def post(self, request, pk):
        obj = self._obj(request, pk)
        form = ReceiptFromProductionForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Receipt document updated.")
            return redirect("production:receipt_list")
        return _render_single_form(request, form=form, page_title="Edit receipt from production", action_url=reverse_lazy("production:receipt_edit", kwargs={"pk": pk}), list_url=reverse_lazy("production:receipt_list"))


class _DocDeleteView(ProductionAdminMixin, View):
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


class BillOfMaterialDeleteView(_DocDeleteView):
    model = BillOfMaterial
    list_url_name = "production:bom_list"
    label = "BOM"


class ProductionOrderDeleteView(_DocDeleteView):
    model = ProductionOrder
    list_url_name = "production:order_list"
    label = "Production order"


class IssueForProductionDeleteView(_DocDeleteView):
    model = IssueForProduction
    list_url_name = "production:issue_list"
    label = "Issue document"


class ReceiptFromProductionDeleteView(_DocDeleteView):
    model = ReceiptFromProduction
    list_url_name = "production:receipt_list"
    label = "Receipt document"


class BillOfMaterialActivateView(ProductionAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(BillOfMaterial, pk=pk, tenant=request.hrm_tenant)
        if obj.status != BillOfMaterial.Status.DRAFT:
            messages.warning(request, "Only draft BOM can be activated.")
            return redirect("production:bom_list")
        obj.status = BillOfMaterial.Status.ACTIVE
        obj.save(update_fields=["status", "updated_at"])
        messages.success(request, "BOM activated.")
        return redirect("production:bom_list")


class ProductionOrderReleaseView(ProductionAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(ProductionOrder, pk=pk, tenant=request.hrm_tenant)
        if obj.status != ProductionOrder.Status.DRAFT:
            messages.warning(request, "Only draft production orders can be released.")
            return redirect("production:order_list")
        obj.status = ProductionOrder.Status.RELEASED
        obj.save(update_fields=["status", "updated_at"])
        messages.success(request, "Production order released.")
        return redirect("production:order_list")


class IssueForProductionPostView(ProductionAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(IssueForProduction, pk=pk, tenant=request.hrm_tenant)
        if obj.status != IssueForProduction.Status.DRAFT:
            messages.warning(request, "Only draft issue documents can be posted.")
            return redirect("production:issue_list")
        with transaction.atomic():
            obj.status = IssueForProduction.Status.POSTED
            obj.save(update_fields=["status", "updated_at"])
            for line in obj.lines.select_related("order_material").all():
                if line.order_material_id:
                    m = line.order_material
                    m.issued_quantity = (m.issued_quantity or 0) + (line.quantity or 0)
                    m.save(update_fields=["issued_quantity"])
            order = obj.production_order
            if order.status in (ProductionOrder.Status.DRAFT, ProductionOrder.Status.RELEASED):
                order.status = ProductionOrder.Status.IN_PROCESS
                order.save(update_fields=["status", "updated_at"])
        messages.success(request, "Issue document posted.")
        return redirect("production:issue_list")


class ReceiptFromProductionPostView(ProductionAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(ReceiptFromProduction, pk=pk, tenant=request.hrm_tenant)
        if obj.status != ReceiptFromProduction.Status.DRAFT:
            messages.warning(request, "Only draft receipt documents can be posted.")
            return redirect("production:receipt_list")
        with transaction.atomic():
            obj.status = ReceiptFromProduction.Status.POSTED
            obj.save(update_fields=["status", "updated_at"])
            order = obj.production_order
            order.produced_quantity = (order.produced_quantity or 0) + (obj.quantity_received or 0)
            if order.produced_quantity >= order.planned_quantity:
                order.status = ProductionOrder.Status.COMPLETED
            elif order.status in (ProductionOrder.Status.DRAFT, ProductionOrder.Status.RELEASED):
                order.status = ProductionOrder.Status.IN_PROCESS
            order.save(update_fields=["produced_quantity", "status", "updated_at"])
        messages.success(request, "Receipt document posted.")
        return redirect("production:receipt_list")

