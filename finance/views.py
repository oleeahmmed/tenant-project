from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import (
    APInvoiceForm,
    APInvoiceLineFormSet,
    APPaymentForm,
    ARInvoiceForm,
    ARInvoiceLineFormSet,
    ARReceiptForm,
    AccountForm,
    AssetDepreciationForm,
    BankAccountForm,
    BudgetForm,
    BudgetLineFormSet,
    CashTransactionForm,
    FiscalPeriodForm,
    FiscalYearForm,
    FixedAssetForm,
    JournalEntryForm,
    JournalLineFormSet,
)
from .mixins import FinanceAdminMixin, FinanceDashboardAccessMixin, FinancePageContextMixin
from .models import (
    APInvoice,
    APPayment,
    ARInvoice,
    ARReceipt,
    Account,
    AssetDepreciation,
    BankAccount,
    Budget,
    CashTransaction,
    FiscalPeriod,
    FiscalYear,
    FixedAsset,
    JournalEntry,
    LedgerEntry,
)
from .services.posting import (
    post_ap_invoice,
    post_ap_payment,
    post_ar_invoice,
    post_ar_receipt,
    post_asset_depreciation,
    post_cash_transaction,
    post_journal_entry,
    reverse_journal_entry,
)
from .services.reports import balance_sheet, budget_vs_actual, general_ledger, profit_and_loss, trial_balance


class FinanceDashboardView(FinanceDashboardAccessMixin, FinancePageContextMixin, TemplateView):
    template_name = "finance/dashboard.html"
    page_title = "Finance"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        ctx["accounts_n"] = Account.objects.filter(tenant=tenant).count()
        ctx["journals_n"] = JournalEntry.objects.filter(tenant=tenant).count()
        ctx["ledger_n"] = LedgerEntry.objects.filter(tenant=tenant).count()
        ctx["ap_open_n"] = APInvoice.objects.filter(tenant=tenant, status=APInvoice.Status.POSTED).count()
        ctx["ar_open_n"] = ARInvoice.objects.filter(tenant=tenant, status=ARInvoice.Status.POSTED).count()
        return ctx


class FinanceGuideView(FinanceAdminMixin, FinancePageContextMixin, TemplateView):
    template_name = "finance/finance_guide_bn.html"
    page_title = "Finance guide (Bangla)"


class AccountListView(FinanceAdminMixin, FinancePageContextMixin, ListView):
    model = Account
    template_name = "finance/entity_list.html"
    context_object_name = "object_list"
    page_title = "Chart of accounts"

    def get_queryset(self):
        return Account.objects.filter(tenant=self.request.hrm_tenant).select_related("parent").order_by("code")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({"entity_title": "Chart of accounts", "create_url_name": "finance:account_create", "edit_url_name": "finance:account_edit", "delete_url_name": "finance:account_delete", "list_url_name": "finance:account_list"})
        return ctx


class AccountCreateView(FinanceAdminMixin, FinancePageContextMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = "finance/entity_form.html"
    success_url = reverse_lazy("finance:account_list")
    page_title = "Add account"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "finance:account_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Account created.")
        return redirect(self.success_url)


class AccountUpdateView(FinanceAdminMixin, FinancePageContextMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "finance/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("finance:account_list")
    page_title = "Edit account"

    def get_queryset(self):
        return Account.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "finance:account_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Account updated.")
        return super().form_valid(form)


class AccountDeleteView(FinanceAdminMixin, FinancePageContextMixin, DeleteView):
    model = Account
    template_name = "finance/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("finance:account_list")
    page_title = "Delete account"

    def get_queryset(self):
        return Account.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "finance:account_list"
        return ctx


class FiscalYearListView(FinanceAdminMixin, FinancePageContextMixin, ListView):
    model = FiscalYear
    template_name = "finance/entity_list.html"
    context_object_name = "object_list"
    page_title = "Fiscal years"

    def get_queryset(self):
        return FiscalYear.objects.filter(tenant=self.request.hrm_tenant).order_by("-start_date")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({"entity_title": "Fiscal years", "create_url_name": "finance:fiscal_year_create", "edit_url_name": "finance:fiscal_year_edit", "delete_url_name": "finance:fiscal_year_delete", "list_url_name": "finance:fiscal_year_list"})
        return ctx


