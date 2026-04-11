from django import forms
from django.forms import inlineformset_factory
from django.urls import reverse_lazy

from foundation.models import Customer, Product, Warehouse

from .models import (
    DeliveryNote,
    DeliveryNoteLine,
    SalesOrder,
    SalesOrderLine,
    SalesQuotation,
    SalesQuotationLine,
    SalesReturn,
    SalesReturnLine,
)

_ctrl = (
    "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-ring"
)


class SalesQuotationForm(forms.ModelForm):
    class Meta:
        model = SalesQuotation
        fields = ["doc_no", "customer", "quote_date", "valid_until", "tax_amount", "notes"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "customer": forms.Select(attrs={"class": _ctrl}),
            "quote_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "valid_until": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "tax_amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.filter(tenant=tenant, is_active=True).order_by("name") if tenant else Customer.objects.none()
        self.fields["customer"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["customer"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_customers")


class SalesQuotationLineForm(forms.ModelForm):
    class Meta:
        model = SalesQuotationLine
        fields = ["product", "warehouse", "description", "quantity", "unit_price", "line_total"]
        widgets = {
            "product": forms.Select(attrs={"class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "description": forms.TextInput(attrs={"class": _ctrl}),
            "quantity": forms.NumberInput(attrs={"class": _ctrl + " js-qty", "step": "any"}),
            "unit_price": forms.NumberInput(attrs={"class": _ctrl + " js-unit-cost", "step": "any"}),
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


SalesQuotationLineFormSet = inlineformset_factory(
    SalesQuotation, SalesQuotationLine, form=SalesQuotationLineForm, extra=1, can_delete=True
)


class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ["doc_no", "customer", "quotation", "order_date", "expected_delivery", "tax_amount", "notes"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "customer": forms.Select(attrs={"class": _ctrl}),
            "quotation": forms.Select(attrs={"class": _ctrl}),
            "order_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "expected_delivery": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "tax_amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["customer"].queryset = Customer.objects.filter(tenant=tenant, is_active=True).order_by("name")
            self.fields["quotation"].queryset = SalesQuotation.objects.filter(tenant=tenant).order_by("-quote_date", "-id")
        else:
            self.fields["customer"].queryset = Customer.objects.none()
            self.fields["quotation"].queryset = SalesQuotation.objects.none()
        self.fields["quotation"].required = False
        self.fields["customer"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["customer"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_customers")
        self.fields["quotation"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class SalesOrderLineForm(forms.ModelForm):
    class Meta:
        model = SalesOrderLine
        fields = ["product", "warehouse", "description", "quantity", "unit_price", "line_total"]
        widgets = {
            "product": forms.Select(attrs={"class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "description": forms.TextInput(attrs={"class": _ctrl}),
            "quantity": forms.NumberInput(attrs={"class": _ctrl + " js-qty", "step": "any"}),
            "unit_price": forms.NumberInput(attrs={"class": _ctrl + " js-unit-cost", "step": "any"}),
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


SalesOrderLineFormSet = inlineformset_factory(
    SalesOrder, SalesOrderLine, form=SalesOrderLineForm, extra=1, can_delete=True
)


class DeliveryNoteForm(forms.ModelForm):
    class Meta:
        model = DeliveryNote
        fields = ["doc_no", "order", "customer", "delivery_date", "notes"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "order": forms.Select(attrs={"class": _ctrl}),
            "customer": forms.Select(attrs={"class": _ctrl}),
            "delivery_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["order"].queryset = SalesOrder.objects.filter(tenant=tenant).order_by("-order_date", "-id")
            self.fields["customer"].queryset = Customer.objects.filter(tenant=tenant, is_active=True).order_by("name")
        else:
            self.fields["order"].queryset = SalesOrder.objects.none()
            self.fields["customer"].queryset = Customer.objects.none()
        self.fields["order"].required = False
        self.fields["customer"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["customer"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_customers")
        self.fields["order"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class DeliveryNoteLineForm(forms.ModelForm):
    class Meta:
        model = DeliveryNoteLine
        fields = ["order_line", "product", "warehouse", "quantity_delivered", "unit_price", "line_total"]
        widgets = {
            "order_line": forms.Select(attrs={"class": _ctrl}),
            "product": forms.Select(attrs={"class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "quantity_delivered": forms.NumberInput(attrs={"class": _ctrl + " js-qty", "step": "any"}),
            "unit_price": forms.NumberInput(attrs={"class": _ctrl + " js-unit-cost", "step": "any"}),
            "line_total": forms.NumberInput(attrs={"class": _ctrl + " js-line-total", "step": "any", "readonly": "readonly"}),
        }

    def __init__(self, *args, tenant=None, order=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["product"].queryset = Product.objects.filter(tenant=tenant).order_by("name")
            self.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True).order_by("name")
            qs = SalesOrderLine.objects.filter(order__tenant=tenant)
            if order:
                qs = qs.filter(order=order)
            self.fields["order_line"].queryset = qs.order_by("id")
        else:
            self.fields["product"].queryset = Product.objects.none()
            self.fields["warehouse"].queryset = Warehouse.objects.none()
            self.fields["order_line"].queryset = SalesOrderLine.objects.none()
        self.fields["warehouse"].required = False
        self.fields["order_line"].required = False
        self.fields["order_line"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["product"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["product"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_products")
        self.fields["warehouse"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["warehouse"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_warehouses")


DeliveryNoteLineFormSet = inlineformset_factory(
    DeliveryNote, DeliveryNoteLine, form=DeliveryNoteLineForm, extra=1, can_delete=True
)


class SalesReturnForm(forms.ModelForm):
    class Meta:
        model = SalesReturn
        fields = ["doc_no", "customer", "delivery", "return_date", "reason", "notes"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "customer": forms.Select(attrs={"class": _ctrl}),
            "delivery": forms.Select(attrs={"class": _ctrl}),
            "return_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "reason": forms.TextInput(attrs={"class": _ctrl}),
            "notes": forms.Textarea(attrs={"class": _ctrl, "rows": 3}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["customer"].queryset = Customer.objects.filter(tenant=tenant, is_active=True).order_by("name")
            self.fields["delivery"].queryset = DeliveryNote.objects.filter(tenant=tenant).order_by("-delivery_date", "-id")
        else:
            self.fields["customer"].queryset = Customer.objects.none()
            self.fields["delivery"].queryset = DeliveryNote.objects.none()
        self.fields["delivery"].required = False
        self.fields["customer"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["customer"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_customers")
        self.fields["delivery"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class SalesReturnLineForm(forms.ModelForm):
    class Meta:
        model = SalesReturnLine
        fields = ["delivery_line", "product", "warehouse", "quantity", "unit_price", "line_total"]
        widgets = {
            "delivery_line": forms.Select(attrs={"class": _ctrl}),
            "product": forms.Select(attrs={"class": _ctrl}),
            "warehouse": forms.Select(attrs={"class": _ctrl}),
            "quantity": forms.NumberInput(attrs={"class": _ctrl + " js-qty", "step": "any"}),
            "unit_price": forms.NumberInput(attrs={"class": _ctrl + " js-unit-cost", "step": "any"}),
            "line_total": forms.NumberInput(attrs={"class": _ctrl + " js-line-total", "step": "any", "readonly": "readonly"}),
        }

    def __init__(self, *args, tenant=None, delivery=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["product"].queryset = Product.objects.filter(tenant=tenant).order_by("name")
            self.fields["warehouse"].queryset = Warehouse.objects.filter(tenant=tenant, is_active=True).order_by("name")
            qs = DeliveryNoteLine.objects.filter(delivery__tenant=tenant)
            if delivery:
                qs = qs.filter(delivery=delivery)
            self.fields["delivery_line"].queryset = qs.order_by("id")
        else:
            self.fields["product"].queryset = Product.objects.none()
            self.fields["warehouse"].queryset = Warehouse.objects.none()
            self.fields["delivery_line"].queryset = DeliveryNoteLine.objects.none()
        self.fields["warehouse"].required = False
        self.fields["delivery_line"].required = False
        self.fields["delivery_line"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["product"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["product"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_products")
        self.fields["warehouse"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["warehouse"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_warehouses")


SalesReturnLineFormSet = inlineformset_factory(
    SalesReturn, SalesReturnLine, form=SalesReturnLineForm, extra=1, can_delete=True
)

