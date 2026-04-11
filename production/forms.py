from django import forms
from django.forms import inlineformset_factory
from django.urls import reverse_lazy

from foundation.models import Product, Warehouse

from .models import (
    BillOfMaterial,
    BillOfMaterialLine,
    IssueForProduction,
    IssueForProductionLine,
    ProductionOrder,
    ProductionOrderMaterial,
    ReceiptFromProduction,
)

_ctrl = (
    "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-ring"
)


class BillOfMaterialForm(forms.ModelForm):
    class Meta:
        model = BillOfMaterial
        fields = ["doc_no", "product", "version", "bom_date", "notes"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "product": forms.Select(attrs={"class": _ctrl}),
            "version": forms.TextInput(attrs={"class": _ctrl}),
            "bom_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(tenant=tenant).order_by("name") if tenant else Product.objects.none()
        self.fields["product"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["product"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_products")


class BillOfMaterialLineForm(forms.ModelForm):
    class Meta:
        model = BillOfMaterialLine
        fields = ["component_product", "warehouse", "quantity", "scrap_percent", "unit_cost", "line_total"]
        widgets = {
            "component_product": forms.Select(attrs={"class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "quantity": forms.NumberInput(attrs={"class": _ctrl + " js-qty", "step": "any"}),
            "scrap_percent": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "unit_cost": forms.NumberInput(attrs={"class": _ctrl + " js-unit-cost", "step": "any"}),
            "line_total": forms.NumberInput(attrs={"class": _ctrl + " js-line-total", "step": "any", "readonly": "readonly"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["component_product"].queryset = Product.objects.filter(tenant=tenant).order_by("name")
            self.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True).order_by("name")
        else:
            self.fields["component_product"].queryset = Product.objects.none()
            self.fields["warehouse"].queryset = Warehouse.objects.none()
        self.fields["warehouse"].required = False
        self.fields["component_product"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["component_product"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_products")
        self.fields["warehouse"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["warehouse"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_warehouses")


BillOfMaterialLineFormSet = inlineformset_factory(
    BillOfMaterial, BillOfMaterialLine, form=BillOfMaterialLineForm, extra=1, can_delete=True
)


class ProductionOrderForm(forms.ModelForm):
    class Meta:
        model = ProductionOrder
        fields = ["doc_no", "bom", "product", "warehouse", "order_date", "due_date", "planned_quantity", "notes"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "bom": forms.Select(attrs={"class": _ctrl}),
            "product": forms.Select(attrs={"class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "order_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "due_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "planned_quantity": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["bom"].queryset = BillOfMaterial.objects.filter(tenant=tenant).order_by("-bom_date", "-id")
            self.fields["product"].queryset = Product.objects.filter(tenant=tenant).order_by("name")
            self.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True).order_by("name")
        else:
            self.fields["bom"].queryset = BillOfMaterial.objects.none()
            self.fields["product"].queryset = Product.objects.none()
            self.fields["warehouse"].queryset = Warehouse.objects.none()
        self.fields["bom"].required = False
        self.fields["bom"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["product"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["product"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_products")
        self.fields["warehouse"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["warehouse"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_warehouses")


class ProductionOrderMaterialForm(forms.ModelForm):
    class Meta:
        model = ProductionOrderMaterial
        fields = ["component_product", "warehouse", "planned_quantity", "unit_cost", "line_total"]
        widgets = {
            "component_product": forms.Select(attrs={"class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "planned_quantity": forms.NumberInput(attrs={"class": _ctrl + " js-qty", "step": "any"}),
            "unit_cost": forms.NumberInput(attrs={"class": _ctrl + " js-unit-cost", "step": "any"}),
            "line_total": forms.NumberInput(attrs={"class": _ctrl + " js-line-total", "step": "any", "readonly": "readonly"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["component_product"].queryset = Product.objects.filter(tenant=tenant).order_by("name")
            self.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True).order_by("name")
        else:
            self.fields["component_product"].queryset = Product.objects.none()
            self.fields["warehouse"].queryset = Warehouse.objects.none()
        self.fields["warehouse"].required = False
        self.fields["component_product"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["component_product"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_products")
        self.fields["warehouse"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["warehouse"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_warehouses")


ProductionOrderMaterialFormSet = inlineformset_factory(
    ProductionOrder, ProductionOrderMaterial, form=ProductionOrderMaterialForm, extra=1, can_delete=True
)


class IssueForProductionForm(forms.ModelForm):
    class Meta:
        model = IssueForProduction
        fields = ["doc_no", "production_order", "issue_date", "warehouse", "notes"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "production_order": forms.Select(attrs={"class": _ctrl}),
            "issue_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["production_order"].queryset = ProductionOrder.objects.filter(tenant=tenant).order_by("-order_date", "-id")
            self.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True).order_by("name")
        else:
            self.fields["production_order"].queryset = ProductionOrder.objects.none()
            self.fields["warehouse"].queryset = Warehouse.objects.none()
        self.fields["production_order"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["warehouse"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["warehouse"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_warehouses")


class IssueForProductionLineForm(forms.ModelForm):
    class Meta:
        model = IssueForProductionLine
        fields = ["order_material", "component_product", "quantity", "unit_cost", "line_total"]
        widgets = {
            "order_material": forms.Select(attrs={"class": _ctrl}),
            "component_product": forms.Select(attrs={"class": _ctrl}),
            "quantity": forms.NumberInput(attrs={"class": _ctrl + " js-qty", "step": "any"}),
            "unit_cost": forms.NumberInput(attrs={"class": _ctrl + " js-unit-cost", "step": "any"}),
            "line_total": forms.NumberInput(attrs={"class": _ctrl + " js-line-total", "step": "any", "readonly": "readonly"}),
        }

    def __init__(self, *args, tenant=None, production_order=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["component_product"].queryset = Product.objects.filter(tenant=tenant).order_by("name")
            qs = ProductionOrderMaterial.objects.filter(production_order__tenant=tenant).select_related("production_order", "component_product")
            if production_order:
                qs = qs.filter(production_order=production_order)
            self.fields["order_material"].queryset = qs.order_by("id")
        else:
            self.fields["component_product"].queryset = Product.objects.none()
            self.fields["order_material"].queryset = ProductionOrderMaterial.objects.none()
        self.fields["order_material"].required = False
        self.fields["order_material"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["component_product"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["component_product"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_products")


IssueForProductionLineFormSet = inlineformset_factory(
    IssueForProduction, IssueForProductionLine, form=IssueForProductionLineForm, extra=1, can_delete=True
)


class ReceiptFromProductionForm(forms.ModelForm):
    class Meta:
        model = ReceiptFromProduction
        fields = [
            "doc_no",
            "production_order",
            "receipt_date",
            "warehouse",
            "quantity_received",
            "unit_cost",
            "total_amount",
            "notes",
        ]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "production_order": forms.Select(attrs={"class": _ctrl}),
            "receipt_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "quantity_received": forms.NumberInput(attrs={"class": _ctrl + " js-qty", "step": "any"}),
            "unit_cost": forms.NumberInput(attrs={"class": _ctrl + " js-unit-cost", "step": "any"}),
            "total_amount": forms.NumberInput(attrs={"class": _ctrl + " js-line-total", "step": "any", "readonly": "readonly"}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["production_order"].queryset = ProductionOrder.objects.filter(tenant=tenant).order_by("-order_date", "-id")
            self.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True).order_by("name")
        else:
            self.fields["production_order"].queryset = ProductionOrder.objects.none()
            self.fields["warehouse"].queryset = Warehouse.objects.none()
        self.fields["production_order"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["warehouse"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["warehouse"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_warehouses")