class FiscalYearCreateView(FinanceAdminMixin, FinancePageContextMixin, CreateView):
    model = FiscalYear
    form_class = FiscalYearForm
    template_name = "finance/entity_form.html"
    success_url = reverse_lazy("finance:fiscal_year_list")
    page_title = "Add fiscal year"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "finance:fiscal_year_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Fiscal year created.")
        return redirect(self.success_url)


class FiscalYearUpdateView(FinanceAdminMixin, FinancePageContextMixin, UpdateView):
    model = FiscalYear
    form_class = FiscalYearForm
    template_name = "finance/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("finance:fiscal_year_list")
    page_title = "Edit fiscal year"

    def get_queryset(self):
        return FiscalYear.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "finance:fiscal_year_list"
        return ctx


class FiscalYearDeleteView(FinanceAdminMixin, FinancePageContextMixin, DeleteView):
    model = FiscalYear
    template_name = "finance/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("finance:fiscal_year_list")
    page_title = "Delete fiscal year"

    def get_queryset(self):
        return FiscalYear.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "finance:fiscal_year_list"
        return ctx


class FiscalPeriodListView(FinanceAdminMixin, FinancePageContextMixin, ListView):
    model = FiscalPeriod
    template_name = "finance/entity_list.html"
    context_object_name = "object_list"
    page_title = "Fiscal periods"

    def get_queryset(self):
        return FiscalPeriod.objects.filter(tenant=self.request.hrm_tenant).select_related("fiscal_year").order_by("-start_date")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({"entity_title": "Fiscal periods", "create_url_name": "finance:fiscal_period_create", "edit_url_name": "finance:fiscal_period_edit", "delete_url_name": "finance:fiscal_period_delete", "list_url_name": "finance:fiscal_period_list"})
        return ctx


class FiscalPeriodCreateView(FinanceAdminMixin, FinancePageContextMixin, CreateView):
    model = FiscalPeriod
    form_class = FiscalPeriodForm
    template_name = "finance/entity_form.html"
    success_url = reverse_lazy("finance:fiscal_period_list")
    page_title = "Add fiscal period"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "finance:fiscal_period_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Fiscal period created.")
        return redirect(self.success_url)


class FiscalPeriodUpdateView(FinanceAdminMixin, FinancePageContextMixin, UpdateView):
    model = FiscalPeriod
    form_class = FiscalPeriodForm
    template_name = "finance/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("finance:fiscal_period_list")
    page_title = "Edit fiscal period"

    def get_queryset(self):
        return FiscalPeriod.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "finance:fiscal_period_list"
        return ctx


class FiscalPeriodDeleteView(FinanceAdminMixin, FinancePageContextMixin, DeleteView):
    model = FiscalPeriod
    template_name = "finance/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("finance:fiscal_period_list")
    page_title = "Delete fiscal period"

    def get_queryset(self):
        return FiscalPeriod.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "finance:fiscal_period_list"
        return ctx


class JournalEntryListView(FinanceAdminMixin, FinancePageContextMixin, ListView):
    model = JournalEntry
    template_name = "finance/journal_list.html"
    context_object_name = "journals"
    page_title = "Journal entries"

    def get_queryset(self):
        return JournalEntry.objects.filter(tenant=self.request.hrm_tenant).select_related("fiscal_period").order_by("-posting_date", "-id")


