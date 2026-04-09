from django import forms

from .models import (
    Category,
    Currency,
    Customer,
    ExchangeRate,
    PaymentMethod,
    PaymentTerm,
    Product,
    SalesPerson,
    Supplier,
    TaxRate,
    TaxType,
    UnitOfMeasure,
    UomConversion,
    Warehouse,
)

_ctrl = "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
_chk = {"class": "rounded border-border"}


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = [
            "code",
            "name",
            "description",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "is_active",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": _ctrl, "placeholder": "e.g. WH-01"}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "description": forms.Textarea(attrs={"rows": 2, "class": _ctrl}),
            "address_line1": forms.TextInput(attrs={"class": _ctrl}),
            "address_line2": forms.TextInput(attrs={"class": _ctrl}),
            "city": forms.TextInput(attrs={"class": _ctrl}),
            "state": forms.TextInput(attrs={"class": _ctrl}),
            "postal_code": forms.TextInput(attrs={"class": _ctrl}),
            "country": forms.TextInput(attrs={"class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["parent", "code", "name", "description", "is_active"]
        widgets = {
            "parent": forms.Select(attrs={"class": _ctrl}),
            "code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "description": forms.Textarea(attrs={"rows": 2, "class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            qs = Category.objects.filter(tenant=tenant)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            self.fields["parent"].queryset = qs
            self.fields["parent"].required = False


class UnitOfMeasureForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = ["code", "name", "decimal_places", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "decimal_places": forms.NumberInput(attrs={"class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "sku",
            "name",
            "description",
            "category",
            "default_uom",
            "default_unit_cost",
            "list_price",
            "is_active",
        ]
        widgets = {
            "sku": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "description": forms.Textarea(attrs={"rows": 2, "class": _ctrl}),
            "category": forms.Select(attrs={"class": _ctrl}),
            "default_uom": forms.Select(attrs={"class": _ctrl}),
            "default_unit_cost": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "list_price": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["category"].queryset = Category.objects.filter(tenant=tenant)
            self.fields["default_uom"].queryset = UnitOfMeasure.objects.filter(tenant=tenant)
            self.fields["category"].required = False
            self.fields["default_uom"].required = False


class UomConversionForm(forms.ModelForm):
    class Meta:
        model = UomConversion
        fields = ["from_uom", "to_uom", "factor"]
        widgets = {
            "from_uom": forms.Select(attrs={"class": _ctrl}),
            "to_uom": forms.Select(attrs={"class": _ctrl}),
            "factor": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["from_uom"].queryset = UnitOfMeasure.objects.filter(tenant=tenant)
            self.fields["to_uom"].queryset = UnitOfMeasure.objects.filter(tenant=tenant)


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "customer_code",
            "name",
            "email",
            "phone",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "is_active",
        ]
        widgets = {
            "customer_code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "email": forms.EmailInput(attrs={"class": _ctrl}),
            "phone": forms.TextInput(attrs={"class": _ctrl}),
            "address_line1": forms.TextInput(attrs={"class": _ctrl}),
            "address_line2": forms.TextInput(attrs={"class": _ctrl}),
            "city": forms.TextInput(attrs={"class": _ctrl}),
            "state": forms.TextInput(attrs={"class": _ctrl}),
            "postal_code": forms.TextInput(attrs={"class": _ctrl}),
            "country": forms.TextInput(attrs={"class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            "supplier_code",
            "name",
            "email",
            "phone",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "is_active",
        ]
        widgets = {
            "supplier_code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "email": forms.EmailInput(attrs={"class": _ctrl}),
            "phone": forms.TextInput(attrs={"class": _ctrl}),
            "address_line1": forms.TextInput(attrs={"class": _ctrl}),
            "address_line2": forms.TextInput(attrs={"class": _ctrl}),
            "city": forms.TextInput(attrs={"class": _ctrl}),
            "state": forms.TextInput(attrs={"class": _ctrl}),
            "postal_code": forms.TextInput(attrs={"class": _ctrl}),
            "country": forms.TextInput(attrs={"class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }


class SalesPersonForm(forms.ModelForm):
    class Meta:
        model = SalesPerson
        fields = ["code", "name", "email", "phone", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "email": forms.EmailInput(attrs={"class": _ctrl}),
            "phone": forms.TextInput(attrs={"class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ["code", "name", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }


class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ["code", "name", "symbol", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "symbol": forms.TextInput(attrs={"class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }


class ExchangeRateForm(forms.ModelForm):
    class Meta:
        model = ExchangeRate
        fields = ["from_currency", "to_currency", "rate", "effective_date"]
        widgets = {
            "from_currency": forms.Select(attrs={"class": _ctrl}),
            "to_currency": forms.Select(attrs={"class": _ctrl}),
            "rate": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "effective_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            cq = Currency.objects.filter(tenant=tenant)
            self.fields["from_currency"].queryset = cq
            self.fields["to_currency"].queryset = cq


class TaxTypeForm(forms.ModelForm):
    class Meta:
        model = TaxType
        fields = ["code", "name", "description", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "description": forms.Textarea(attrs={"rows": 2, "class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }


class TaxRateForm(forms.ModelForm):
    class Meta:
        model = TaxRate
        fields = ["tax_type", "rate_percent", "effective_from"]
        widgets = {
            "tax_type": forms.Select(attrs={"class": _ctrl}),
            "rate_percent": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "effective_from": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["tax_type"].queryset = TaxType.objects.filter(tenant=tenant)


class PaymentTermForm(forms.ModelForm):
    class Meta:
        model = PaymentTerm
        fields = ["code", "name", "days_until_due", "description", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "days_until_due": forms.NumberInput(attrs={"class": _ctrl}),
            "description": forms.Textarea(attrs={"rows": 2, "class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }
