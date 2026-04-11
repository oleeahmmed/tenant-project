from django import forms
from django.forms import inlineformset_factory
from django.urls import reverse_lazy

from foundation.models import Currency, Customer, PaymentMethod, Supplier

from .models import (
    APInvoice,
    APInvoiceLine,
    APPaymentAllocation,
    APPayment,
    ARInvoice,
    ARInvoiceLine,
    ARReceiptAllocation,
    ARReceipt,
    Account,
    AssetDepreciation,
    BankAccount,
    Budget,
    BudgetLine,
    CashTransaction,
    CostCenter,
    FiscalPeriod,
    FiscalYear,
    FixedAsset,
    JournalEntry,
    JournalLine,
    Project,
)

_ctrl = "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
_chk = {"class": "rounded border-border"}


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["parent", "code", "name", "account_type", "natural_side", "is_postable", "is_active"]
        widgets = {
            "parent": forms.Select(attrs={"class": _ctrl}),
            "code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "account_type": forms.Select(attrs={"class": _ctrl}),
            "natural_side": forms.Select(attrs={"class": _ctrl}),
            "is_postable": forms.CheckboxInput(attrs=_chk),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].required = False
        if tenant:
            qs = Account.objects.filter(tenant=tenant)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            self.fields["parent"].queryset = qs
        self.fields["parent"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class FiscalYearForm(forms.ModelForm):
    class Meta:
        model = FiscalYear
        fields = ["name", "start_date", "end_date", "is_closed"]
        widgets = {"name": forms.TextInput(attrs={"class": _ctrl}), "start_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}), "end_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}), "is_closed": forms.CheckboxInput(attrs=_chk)}