class JournalEntryCreateView(FinanceAdminMixin, FinancePageContextMixin, View):
    page_title = "Add journal entry"

    def get(self, request):
        form = JournalEntryForm(tenant=request.hrm_tenant)
        formset = JournalLineFormSet(prefix="lines")
        for f in formset.forms:
            f.fields["account"].queryset = Account.objects.filter(tenant=request.hrm_tenant, is_active=True)
        return render(request, "finance/journal_form.html", {"form": form, "formset": formset, "is_edit": False, "active_page": "finance", "page_title": self.page_title})

    def post(self, request):
        form = JournalEntryForm(request.POST, tenant=request.hrm_tenant)
        formset = JournalLineFormSet(request.POST, prefix="lines")
        for f in formset.forms:
            f.fields["account"].queryset = Account.objects.filter(tenant=request.hrm_tenant, is_active=True)
        if form.is_valid() and formset.is_valid():
            journal = form.save(commit=False)
            journal.tenant = request.hrm_tenant
            journal.save()
            formset.instance = journal
            lines = formset.save(commit=False)
            for line in lines:
                line.tenant = request.hrm_tenant
                line.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, "Journal entry saved in draft.")
            return redirect("finance:journal_detail", pk=journal.pk)
        return render(request, "finance/journal_form.html", {"form": form, "formset": formset, "is_edit": False, "active_page": "finance", "page_title": self.page_title})


class JournalEntryUpdateView(FinanceAdminMixin, FinancePageContextMixin, View):
    page_title = "Edit journal entry"

    def get_object(self, request, pk):
        return get_object_or_404(JournalEntry, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        journal = self.get_object(request, pk)
        if journal.status != JournalEntry.Status.DRAFT:
            messages.error(request, "Only draft journals can be edited.")
            return redirect("finance:journal_detail", pk=journal.pk)
        form = JournalEntryForm(instance=journal, tenant=request.hrm_tenant)
        formset = JournalLineFormSet(instance=journal, prefix="lines")
        for f in formset.forms:
            f.fields["account"].queryset = Account.objects.filter(tenant=request.hrm_tenant, is_active=True)
        return render(request, "finance/journal_form.html", {"form": form, "formset": formset, "object": journal, "is_edit": True, "active_page": "finance", "page_title": self.page_title})

    def post(self, request, pk):
        journal = self.get_object(request, pk)
        if journal.status != JournalEntry.Status.DRAFT:
            messages.error(request, "Only draft journals can be edited.")
            return redirect("finance:journal_detail", pk=journal.pk)
        form = JournalEntryForm(request.POST, instance=journal, tenant=request.hrm_tenant)
        formset = JournalLineFormSet(request.POST, instance=journal, prefix="lines")
        for f in formset.forms:
            f.fields["account"].queryset = Account.objects.filter(tenant=request.hrm_tenant, is_active=True)
        if form.is_valid() and formset.is_valid():
            form.save()
            lines = formset.save(commit=False)
            for line in lines:
                line.tenant = request.hrm_tenant
                line.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, "Draft journal updated.")
            return redirect("finance:journal_detail", pk=journal.pk)
        return render(request, "finance/journal_form.html", {"form": form, "formset": formset, "object": journal, "is_edit": True, "active_page": "finance", "page_title": self.page_title})


class JournalEntryDetailView(FinanceAdminMixin, FinancePageContextMixin, DetailView):
    model = JournalEntry
    template_name = "finance/journal_detail.html"
    context_object_name = "journal"
    page_title = "Journal details"

    def get_queryset(self):
        return JournalEntry.objects.filter(tenant=self.request.hrm_tenant).prefetch_related("lines__account")


class JournalEntryPostView(FinanceAdminMixin, View):
    def post(self, request, pk):
        journal = get_object_or_404(JournalEntry, pk=pk, tenant=request.hrm_tenant)
        try:
            post_journal_entry(journal=journal, posted_by=request.user)
            messages.success(request, "Journal posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:journal_detail", pk=pk)


class JournalEntryReverseView(FinanceAdminMixin, View):
    def post(self, request, pk):
        journal = get_object_or_404(JournalEntry, pk=pk, tenant=request.hrm_tenant)
        try:
            reversal = reverse_journal_entry(journal=journal, posted_by=request.user)
            messages.success(request, f"Journal reversed ({reversal.entry_no}).")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:journal_detail", pk=pk)


def _simple_list_view(model_cls, template, context_name, page_title):
    _page_title = page_title

    class _V(FinanceAdminMixin, FinancePageContextMixin, ListView):
        model = model_cls
        template_name = template
        context_object_name = context_name
        page_title = _page_title

        def get_queryset(self):
            return model_cls.objects.filter(tenant=self.request.hrm_tenant).order_by("-id")

    return _V


