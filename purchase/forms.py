from django import forms
from django.forms import inlineformset_factory
from django.urls import reverse_lazy

from foundation.models import Product, Supplier, Warehouse

from .models import (
    GoodsReceipt,
    GoodsReceiptLine,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseRequest,
    PurchaseRequestLine,
    PurchaseReturn,
    PurchaseReturnLine,
)

_ctrl = (
    "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-ring"
)


class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ["doc_no", "requester_name", "request_date", "needed_by", "notes"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "requester_name": forms.TextInput(attrs={"class": _ctrl}),
            "request_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "needed_by": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }


class PurchaseRequestLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequestLine
        fields = ["product", "description", "quantity"]
        widgets = {
            "product": forms.Select(attrs={"class": _ctrl}),
            "description": forms.TextInput(attrs={"class": _ctrl}),
            "quantity": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(tenant=tenant).order_by("name") if tenant else Product.objects.none()
        self.fields["product"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["product"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_products")


PurchaseRequestLineFormSet = inlineformset_factory(
    PurchaseRequest, PurchaseRequestLine, form=PurchaseRequestLineForm, extra=1, can_delete=True
)


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            "doc_no",
            "supplier",
            "purchase_request",
            "order_date",
            "expected_date",
            "tax_amount",
            "notes",
        ]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "supplier": forms.Select(attrs={"class": _ctrl}),
            "purchase_request": forms.Select(attrs={"class": _ctrl}),
            "order_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "expected_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "tax_amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["supplier"].queryset = Supplier.objects.filter(tenant=tenant, is_active=True).order_by("name")
            self.fields["purchase_request"].queryset = PurchaseRequest.objects.filter(tenant=tenant).order_by("-request_date", "-id")
        else:
            self.fields["supplier"].queryset = Supplier.objects.none()
            self.fields["purchase_request"].queryset = PurchaseRequest.objects.none()
        self.fields["purchase_request"].required = False
        self.fields["supplier"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["supplier"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_suppliers")
        self.fields["purchase_request"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class PurchaseOrderLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderLine
        fields = ["product", "warehouse", "description", "quantity", "unit_cost", "line_total"]
        widgets = {
            "product": forms.Select(attrs={"class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "description": forms.TextInput(attrs={"class": _ctrl}),
            "quantity": forms.NumberInput(attrs={"class": _ctrl + " js-qty", "step": "any"}),
            "unit_cost": forms.NumberInput(attrs={"class": _ctrl + " js-unit-cost", "step": "any"}),
            "line_total": forms.NumberInput(attrs={"class": _ctrl + " js-line-total", "step": "any", "readonly": "readonly"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["product"].queryset = Product.objects.filter(tenant=tenant).order_by("name")
            self.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True).order_by("name")
        else:
            self.fields["product"].queryset = Product.objects.none()
            self.fields["warehouse"].queryset = Warehouse.objects.none()
        self.fields["warehouse"].required = False
        self.fields["product"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["product"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_products")
        self.fields["warehouse"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["warehouse"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_warehouses")


PurchaseOrderLineFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseOrderLine, form=PurchaseOrderLineForm, extra=1, can_delete=True
)


class GoodsReceiptForm(forms.ModelForm):
    class Meta:
        model = GoodsReceipt
        fields = ["doc_no", "purchase_order", "supplier", "receipt_date", "notes"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "purchase_order": forms.Select(attrs={"class": _ctrl}),
            "supplier": forms.Select(attrs={"class": _ctrl}),
            "receipt_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["purchase_order"].queryset = PurchaseOrder.objects.filter(tenant=tenant).order_by("-order_date", "-id")
            self.fields["supplier"].queryset = Supplier.objects.filter(tenant=tenant, is_active=True).order_by("name")
        else:
            self.fields["purchase_order"].queryset = PurchaseOrder.objects.none()
            self.fields["supplier"].queryset = Supplier.objects.none()
        self.fields["purchase_order"].required = False
        self.fields["supplier"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["supplier"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_suppliers")
        self.fields["purchase_order"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class GoodsReceiptLineForm(forms.ModelForm):
    class Meta:
        model = GoodsReceiptLine
        fields = ["purchase_order_line", "product", "warehouse", "quantity_received", "unit_cost", "line_total"]
        widgets = {
            "purchase_order_line": forms.Select(attrs={"class": _ctrl}),
            "product": forms.Select(attrs={"class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "quantity_received": forms.NumberInput(attrs={"class": _ctrl + " js-qty", "step": "any"}),
            "unit_cost": forms.NumberInput(attrs={"class": _ctrl + " js-unit-cost", "step": "any"}),
            "line_total": forms.NumberInput(attrs={"class": _ctrl + " js-line-total", "step": "any", "readonly": "readonly"}),
        }

    def __init__(self, *args, tenant=None, purchase_order=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["product"].queryset = Product.objects.filter(tenant=tenant).order_by("name")
            self.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True).order_by("name")
            po_line_qs = PurchaseOrderLine.objects.filter(purchase_order__tenant=tenant).select_related("purchase_order", "product")
            if purchase_order:
                po_line_qs = po_line_qs.filter(purchase_order=purchase_order)
            self.fields["purchase_order_line"].queryset = po_line_qs.order_by("id")
        else:
            self.fields["product"].queryset = Product.objects.none()
            self.fields["warehouse"].queryset = Warehouse.objects.none()
            self.fields["purchase_order_line"].queryset = PurchaseOrderLine.objects.none()
        self.fields["warehouse"].required = False
        self.fields["purchase_order_line"].required = False
        self.fields["purchase_order_line"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["product"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["product"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_products")
        self.fields["warehouse"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["warehouse"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_warehouses")


GoodsReceiptLineFormSet = inlineformset_factory(
    GoodsReceipt, GoodsReceiptLine, form=GoodsReceiptLineForm, extra=1, can_delete=True
)


class PurchaseReturnForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturn
        fields = ["doc_no", "supplier", "goods_receipt", "return_date", "reason", "notes"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "supplier": forms.Select(attrs={"class": _ctrl}),
            "goods_receipt": forms.Select(attrs={"class": _ctrl}),
            "return_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "reason": forms.TextInput(attrs={"class": _ctrl}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["supplier"].queryset = Supplier.objects.filter(tenant=tenant, is_active=True).order_by("name")
            self.fields["goods_receipt"].queryset = GoodsReceipt.objects.filter(tenant=tenant).order_by("-receipt_date", "-id")
        else:
            self.fields["supplier"].queryset = Supplier.objects.none()
            self.fields["goods_receipt"].queryset = GoodsReceipt.objects.none()
        self.fields["goods_receipt"].required = False
        self.fields["supplier"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["supplier"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_suppliers")
        self.fields["goods_receipt"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class PurchaseReturnLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturnLine
        fields = ["goods_receipt_line", "product", "warehouse", "quantity", "unit_cost", "line_total"]
        widgets = {
            "goods_receipt_line": forms.Select(attrs={"class": _ctrl}),
            "product": forms.Select(attrs={"class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "quantity": forms.NumberInput(attrs={"class": _ctrl + " js-qty", "step": "any"}),
            "unit_cost": forms.NumberInput(attrs={"class": _ctrl + " js-unit-cost", "step": "any"}),
            "line_total": forms.NumberInput(attrs={"class": _ctrl + " js-line-total", "step": "any", "readonly": "readonly"}),
        }

    def __init__(self, *args, tenant=None, goods_receipt=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["product"].queryset = Product.objects.filter(tenant=tenant).order_by("name")
            self.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True).order_by("name")
            grn_line_qs = GoodsReceiptLine.objects.filter(receipt__tenant=tenant).select_related("receipt", "product")
            if goods_receipt:
                grn_line_qs = grn_line_qs.filter(receipt=goods_receipt)
            self.fields["goods_receipt_line"].queryset = grn_line_qs.order_by("id")
        else:
            self.fields["product"].queryset = Product.objects.none()
            self.fields["warehouse"].queryset = Warehouse.objects.none()
            self.fields["goods_receipt_line"].queryset = GoodsReceiptLine.objects.none()
        self.fields["warehouse"].required = False
        self.fields["goods_receipt_line"].required = False
        self.fields["goods_receipt_line"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["product"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["product"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_products")
        self.fields["warehouse"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["warehouse"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_warehouses")


PurchaseReturnLineFormSet = inlineformset_factory(
    PurchaseReturn, PurchaseReturnLine, form=PurchaseReturnLineForm, extra=1, can_delete=True
)