class FiscalPeriodForm(forms.ModelForm):
    class Meta:
        model = FiscalPeriod
        fields = ["fiscal_year", "period_no", "name", "start_date", "end_date", "is_closed"]
        widgets = {
            "fiscal_year": forms.Select(attrs={"class": _ctrl}),
            "period_no": forms.NumberInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "start_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "is_closed": forms.CheckboxInput(attrs=_chk),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["fiscal_year"].queryset = FiscalYear.objects.filter(tenant=tenant)
        self.fields["fiscal_year"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ["entry_no", "posting_date", "fiscal_period", "memo"]
        widgets = {
            "entry_no": forms.TextInput(attrs={"class": _ctrl}),
            "posting_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "fiscal_period": forms.Select(attrs={"class": _ctrl}),
            "memo": forms.TextInput(attrs={"class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fiscal_period"].required = False
        if tenant:
            self.fields["fiscal_period"].queryset = FiscalPeriod.objects.filter(tenant=tenant)
        self.fields["fiscal_period"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class JournalLineForm(forms.ModelForm):
    class Meta:
        model = JournalLine
        fields = ["line_no", "account", "description", "debit", "credit", "cost_center", "project"]
        widgets = {
            "line_no": forms.NumberInput(attrs={"class": _ctrl}),
            "account": forms.Select(attrs={"class": _ctrl}),
            "description": forms.TextInput(attrs={"class": _ctrl}),
            "debit": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "credit": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "cost_center": forms.Select(attrs={"class": _ctrl}),
            "project": forms.Select(attrs={"class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cost_center"].required = False
        self.fields["project"].required = False
        if tenant:
            self.fields["account"].queryset = Account.objects.filter(tenant=tenant, is_active=True)
            self.fields["cost_center"].queryset = CostCenter.objects.filter(tenant=tenant, is_active=True)
            self.fields["project"].queryset = Project.objects.filter(tenant=tenant, is_active=True)
        self.fields["account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["cost_center"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["project"].widget.attrs["class"] = _ctrl + " inv-ts-local"


JournalLineFormSet = inlineformset_factory(
    JournalEntry,
    JournalLine,
    form=JournalLineForm,
    extra=1,
    can_delete=True,
)


class APInvoiceForm(forms.ModelForm):
    class Meta:
        model = APInvoice
        fields = ["doc_no", "supplier", "posting_date", "due_date", "currency", "exchange_rate", "subtotal", "tax_amount", "shipping_charge", "total_amount", "memo", "expense_account", "ap_account", "tax_account"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "supplier": forms.Select(attrs={"class": _ctrl}),
            "posting_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "due_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "currency": forms.Select(attrs={"class": _ctrl}),
            "exchange_rate": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "subtotal": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "tax_amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "shipping_charge": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "total_amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "memo": forms.TextInput(attrs={"class": _ctrl}),
            "expense_account": forms.Select(attrs={"class": _ctrl}),
            "ap_account": forms.Select(attrs={"class": _ctrl}),
            "tax_account": forms.Select(attrs={"class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["currency"].required = False
        self.fields["expense_account"].required = False
        self.fields["ap_account"].required = False
        self.fields["tax_account"].required = False
        if tenant:
            self.fields["supplier"].queryset = Supplier.objects.filter(tenant=tenant, is_active=True)
            self.fields["currency"].queryset = Currency.objects.filter(tenant=tenant, is_active=True)
            acc = Account.objects.filter(tenant=tenant, is_active=True)
            self.fields["expense_account"].queryset = acc
            self.fields["ap_account"].queryset = acc
            self.fields["tax_account"].queryset = acc
        self.fields["supplier"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["supplier"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_suppliers")
        self.fields["currency"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["currency"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_currencies")
        self.fields["expense_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["ap_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["tax_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class APInvoiceLineForm(forms.ModelForm):
    class Meta:
        model = APInvoiceLine
        fields = ["line_no", "description", "quantity", "unit_price", "line_total"]
        widgets = {
            "line_no": forms.NumberInput(attrs={"class": _ctrl}),
            "description": forms.TextInput(attrs={"class": _ctrl}),
            "quantity": forms.NumberInput(attrs={"class": _ctrl + " fin-line-qty", "step": "any"}),
            "unit_price": forms.NumberInput(attrs={"class": _ctrl + " fin-line-unit-price", "step": "any"}),
            "line_total": forms.NumberInput(attrs={"class": _ctrl + " fin-line-total", "step": "any", "readonly": "readonly"}),
        }


APInvoiceLineFormSet = inlineformset_factory(APInvoice, APInvoiceLine, form=APInvoiceLineForm, extra=1, can_delete=True)


class ARInvoiceForm(forms.ModelForm):
    class Meta:
        model = ARInvoice
        fields = ["doc_no", "customer", "posting_date", "due_date", "currency", "exchange_rate", "subtotal", "tax_amount", "shipping_charge", "total_amount", "memo", "revenue_account", "ar_account", "tax_account"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "customer": forms.Select(attrs={"class": _ctrl}),
            "posting_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "due_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "currency": forms.Select(attrs={"class": _ctrl}),
            "exchange_rate": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "subtotal": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "tax_amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "shipping_charge": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "total_amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "memo": forms.TextInput(attrs={"class": _ctrl}),
            "revenue_account": forms.Select(attrs={"class": _ctrl}),
            "ar_account": forms.Select(attrs={"class": _ctrl}),
            "tax_account": forms.Select(attrs={"class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["currency"].required = False
        self.fields["revenue_account"].required = False
        self.fields["ar_account"].required = False
        self.fields["tax_account"].required = False
        if tenant:
            self.fields["customer"].queryset = Customer.objects.filter(tenant=tenant, is_active=True)
            self.fields["currency"].queryset = Currency.objects.filter(tenant=tenant, is_active=True)
            acc = Account.objects.filter(tenant=tenant, is_active=True)
            self.fields["revenue_account"].queryset = acc
            self.fields["ar_account"].queryset = acc
            self.fields["tax_account"].queryset = acc
        self.fields["customer"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["customer"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_customers")
        self.fields["currency"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["currency"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_currencies")
        self.fields["revenue_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["ar_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["tax_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class ARInvoiceLineForm(forms.ModelForm):
    class Meta:
        model = ARInvoiceLine
        fields = ["line_no", "description", "quantity", "unit_price", "line_total"]
        widgets = {
            "line_no": forms.NumberInput(attrs={"class": _ctrl}),
            "description": forms.TextInput(attrs={"class": _ctrl}),
            "quantity": forms.NumberInput(attrs={"class": _ctrl + " fin-line-qty", "step": "any"}),
            "unit_price": forms.NumberInput(attrs={"class": _ctrl + " fin-line-unit-price", "step": "any"}),
            "line_total": forms.NumberInput(attrs={"class": _ctrl + " fin-line-total", "step": "any", "readonly": "readonly"}),
        }


ARInvoiceLineFormSet = inlineformset_factory(ARInvoice, ARInvoiceLine, form=ARInvoiceLineForm, extra=1, can_delete=True)


class APPaymentForm(forms.ModelForm):
    class Meta:
        model = APPayment
        fields = ["doc_no", "supplier", "ap_invoice", "posting_date", "amount", "payment_method", "bank_account", "ap_account", "cash_account"]
        widgets = {f: forms.TextInput(attrs={"class": _ctrl}) for f in ["doc_no"]}
        widgets.update({
            "supplier": forms.Select(attrs={"class": _ctrl}),
            "ap_invoice": forms.Select(attrs={"class": _ctrl}),
            "posting_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "payment_method": forms.Select(attrs={"class": _ctrl}),
            "bank_account": forms.Select(attrs={"class": _ctrl}),
            "ap_account": forms.Select(attrs={"class": _ctrl}),
            "cash_account": forms.Select(attrs={"class": _ctrl}),
        })

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ["payment_method", "bank_account", "ap_account", "cash_account", "ap_invoice"]:
            self.fields[f].required = False
        if tenant:
            self.fields["supplier"].queryset = Supplier.objects.filter(tenant=tenant, is_active=True)
            self.fields["ap_invoice"].queryset = APInvoice.objects.filter(tenant=tenant, status=APInvoice.Status.POSTED).order_by("-posting_date", "-id")
            self.fields["payment_method"].queryset = PaymentMethod.objects.filter(tenant=tenant, is_active=True)
            self.fields["bank_account"].queryset = BankAccount.objects.filter(tenant=tenant, is_active=True)
            acc = Account.objects.filter(tenant=tenant, is_active=True)
            self.fields["ap_account"].queryset = acc
            self.fields["cash_account"].queryset = acc
        self.fields["supplier"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["supplier"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_suppliers")
        self.fields["ap_invoice"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["payment_method"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["payment_method"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_payment_methods")
        self.fields["bank_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["ap_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["cash_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class APPaymentAllocationForm(forms.ModelForm):
    class Meta:
        model = APPaymentAllocation
        fields = ["invoice", "amount"]
        widgets = {
            "invoice": forms.Select(attrs={"class": _ctrl}),
            "amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
        }

    def __init__(self, *args, tenant=None, supplier=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = APInvoice.objects.none()
        if tenant:
            qs = APInvoice.objects.filter(tenant=tenant, status=APInvoice.Status.POSTED).order_by("-posting_date", "-id")
            if supplier:
                qs = qs.filter(supplier=supplier)
        self.fields["invoice"].queryset = qs
        self.fields["invoice"].widget.attrs["class"] = _ctrl + " inv-ts-local"


APPaymentAllocationFormSet = inlineformset_factory(
    APPayment,
    APPaymentAllocation,
    form=APPaymentAllocationForm,
    extra=1,
    can_delete=True,
)


class ARReceiptForm(forms.ModelForm):
    class Meta:
        model = ARReceipt
        fields = ["doc_no", "customer", "ar_invoice", "posting_date", "amount", "payment_method", "bank_account", "ar_account", "cash_account"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "customer": forms.Select(attrs={"class": _ctrl}),
            "ar_invoice": forms.Select(attrs={"class": _ctrl}),
            "posting_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "payment_method": forms.Select(attrs={"class": _ctrl}),
            "bank_account": forms.Select(attrs={"class": _ctrl}),
            "ar_account": forms.Select(attrs={"class": _ctrl}),
            "cash_account": forms.Select(attrs={"class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ["payment_method", "bank_account", "ar_account", "cash_account", "ar_invoice"]:
            self.fields[f].required = False
        if tenant:
            self.fields["customer"].queryset = Customer.objects.filter(tenant=tenant, is_active=True)
            self.fields["ar_invoice"].queryset = ARInvoice.objects.filter(tenant=tenant, status=ARInvoice.Status.POSTED).order_by("-posting_date", "-id")
            self.fields["payment_method"].queryset = PaymentMethod.objects.filter(tenant=tenant, is_active=True)
            self.fields["bank_account"].queryset = BankAccount.objects.filter(tenant=tenant, is_active=True)
            acc = Account.objects.filter(tenant=tenant, is_active=True)
            self.fields["ar_account"].queryset = acc
            self.fields["cash_account"].queryset = acc
        self.fields["customer"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["customer"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_customers")
        self.fields["ar_invoice"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["payment_method"].widget.attrs["class"] = _ctrl + " inv-ts-autocomplete"
        self.fields["payment_method"].widget.attrs["data-autocomplete-url"] = reverse_lazy("foundation_api:autocomplete_payment_methods")
        self.fields["bank_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["ar_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["cash_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class ARReceiptAllocationForm(forms.ModelForm):
    class Meta:
        model = ARReceiptAllocation
        fields = ["invoice", "amount"]
        widgets = {
            "invoice": forms.Select(attrs={"class": _ctrl}),
            "amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
        }

    def __init__(self, *args, tenant=None, customer=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = ARInvoice.objects.none()
        if tenant:
            qs = ARInvoice.objects.filter(tenant=tenant, status=ARInvoice.Status.POSTED).order_by("-posting_date", "-id")
            if customer:
                qs = qs.filter(customer=customer)
        self.fields["invoice"].queryset = qs
        self.fields["invoice"].widget.attrs["class"] = _ctrl + " inv-ts-local"


ARReceiptAllocationFormSet = inlineformset_factory(
    ARReceipt,
    ARReceiptAllocation,
    form=ARReceiptAllocationForm,
    extra=1,
    can_delete=True,
)


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ["code", "name", "account_number", "gl_account", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "account_number": forms.TextInput(attrs={"class": _ctrl}),
            "gl_account": forms.Select(attrs={"class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["gl_account"].queryset = Account.objects.filter(tenant=tenant, is_active=True)
        self.fields["gl_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class CashTransactionForm(forms.ModelForm):
    class Meta:
        model = CashTransaction
        fields = ["doc_no", "posting_date", "direction", "amount", "from_bank_account", "to_bank_account", "counterparty_account", "memo"]
        widgets = {
            "doc_no": forms.TextInput(attrs={"class": _ctrl}),
            "posting_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "direction": forms.Select(attrs={"class": _ctrl}),
            "amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "from_bank_account": forms.Select(attrs={"class": _ctrl}),
            "to_bank_account": forms.Select(attrs={"class": _ctrl}),
            "counterparty_account": forms.Select(attrs={"class": _ctrl}),
            "memo": forms.TextInput(attrs={"class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ["from_bank_account", "to_bank_account", "counterparty_account"]:
            self.fields[f].required = False
        if tenant:
            self.fields["from_bank_account"].queryset = BankAccount.objects.filter(tenant=tenant, is_active=True)
            self.fields["to_bank_account"].queryset = BankAccount.objects.filter(tenant=tenant, is_active=True)
            self.fields["counterparty_account"].queryset = Account.objects.filter(tenant=tenant, is_active=True)
        self.fields["from_bank_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["to_bank_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["counterparty_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class FixedAssetForm(forms.ModelForm):
    class Meta:
        model = FixedAsset
        fields = ["code", "name", "capitalization_date", "cost", "salvage_value", "useful_life_months", "depreciation_method", "asset_account", "accumulated_depreciation_account", "depreciation_expense_account", "status"]
        widgets = {
            "code": forms.TextInput(attrs={"class": _ctrl}),
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "capitalization_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "cost": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "salvage_value": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "useful_life_months": forms.NumberInput(attrs={"class": _ctrl}),
            "depreciation_method": forms.Select(attrs={"class": _ctrl}),
            "asset_account": forms.Select(attrs={"class": _ctrl}),
            "accumulated_depreciation_account": forms.Select(attrs={"class": _ctrl}),
            "depreciation_expense_account": forms.Select(attrs={"class": _ctrl}),
            "status": forms.Select(attrs={"class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            acc = Account.objects.filter(tenant=tenant, is_active=True)
            self.fields["asset_account"].queryset = acc
            self.fields["accumulated_depreciation_account"].queryset = acc
            self.fields["depreciation_expense_account"].queryset = acc
        self.fields["asset_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["accumulated_depreciation_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["depreciation_expense_account"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class AssetDepreciationForm(forms.ModelForm):
    class Meta:
        model = AssetDepreciation
        fields = ["asset", "period", "posting_date", "amount"]
        widgets = {
            "asset": forms.Select(attrs={"class": _ctrl}),
            "period": forms.Select(attrs={"class": _ctrl}),
            "posting_date": forms.DateInput(attrs={"class": _ctrl, "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["period"].required = False
        if tenant:
            self.fields["asset"].queryset = FixedAsset.objects.filter(tenant=tenant)
            self.fields["period"].queryset = FiscalPeriod.objects.filter(tenant=tenant)
        self.fields["asset"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["period"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ["name", "fiscal_year", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "fiscal_year": forms.Select(attrs={"class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs=_chk),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["fiscal_year"].queryset = FiscalYear.objects.filter(tenant=tenant)
        self.fields["fiscal_year"].widget.attrs["class"] = _ctrl + " inv-ts-local"


class BudgetLineForm(forms.ModelForm):
    class Meta:
        model = BudgetLine
        fields = ["fiscal_period", "account", "cost_center", "amount"]
        widgets = {
            "fiscal_period": forms.Select(attrs={"class": _ctrl}),
            "account": forms.Select(attrs={"class": _ctrl}),
            "cost_center": forms.Select(attrs={"class": _ctrl}),
            "amount": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cost_center"].required = False
        if tenant:
            self.fields["fiscal_period"].queryset = FiscalPeriod.objects.filter(tenant=tenant)
            self.fields["account"].queryset = Account.objects.filter(tenant=tenant, is_active=True)
            self.fields["cost_center"].queryset = CostCenter.objects.filter(tenant=tenant, is_active=True)
        self.fields["fiscal_period"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["account"].widget.attrs["class"] = _ctrl + " inv-ts-local"
        self.fields["cost_center"].widget.attrs["class"] = _ctrl + " inv-ts-local"


BudgetLineFormSet = inlineformset_factory(Budget, BudgetLine, form=BudgetLineForm, extra=1, can_delete=True)