class APInvoiceListView(_simple_list_view(APInvoice, "finance/document_list.html", "object_list", "AP invoices")):
    pass


class ARInvoiceListView(_simple_list_view(ARInvoice, "finance/document_list.html", "object_list", "AR invoices")):
    pass


class APPaymentListView(_simple_list_view(APPayment, "finance/document_list.html", "object_list", "AP payments")):
    pass


class ARReceiptListView(_simple_list_view(ARReceipt, "finance/document_list.html", "object_list", "AR receipts")):
    pass


class BankAccountListView(_simple_list_view(BankAccount, "finance/document_list.html", "object_list", "Bank accounts")):
    pass


class CashTransactionListView(_simple_list_view(CashTransaction, "finance/document_list.html", "object_list", "Cash transactions")):
    pass


class FixedAssetListView(_simple_list_view(FixedAsset, "finance/document_list.html", "object_list", "Fixed assets")):
    pass


class AssetDepreciationListView(_simple_list_view(AssetDepreciation, "finance/document_list.html", "object_list", "Asset depreciation")):
    pass


class BudgetListView(_simple_list_view(Budget, "finance/document_list.html", "object_list", "Budgets")):
    pass


def _render_document_form(request, *, form, formset=None, title, action_url, list_url):
    return render(
        request,
        "finance/document_form.html",
        {
            "form": form,
            "formset": formset,
            "page_title": title,
            "active_page": "finance",
            "action_url": action_url,
            "list_url": list_url,
        },
    )


class APInvoiceCreateView(FinanceAdminMixin, View):
    def get(self, request):
        form = APInvoiceForm(tenant=request.hrm_tenant)
        formset = APInvoiceLineFormSet(prefix="lines")
        return _render_document_form(request, form=form, formset=formset, title="Add AP invoice", action_url=reverse_lazy("finance:ap_invoice_create"), list_url=reverse_lazy("finance:ap_invoice_list"))

    def post(self, request):
        form = APInvoiceForm(request.POST, tenant=request.hrm_tenant)
        formset = APInvoiceLineFormSet(request.POST, prefix="lines")
        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.hrm_tenant
            obj.save()
            formset.instance = obj
            lines = formset.save(commit=False)
            for line in lines:
                line.tenant = request.hrm_tenant
                line.save()
            messages.success(request, "AP invoice created.")
            return redirect("finance:ap_invoice_list")
        return _render_document_form(request, form=form, formset=formset, title="Add AP invoice", action_url=reverse_lazy("finance:ap_invoice_create"), list_url=reverse_lazy("finance:ap_invoice_list"))


class APInvoicePostView(FinanceAdminMixin, View):
    def post(self, request, pk):
        doc = get_object_or_404(APInvoice, pk=pk, tenant=request.hrm_tenant)
        try:
            post_ap_invoice(invoice=doc, posted_by=request.user)
            messages.success(request, "AP invoice posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:ap_invoice_list")


class ARInvoiceCreateView(FinanceAdminMixin, View):
    def get(self, request):
        form = ARInvoiceForm(tenant=request.hrm_tenant)
        formset = ARInvoiceLineFormSet(prefix="lines")
        return _render_document_form(request, form=form, formset=formset, title="Add AR invoice", action_url=reverse_lazy("finance:ar_invoice_create"), list_url=reverse_lazy("finance:ar_invoice_list"))

    def post(self, request):
        form = ARInvoiceForm(request.POST, tenant=request.hrm_tenant)
        formset = ARInvoiceLineFormSet(request.POST, prefix="lines")
        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.hrm_tenant
            obj.save()
            formset.instance = obj
            lines = formset.save(commit=False)
            for line in lines:
                line.tenant = request.hrm_tenant
                line.save()
            messages.success(request, "AR invoice created.")
            return redirect("finance:ar_invoice_list")
        return _render_document_form(request, form=form, formset=formset, title="Add AR invoice", action_url=reverse_lazy("finance:ar_invoice_create"), list_url=reverse_lazy("finance:ar_invoice_list"))


class ARInvoicePostView(FinanceAdminMixin, View):
    def post(self, request, pk):
        doc = get_object_or_404(ARInvoice, pk=pk, tenant=request.hrm_tenant)
        try:
            post_ar_invoice(invoice=doc, posted_by=request.user)
            messages.success(request, "AR invoice posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:ar_invoice_list")


class APPaymentCreateView(FinanceAdminMixin, CreateView):
    model = APPayment
    form_class = APPaymentForm
    template_name = "finance/document_form_single.html"
    success_url = reverse_lazy("finance:ap_payment_list")
    page_title = "Add AP payment"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "AP payment created.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "finance:ap_payment_list"
        return ctx


class APPaymentPostView(FinanceAdminMixin, View):
    def post(self, request, pk):
        doc = get_object_or_404(APPayment, pk=pk, tenant=request.hrm_tenant)
        try:
            post_ap_payment(payment=doc, posted_by=request.user)
            messages.success(request, "AP payment posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:ap_payment_list")


class ARReceiptCreateView(FinanceAdminMixin, CreateView):
    model = ARReceipt
    form_class = ARReceiptForm
    template_name = "finance/document_form_single.html"
    success_url = reverse_lazy("finance:ar_receipt_list")
    page_title = "Add AR receipt"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "AR receipt created.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "finance:ar_receipt_list"
        return ctx


class ARReceiptPostView(FinanceAdminMixin, View):
    def post(self, request, pk):
        doc = get_object_or_404(ARReceipt, pk=pk, tenant=request.hrm_tenant)
        try:
            post_ar_receipt(receipt=doc, posted_by=request.user)
            messages.success(request, "AR receipt posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:ar_receipt_list")


class BankAccountCreateView(FinanceAdminMixin, CreateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = "finance/document_form_single.html"
    success_url = reverse_lazy("finance:bank_account_list")
    page_title = "Add bank account"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Bank account created.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "finance:bank_account_list"
        return ctx


class CashTransactionCreateView(FinanceAdminMixin, CreateView):
    model = CashTransaction
    form_class = CashTransactionForm
    template_name = "finance/document_form_single.html"
    success_url = reverse_lazy("finance:cash_transaction_list")
    page_title = "Add cash transaction"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Cash transaction created.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "finance:cash_transaction_list"
        return ctx


class CashTransactionPostView(FinanceAdminMixin, View):
    def post(self, request, pk):
        doc = get_object_or_404(CashTransaction, pk=pk, tenant=request.hrm_tenant)
        try:
            post_cash_transaction(txn=doc, posted_by=request.user)
            messages.success(request, "Cash transaction posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:cash_transaction_list")


class FixedAssetCreateView(FinanceAdminMixin, CreateView):
    model = FixedAsset
    form_class = FixedAssetForm
    template_name = "finance/document_form_single.html"
    success_url = reverse_lazy("finance:fixed_asset_list")
    page_title = "Add fixed asset"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Fixed asset created.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "finance:fixed_asset_list"
        return ctx


class AssetDepreciationCreateView(FinanceAdminMixin, CreateView):
    model = AssetDepreciation
    form_class = AssetDepreciationForm
    template_name = "finance/document_form_single.html"
    success_url = reverse_lazy("finance:asset_depreciation_list")
    page_title = "Add depreciation run"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Depreciation row created.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "finance:asset_depreciation_list"
        return ctx


class AssetDepreciationPostView(FinanceAdminMixin, View):
    def post(self, request, pk):
        doc = get_object_or_404(AssetDepreciation, pk=pk, tenant=request.hrm_tenant)
        try:
            post_asset_depreciation(dep=doc, posted_by=request.user)
            messages.success(request, "Depreciation posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:asset_depreciation_list")


class BudgetCreateView(FinanceAdminMixin, View):
    def get(self, request):
        form = BudgetForm(tenant=request.hrm_tenant)
        formset = BudgetLineFormSet(prefix="lines")
        return _render_document_form(request, form=form, formset=formset, title="Add budget", action_url=reverse_lazy("finance:budget_create"), list_url=reverse_lazy("finance:budget_list"))

    def post(self, request):
        form = BudgetForm(request.POST, tenant=request.hrm_tenant)
        formset = BudgetLineFormSet(request.POST, prefix="lines")
        if form.is_valid() and formset.is_valid():
            budget = form.save(commit=False)
            budget.tenant = request.hrm_tenant
            budget.save()
            formset.instance = budget
            lines = formset.save(commit=False)
            for line in lines:
                line.tenant = request.hrm_tenant
                line.save()
            messages.success(request, "Budget created.")
            return redirect("finance:budget_list")
        return _render_document_form(request, form=form, formset=formset, title="Add budget", action_url=reverse_lazy("finance:budget_create"), list_url=reverse_lazy("finance:budget_list"))


class GeneralLedgerReportView(FinanceAdminMixin, FinancePageContextMixin, TemplateView):
    template_name = "finance/report_gl.html"
    page_title = "General Ledger"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        account_id = self.request.GET.get("account_id")
        date_from = self.request.GET.get("date_from") or None
        date_to = self.request.GET.get("date_to") or None
        ctx["rows"] = general_ledger(tenant=tenant, date_from=date_from, date_to=date_to, account_id=int(account_id) if account_id and account_id.isdigit() else None)
        ctx["accounts"] = Account.objects.filter(tenant=tenant, is_active=True).order_by("code")
        ctx["filter_account_id"] = account_id or ""
        ctx["filter_date_from"] = date_from or ""
        ctx["filter_date_to"] = date_to or ""
        return ctx


class TrialBalanceReportView(FinanceAdminMixin, FinancePageContextMixin, TemplateView):
    template_name = "finance/report_trial_balance.html"
    page_title = "Trial Balance"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        date_to = self.request.GET.get("date_to") or None
        rows, td, tc = trial_balance(tenant=self.request.hrm_tenant, date_to=date_to)
        ctx["rows"] = rows
        ctx["total_debit"] = td
        ctx["total_credit"] = tc
        ctx["filter_date_to"] = date_to or ""
        return ctx


class ProfitLossReportView(FinanceAdminMixin, FinancePageContextMixin, TemplateView):
    template_name = "finance/report_profit_loss.html"
    page_title = "Profit & Loss"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        date_from = self.request.GET.get("date_from") or None
        date_to = self.request.GET.get("date_to") or None
        income, expense, total_income, total_expense, net_profit = profit_and_loss(tenant=self.request.hrm_tenant, date_from=date_from, date_to=date_to)
        ctx["income_rows"] = income
        ctx["expense_rows"] = expense
        ctx["total_income"] = total_income
        ctx["total_expense"] = total_expense
        ctx["net_profit"] = net_profit
        ctx["filter_date_from"] = date_from or ""
        ctx["filter_date_to"] = date_to or ""
        return ctx


class BalanceSheetReportView(FinanceAdminMixin, FinancePageContextMixin, TemplateView):
    template_name = "finance/report_balance_sheet.html"
    page_title = "Balance Sheet"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        date_to = self.request.GET.get("date_to") or None
        assets, liabilities, equity, ta, tl, te = balance_sheet(tenant=self.request.hrm_tenant, date_to=date_to)
        ctx["asset_rows"] = assets
        ctx["liability_rows"] = liabilities
        ctx["equity_rows"] = equity
        ctx["total_assets"] = ta
        ctx["total_liabilities"] = tl
        ctx["total_equity"] = te
        ctx["filter_date_to"] = date_to or ""
        return ctx


class BudgetVsActualReportView(FinanceAdminMixin, FinancePageContextMixin, TemplateView):
    template_name = "finance/report_budget_vs_actual.html"
    page_title = "Budget vs Actual"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        budget_id = self.request.GET.get("budget_id")
        budget = None
        rows = []
        if budget_id and budget_id.isdigit():
            budget, rows = budget_vs_actual(tenant=self.request.hrm_tenant, budget_id=int(budget_id))
        ctx["budget"] = budget
        ctx["rows"] = rows
        ctx["budgets"] = Budget.objects.filter(tenant=self.request.hrm_tenant).order_by("-id")
        ctx["filter_budget_id"] = budget_id or ""
        return ctx

