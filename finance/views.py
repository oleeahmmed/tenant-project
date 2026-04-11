from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from foundation.models import Customer, Supplier

from .forms import (
    APInvoiceForm,
    APInvoiceLineFormSet,
    APPaymentAllocationFormSet,
    APPaymentForm,
    ARInvoiceForm,
    ARInvoiceLineFormSet,
    ARReceiptAllocationFormSet,
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
from .mixins import (
    FinanceAdminMixin,
    FinanceDashboardAccessMixin,
    FinanceMasterListMixin,
    FinancePageContextMixin,
    FinancePermissionRequiredMixin,
)
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
    cancel_ap_invoice,
    cancel_ap_payment,
    cancel_ar_invoice,
    cancel_ar_receipt,
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


class FinanceEntityListView(
    FinanceAdminMixin,
    FinancePageContextMixin,
    FinanceMasterListMixin,
    ListView,
):
    """Foundation-style master list: filters, search, pagination, row ⋮ menu, print."""

    template_name = "finance/entity_list.html"
    context_object_name = "object_list"
    entity_subtitle = "Search, filter, and manage records"
    column_specs = []
    search_fields = []
    sort_allowlist = []
    default_sort = "name"
    sort_choices = []
    has_is_active = True
    detail_url_name = None
    create_url_name = ""
    list_url_name = ""
    edit_url_name = ""
    delete_url_name = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["entity_title"] = getattr(self, "entity_title", self.page_title)
        ctx["entity_subtitle"] = getattr(self, "entity_subtitle", "Search, filter, and manage records")
        ctx["create_url_name"] = self.create_url_name
        ctx["list_url_name"] = self.list_url_name
        ctx["edit_url_name"] = self.edit_url_name
        ctx["delete_url_name"] = self.delete_url_name
        ctx["column_specs"] = self.column_specs
        ctx["has_is_active"] = getattr(self, "has_is_active", True)
        ctx["new_button_label"] = getattr(self, "new_button_label", "Add")
        if getattr(self, "detail_url_name", None):
            ctx["detail_url_name"] = self.detail_url_name
        return ctx


class AccountListView(FinanceEntityListView):
    model = Account
    page_title = "Chart of accounts"
    entity_title = "Chart of accounts"
    entity_subtitle = "Accounts, types, and posting flags"
    create_url_name = "finance:account_create"
    list_url_name = "finance:account_list"
    edit_url_name = "finance:account_edit"
    delete_url_name = "finance:account_delete"
    new_button_label = "Add account"
    search_fields = ["code", "name"]
    sort_allowlist = ["code", "-code", "name", "-name", "account_type", "-account_type"]
    default_sort = "code"
    sort_choices = [
        ("code", "Code A–Z"),
        ("-code", "Code Z–A"),
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
        ("account_type", "Type A–Z"),
        ("-account_type", "Type Z–A"),
    ]
    column_specs = [
        {"field": "code", "label": "Code", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "account_type", "label": "Type"},
        {"field": "natural_side", "label": "Side"},
        {"field": "is_postable", "label": "Postable", "bool": True},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = Account.objects.filter(tenant=self.request.hrm_tenant).select_related("parent")
        return self.apply_master_filters(qs)


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


class FiscalYearListView(FinanceEntityListView):
    model = FiscalYear
    page_title = "Fiscal years"
    entity_title = "Fiscal years"
    entity_subtitle = "Fiscal year boundaries and close status"
    create_url_name = "finance:fiscal_year_create"
    list_url_name = "finance:fiscal_year_list"
    edit_url_name = "finance:fiscal_year_edit"
    delete_url_name = "finance:fiscal_year_delete"
    new_button_label = "Add fiscal year"
    has_is_active = False
    search_fields = ["name"]
    sort_allowlist = ["name", "-name", "start_date", "-start_date", "end_date", "-end_date"]
    default_sort = "-start_date"
    sort_choices = [
        ("-start_date", "Start date (newest)"),
        ("start_date", "Start date (oldest)"),
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
    ]
    column_specs = [
        {"field": "name", "label": "Name"},
        {"field": "start_date", "label": "Start"},
        {"field": "end_date", "label": "End"},
        {"field": "is_closed", "label": "Closed", "bool": True},
    ]

    def get_queryset(self):
        qs = FiscalYear.objects.filter(tenant=self.request.hrm_tenant)
        return self.apply_master_filters(qs)


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


class FiscalPeriodListView(FinanceEntityListView):
    model = FiscalPeriod
    page_title = "Fiscal periods"
    entity_title = "Fiscal periods"
    entity_subtitle = "Accounting periods within fiscal years"
    create_url_name = "finance:fiscal_period_create"
    list_url_name = "finance:fiscal_period_list"
    edit_url_name = "finance:fiscal_period_edit"
    delete_url_name = "finance:fiscal_period_delete"
    new_button_label = "Add fiscal period"
    has_is_active = False
    search_fields = ["name", "fiscal_year__name"]
    sort_allowlist = ["start_date", "-start_date", "period_no", "-period_no", "name", "-name"]
    default_sort = "-start_date"
    sort_choices = [
        ("-start_date", "Start date (newest)"),
        ("start_date", "Start date (oldest)"),
        ("period_no", "Period no. (asc)"),
        ("-period_no", "Period no. (desc)"),
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
    ]
    column_specs = [
        {"field": "fiscal_year__name", "label": "Fiscal year"},
        {"field": "period_no", "label": "No."},
        {"field": "name", "label": "Period"},
        {"field": "start_date", "label": "Start"},
        {"field": "end_date", "label": "End"},
        {"field": "is_closed", "label": "Closed", "bool": True},
    ]

    def get_queryset(self):
        qs = FiscalPeriod.objects.filter(tenant=self.request.hrm_tenant).select_related("fiscal_year")
        return self.apply_master_filters(qs)


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
    paginate_by = 15

    def get_queryset(self):
        qs = JournalEntry.objects.filter(tenant=self.request.hrm_tenant).select_related("fiscal_period")
        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        ordering = (self.request.GET.get("sort") or "-posting_date").strip()
        if q:
            qs = qs.filter(Q(entry_no__icontains=q) | Q(memo__icontains=q))
        if status:
            qs = qs.filter(status=status)
        allowed = {
            "-posting_date": "-posting_date",
            "posting_date": "posting_date",
            "entry_no": "entry_no",
            "-entry_no": "-entry_no",
            "-id": "-id",
            "id": "id",
        }
        return qs.order_by(allowed.get(ordering, "-posting_date"), "-id")

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
        ctx["status_choices"] = JournalEntry.Status.choices
        ctx["selected"] = {
            "q": self.request.GET.get("q", ""),
            "status": self.request.GET.get("status", ""),
            "sort": self.request.GET.get("sort", "-posting_date"),
            "page_size": self.request.GET.get("page_size", str(self.paginate_by)),
        }
        return ctx


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


class JournalEntryPostView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.journal.post"
    def post(self, request, pk):
        journal = get_object_or_404(JournalEntry, pk=pk, tenant=request.hrm_tenant)
        try:
            post_journal_entry(journal=journal, posted_by=request.user)
            messages.success(request, "Journal posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:journal_detail", pk=pk)


class JournalEntryReverseView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.journal.reverse"
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
        paginate_by = 20

        def get_queryset(self):
            qs = model_cls.objects.filter(tenant=self.request.hrm_tenant)
            q = (self.request.GET.get("q") or "").strip()
            status = (self.request.GET.get("status") or "").strip()
            party = (self.request.GET.get("party") or "").strip()
            ordering = (self.request.GET.get("sort") or "-id").strip()

            if hasattr(model_cls, "supplier"):
                qs = qs.select_related("supplier")
            if hasattr(model_cls, "customer"):
                qs = qs.select_related("customer")

            if q:
                filters = Q()
                for fld in ("doc_no", "memo", "code", "name"):
                    if hasattr(model_cls, fld):
                        filters |= Q(**{f"{fld}__icontains": q})
                if filters:
                    qs = qs.filter(filters)
            if status and hasattr(model_cls, "status"):
                qs = qs.filter(status=status)
            if party.isdigit():
                if hasattr(model_cls, "supplier"):
                    qs = qs.filter(supplier_id=int(party))
                elif hasattr(model_cls, "customer"):
                    qs = qs.filter(customer_id=int(party))

            allowed = {"id", "-id"}
            for f in ("posting_date", "created_at"):
                if hasattr(model_cls, f):
                    allowed.update({f, f"-{f}"})
            if ordering not in allowed:
                ordering = "-id"
            return qs.order_by(ordering, "-id")

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
            party = (self.request.GET.get("party") or "").strip()
            party_url = ""
            party_label = ""
            filtered_party = None
            if hasattr(model_cls, "supplier"):
                party_url = "/api/foundation/autocomplete/suppliers/"
                party_label = "Supplier"
                if party.isdigit():
                    filtered_party = Supplier.objects.filter(
                        tenant=self.request.hrm_tenant, pk=int(party)
                    ).only("id", "supplier_code", "name").first()
            elif hasattr(model_cls, "customer"):
                party_url = "/api/foundation/autocomplete/customers/"
                party_label = "Customer"
                if party.isdigit():
                    filtered_party = Customer.objects.filter(
                        tenant=self.request.hrm_tenant, pk=int(party)
                    ).only("id", "customer_code", "name").first()
            ctx.update(
                {
                    "qs_no_page": params.urlencode(),
                    "selected": {
                        "q": self.request.GET.get("q", ""),
                        "status": self.request.GET.get("status", ""),
                        "party": party,
                        "sort": self.request.GET.get("sort", "-id"),
                        "page_size": self.request.GET.get("page_size", str(self.paginate_by)),
                    },
                    "status_choices": getattr(model_cls, "Status", None).choices if hasattr(model_cls, "Status") else [],
                    "party_autocomplete_url": party_url,
                    "party_label": party_label,
                    "filtered_party": filtered_party,
                }
            )
            return ctx

    return _V


class APInvoiceListView(_simple_list_view(APInvoice, "finance/document_list.html", "object_list", "AP invoices")):
    pass


class APInvoiceDetailView(FinanceAdminMixin, FinancePageContextMixin, DetailView):
    model = APInvoice
    template_name = "finance/document_detail.html"
    context_object_name = "object"
    page_title = "AP invoice details"

    def get_queryset(self):
        return APInvoice.objects.filter(tenant=self.request.hrm_tenant).select_related("supplier", "journal_entry")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url"] = reverse_lazy("finance:ap_invoice_list")
        return ctx


class ARInvoiceListView(_simple_list_view(ARInvoice, "finance/document_list.html", "object_list", "AR invoices")):
    pass


class ARInvoiceDetailView(FinanceAdminMixin, FinancePageContextMixin, DetailView):
    model = ARInvoice
    template_name = "finance/document_detail.html"
    context_object_name = "object"
    page_title = "AR invoice details"

    def get_queryset(self):
        return ARInvoice.objects.filter(tenant=self.request.hrm_tenant).select_related("customer", "journal_entry")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url"] = reverse_lazy("finance:ar_invoice_list")
        return ctx


class APPaymentListView(_simple_list_view(APPayment, "finance/document_list.html", "object_list", "AP payments")):
    pass


class APPaymentDetailView(FinanceAdminMixin, FinancePageContextMixin, DetailView):
    model = APPayment
    template_name = "finance/document_detail.html"
    context_object_name = "object"
    page_title = "AP payment details"

    def get_queryset(self):
        return APPayment.objects.filter(tenant=self.request.hrm_tenant).select_related("supplier", "journal_entry")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url"] = reverse_lazy("finance:ap_payment_list")
        return ctx


class ARReceiptListView(_simple_list_view(ARReceipt, "finance/document_list.html", "object_list", "AR receipts")):
    pass


class ARReceiptDetailView(FinanceAdminMixin, FinancePageContextMixin, DetailView):
    model = ARReceipt
    template_name = "finance/document_detail.html"
    context_object_name = "object"
    page_title = "AR receipt details"

    def get_queryset(self):
        return ARReceipt.objects.filter(tenant=self.request.hrm_tenant).select_related("customer", "journal_entry")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url"] = reverse_lazy("finance:ar_receipt_list")
        return ctx


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


class APInvoiceUpdateView(FinanceAdminMixin, View):
    def get_object(self, request, pk):
        return get_object_or_404(APInvoice, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        if obj.status != APInvoice.Status.DRAFT:
            messages.error(request, "Only draft AP invoices can be edited.")
            return redirect("finance:ap_invoice_list")
        form = APInvoiceForm(instance=obj, tenant=request.hrm_tenant)
        formset = APInvoiceLineFormSet(instance=obj, prefix="lines")
        return _render_document_form(request, form=form, formset=formset, title="Edit AP invoice", action_url=reverse_lazy("finance:ap_invoice_edit", kwargs={"pk": obj.pk}), list_url=reverse_lazy("finance:ap_invoice_list"))

    def post(self, request, pk):
        obj = self.get_object(request, pk)
        if obj.status != APInvoice.Status.DRAFT:
            messages.error(request, "Only draft AP invoices can be edited.")
            return redirect("finance:ap_invoice_list")
        form = APInvoiceForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = APInvoiceLineFormSet(request.POST, instance=obj, prefix="lines")
        if form.is_valid() and formset.is_valid():
            form.save()
            lines = formset.save(commit=False)
            for line in lines:
                line.tenant = request.hrm_tenant
                line.save()
            for deleted in formset.deleted_objects:
                deleted.delete()
            messages.success(request, "AP invoice updated.")
            return redirect("finance:ap_invoice_list")
        return _render_document_form(request, form=form, formset=formset, title="Edit AP invoice", action_url=reverse_lazy("finance:ap_invoice_edit", kwargs={"pk": obj.pk}), list_url=reverse_lazy("finance:ap_invoice_list"))


class APInvoiceDeleteView(FinanceAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(APInvoice, pk=pk, tenant=request.hrm_tenant)
        if obj.status != APInvoice.Status.DRAFT:
            messages.error(request, "Only draft AP invoices can be deleted.")
            return redirect("finance:ap_invoice_list")
        obj.delete()
        messages.success(request, "AP invoice deleted.")
        return redirect("finance:ap_invoice_list")


class APInvoicePostView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.ap.post"
    def post(self, request, pk):
        doc = get_object_or_404(APInvoice, pk=pk, tenant=request.hrm_tenant)
        try:
            post_ap_invoice(invoice=doc, posted_by=request.user)
            messages.success(request, "AP invoice posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:ap_invoice_list")


class APInvoiceCancelView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.ap.post"

    def post(self, request, pk):
        doc = get_object_or_404(APInvoice, pk=pk, tenant=request.hrm_tenant)
        try:
            cancel_ap_invoice(invoice=doc, posted_by=request.user)
            messages.success(request, "AP invoice cancelled.")
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


class ARInvoiceUpdateView(FinanceAdminMixin, View):
    def get_object(self, request, pk):
        return get_object_or_404(ARInvoice, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        if obj.status != ARInvoice.Status.DRAFT:
            messages.error(request, "Only draft AR invoices can be edited.")
            return redirect("finance:ar_invoice_list")
        form = ARInvoiceForm(instance=obj, tenant=request.hrm_tenant)
        formset = ARInvoiceLineFormSet(instance=obj, prefix="lines")
        return _render_document_form(request, form=form, formset=formset, title="Edit AR invoice", action_url=reverse_lazy("finance:ar_invoice_edit", kwargs={"pk": obj.pk}), list_url=reverse_lazy("finance:ar_invoice_list"))

    def post(self, request, pk):
        obj = self.get_object(request, pk)
        if obj.status != ARInvoice.Status.DRAFT:
            messages.error(request, "Only draft AR invoices can be edited.")
            return redirect("finance:ar_invoice_list")
        form = ARInvoiceForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = ARInvoiceLineFormSet(request.POST, instance=obj, prefix="lines")
        if form.is_valid() and formset.is_valid():
            form.save()
            lines = formset.save(commit=False)
            for line in lines:
                line.tenant = request.hrm_tenant
                line.save()
            for deleted in formset.deleted_objects:
                deleted.delete()
            messages.success(request, "AR invoice updated.")
            return redirect("finance:ar_invoice_list")
        return _render_document_form(request, form=form, formset=formset, title="Edit AR invoice", action_url=reverse_lazy("finance:ar_invoice_edit", kwargs={"pk": obj.pk}), list_url=reverse_lazy("finance:ar_invoice_list"))


class ARInvoiceDeleteView(FinanceAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(ARInvoice, pk=pk, tenant=request.hrm_tenant)
        if obj.status != ARInvoice.Status.DRAFT:
            messages.error(request, "Only draft AR invoices can be deleted.")
            return redirect("finance:ar_invoice_list")
        obj.delete()
        messages.success(request, "AR invoice deleted.")
        return redirect("finance:ar_invoice_list")


class ARInvoicePostView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.ar.post"
    def post(self, request, pk):
        doc = get_object_or_404(ARInvoice, pk=pk, tenant=request.hrm_tenant)
        try:
            post_ar_invoice(invoice=doc, posted_by=request.user)
            messages.success(request, "AR invoice posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:ar_invoice_list")


class ARInvoiceCancelView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.ar.post"

    def post(self, request, pk):
        doc = get_object_or_404(ARInvoice, pk=pk, tenant=request.hrm_tenant)
        try:
            cancel_ar_invoice(invoice=doc, posted_by=request.user)
            messages.success(request, "AR invoice cancelled.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:ar_invoice_list")


class APPaymentCreateView(FinanceAdminMixin, View):
    def get(self, request):
        form = APPaymentForm(tenant=request.hrm_tenant)
        formset = APPaymentAllocationFormSet(prefix="alloc")
        for f in formset.forms:
            f.fields["invoice"].queryset = APInvoice.objects.filter(tenant=request.hrm_tenant, status=APInvoice.Status.POSTED).order_by("-posting_date", "-id")
        return _render_document_form(request, form=form, formset=formset, title="Add AP payment", action_url=reverse_lazy("finance:ap_payment_create"), list_url=reverse_lazy("finance:ap_payment_list"))

    def post(self, request):
        form = APPaymentForm(request.POST, tenant=request.hrm_tenant)
        formset = APPaymentAllocationFormSet(request.POST, prefix="alloc")
        supplier = None
        if form.is_valid():
            supplier = form.cleaned_data.get("supplier")
        for f in formset.forms:
            f.fields["invoice"].queryset = APInvoice.objects.filter(tenant=request.hrm_tenant, status=APInvoice.Status.POSTED, supplier=supplier).order_by("-posting_date", "-id") if supplier else APInvoice.objects.filter(tenant=request.hrm_tenant, status=APInvoice.Status.POSTED).order_by("-posting_date", "-id")
        if form.is_valid() and formset.is_valid():
            self.object = form.save(commit=False)
            self.object.tenant = request.hrm_tenant
            self.object.save()
            formset.instance = self.object
            rows = formset.save(commit=False)
            for row in rows:
                row.tenant = request.hrm_tenant
                row.save()
            for deleted in formset.deleted_objects:
                deleted.delete()
            messages.success(request, "AP payment created.")
            return redirect("finance:ap_payment_list")
        return _render_document_form(request, form=form, formset=formset, title="Add AP payment", action_url=reverse_lazy("finance:ap_payment_create"), list_url=reverse_lazy("finance:ap_payment_list"))


class APPaymentUpdateView(FinanceAdminMixin, View):
    def get_object(self, request, pk):
        return get_object_or_404(APPayment, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        if obj.status != APPayment.Status.DRAFT:
            messages.error(request, "Only draft AP payments can be edited.")
            return redirect("finance:ap_payment_list")
        form = APPaymentForm(instance=obj, tenant=request.hrm_tenant)
        formset = APPaymentAllocationFormSet(instance=obj, prefix="alloc")
        for f in formset.forms:
            f.fields["invoice"].queryset = APInvoice.objects.filter(tenant=request.hrm_tenant, status=APInvoice.Status.POSTED, supplier=obj.supplier).order_by("-posting_date", "-id")
        return _render_document_form(request, form=form, formset=formset, title="Edit AP payment", action_url=reverse_lazy("finance:ap_payment_edit", kwargs={"pk": obj.pk}), list_url=reverse_lazy("finance:ap_payment_list"))

    def post(self, request, pk):
        obj = self.get_object(request, pk)
        if obj.status != APPayment.Status.DRAFT:
            messages.error(request, "Only draft AP payments can be edited.")
            return redirect("finance:ap_payment_list")
        form = APPaymentForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = APPaymentAllocationFormSet(request.POST, instance=obj, prefix="alloc")
        supplier = None
        if form.is_valid():
            supplier = form.cleaned_data.get("supplier")
        for f in formset.forms:
            f.fields["invoice"].queryset = APInvoice.objects.filter(tenant=request.hrm_tenant, status=APInvoice.Status.POSTED, supplier=supplier).order_by("-posting_date", "-id") if supplier else APInvoice.objects.filter(tenant=request.hrm_tenant, status=APInvoice.Status.POSTED).order_by("-posting_date", "-id")
        if form.is_valid() and formset.is_valid():
            form.save()
            rows = formset.save(commit=False)
            for row in rows:
                row.tenant = request.hrm_tenant
                row.save()
            for deleted in formset.deleted_objects:
                deleted.delete()
            messages.success(request, "AP payment updated.")
            return redirect("finance:ap_payment_list")
        return _render_document_form(request, form=form, formset=formset, title="Edit AP payment", action_url=reverse_lazy("finance:ap_payment_edit", kwargs={"pk": obj.pk}), list_url=reverse_lazy("finance:ap_payment_list"))


class APPaymentDeleteView(FinanceAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(APPayment, pk=pk, tenant=request.hrm_tenant)
        if obj.status != APPayment.Status.DRAFT:
            messages.error(request, "Only draft AP payments can be deleted.")
            return redirect("finance:ap_payment_list")
        obj.delete()
        messages.success(request, "AP payment deleted.")
        return redirect("finance:ap_payment_list")


class APPaymentPostView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.ap.post"
    def post(self, request, pk):
        doc = get_object_or_404(APPayment, pk=pk, tenant=request.hrm_tenant)
        try:
            post_ap_payment(payment=doc, posted_by=request.user)
            messages.success(request, "AP payment posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:ap_payment_list")


class APPaymentCancelView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.ap.post"

    def post(self, request, pk):
        doc = get_object_or_404(APPayment, pk=pk, tenant=request.hrm_tenant)
        try:
            cancel_ap_payment(payment=doc, posted_by=request.user)
            messages.success(request, "AP payment cancelled.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:ap_payment_list")


class ARReceiptCreateView(FinanceAdminMixin, View):
    def get(self, request):
        form = ARReceiptForm(tenant=request.hrm_tenant)
        formset = ARReceiptAllocationFormSet(prefix="alloc")
        for f in formset.forms:
            f.fields["invoice"].queryset = ARInvoice.objects.filter(tenant=request.hrm_tenant, status=ARInvoice.Status.POSTED).order_by("-posting_date", "-id")
        return _render_document_form(request, form=form, formset=formset, title="Add AR receipt", action_url=reverse_lazy("finance:ar_receipt_create"), list_url=reverse_lazy("finance:ar_receipt_list"))

    def post(self, request):
        form = ARReceiptForm(request.POST, tenant=request.hrm_tenant)
        formset = ARReceiptAllocationFormSet(request.POST, prefix="alloc")
        customer = None
        if form.is_valid():
            customer = form.cleaned_data.get("customer")
        for f in formset.forms:
            f.fields["invoice"].queryset = ARInvoice.objects.filter(tenant=request.hrm_tenant, status=ARInvoice.Status.POSTED, customer=customer).order_by("-posting_date", "-id") if customer else ARInvoice.objects.filter(tenant=request.hrm_tenant, status=ARInvoice.Status.POSTED).order_by("-posting_date", "-id")
        if form.is_valid() and formset.is_valid():
            self.object = form.save(commit=False)
            self.object.tenant = request.hrm_tenant
            self.object.save()
            formset.instance = self.object
            rows = formset.save(commit=False)
            for row in rows:
                row.tenant = request.hrm_tenant
                row.save()
            for deleted in formset.deleted_objects:
                deleted.delete()
            messages.success(request, "AR receipt created.")
            return redirect("finance:ar_receipt_list")
        return _render_document_form(request, form=form, formset=formset, title="Add AR receipt", action_url=reverse_lazy("finance:ar_receipt_create"), list_url=reverse_lazy("finance:ar_receipt_list"))


class ARReceiptUpdateView(FinanceAdminMixin, View):
    def get_object(self, request, pk):
        return get_object_or_404(ARReceipt, pk=pk, tenant=request.hrm_tenant)

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        if obj.status != ARReceipt.Status.DRAFT:
            messages.error(request, "Only draft AR receipts can be edited.")
            return redirect("finance:ar_receipt_list")
        form = ARReceiptForm(instance=obj, tenant=request.hrm_tenant)
        formset = ARReceiptAllocationFormSet(instance=obj, prefix="alloc")
        for f in formset.forms:
            f.fields["invoice"].queryset = ARInvoice.objects.filter(tenant=request.hrm_tenant, status=ARInvoice.Status.POSTED, customer=obj.customer).order_by("-posting_date", "-id")
        return _render_document_form(request, form=form, formset=formset, title="Edit AR receipt", action_url=reverse_lazy("finance:ar_receipt_edit", kwargs={"pk": obj.pk}), list_url=reverse_lazy("finance:ar_receipt_list"))

    def post(self, request, pk):
        obj = self.get_object(request, pk)
        if obj.status != ARReceipt.Status.DRAFT:
            messages.error(request, "Only draft AR receipts can be edited.")
            return redirect("finance:ar_receipt_list")
        form = ARReceiptForm(request.POST, instance=obj, tenant=request.hrm_tenant)
        formset = ARReceiptAllocationFormSet(request.POST, instance=obj, prefix="alloc")
        customer = None
        if form.is_valid():
            customer = form.cleaned_data.get("customer")
        for f in formset.forms:
            f.fields["invoice"].queryset = ARInvoice.objects.filter(tenant=request.hrm_tenant, status=ARInvoice.Status.POSTED, customer=customer).order_by("-posting_date", "-id") if customer else ARInvoice.objects.filter(tenant=request.hrm_tenant, status=ARInvoice.Status.POSTED).order_by("-posting_date", "-id")
        if form.is_valid() and formset.is_valid():
            form.save()
            rows = formset.save(commit=False)
            for row in rows:
                row.tenant = request.hrm_tenant
                row.save()
            for deleted in formset.deleted_objects:
                deleted.delete()
            messages.success(request, "AR receipt updated.")
            return redirect("finance:ar_receipt_list")
        return _render_document_form(request, form=form, formset=formset, title="Edit AR receipt", action_url=reverse_lazy("finance:ar_receipt_edit", kwargs={"pk": obj.pk}), list_url=reverse_lazy("finance:ar_receipt_list"))


class ARReceiptDeleteView(FinanceAdminMixin, View):
    def post(self, request, pk):
        obj = get_object_or_404(ARReceipt, pk=pk, tenant=request.hrm_tenant)
        if obj.status != ARReceipt.Status.DRAFT:
            messages.error(request, "Only draft AR receipts can be deleted.")
            return redirect("finance:ar_receipt_list")
        obj.delete()
        messages.success(request, "AR receipt deleted.")
        return redirect("finance:ar_receipt_list")


class ARReceiptPostView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.ar.post"
    def post(self, request, pk):
        doc = get_object_or_404(ARReceipt, pk=pk, tenant=request.hrm_tenant)
        try:
            post_ar_receipt(receipt=doc, posted_by=request.user)
            messages.success(request, "AR receipt posted.")
        except ValidationError as exc:
            messages.error(request, str(exc))
        return redirect("finance:ar_receipt_list")


class ARReceiptCancelView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.ar.post"

    def post(self, request, pk):
        doc = get_object_or_404(ARReceipt, pk=pk, tenant=request.hrm_tenant)
        try:
            cancel_ar_receipt(receipt=doc, posted_by=request.user)
            messages.success(request, "AR receipt cancelled.")
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


class CashTransactionPostView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.cash.post"
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


class AssetDepreciationPostView(FinancePermissionRequiredMixin, FinanceAdminMixin, View):
    permission_codename = "finance.asset.post"
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


class GeneralLedgerReportView(FinancePermissionRequiredMixin, FinanceAdminMixin, FinancePageContextMixin, TemplateView):
    permission_codename = "finance.report.view"
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


class TrialBalanceReportView(FinancePermissionRequiredMixin, FinanceAdminMixin, FinancePageContextMixin, TemplateView):
    permission_codename = "finance.report.view"
    template_name = "finance/report_trial_balance.html"
    page_title = "Trial Balance"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        date_to = self.request.GET.get("date_to") or None
        account_id = self.request.GET.get("account_id") or ""
        rows, td, tc = trial_balance(tenant=tenant, date_to=date_to)
        if account_id.isdigit():
            rows = rows.filter(account_id=int(account_id))
            td = sum((r.get("total_debit") or 0 for r in rows), 0)
            tc = sum((r.get("total_credit") or 0 for r in rows), 0)
        ctx["rows"] = rows
        ctx["total_debit"] = td
        ctx["total_credit"] = tc
        ctx["accounts"] = Account.objects.filter(tenant=tenant, is_active=True).order_by("code")
        ctx["filter_account_id"] = account_id
        ctx["filter_date_to"] = date_to or ""
        return ctx


class ProfitLossReportView(FinancePermissionRequiredMixin, FinanceAdminMixin, FinancePageContextMixin, TemplateView):
    permission_codename = "finance.report.view"
    template_name = "finance/report_profit_loss.html"
    page_title = "Profit & Loss"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        date_from = self.request.GET.get("date_from") or None
        date_to = self.request.GET.get("date_to") or None
        account_id = self.request.GET.get("account_id") or ""
        income, expense, total_income, total_expense, net_profit = profit_and_loss(tenant=tenant, date_from=date_from, date_to=date_to)
        if account_id.isdigit():
            aid = int(account_id)
            income = [r for r in income if r.get("account_id") == aid]
            expense = [r for r in expense if r.get("account_id") == aid]
            total_income = sum((r.get("amount") or 0 for r in income), 0)
            total_expense = sum((r.get("amount") or 0 for r in expense), 0)
            net_profit = total_income - total_expense
        ctx["income_rows"] = income
        ctx["expense_rows"] = expense
        ctx["total_income"] = total_income
        ctx["total_expense"] = total_expense
        ctx["net_profit"] = net_profit
        ctx["accounts"] = Account.objects.filter(
            tenant=tenant,
            is_active=True,
            account_type__in=[Account.AccountType.INCOME, Account.AccountType.EXPENSE],
        ).order_by("code")
        ctx["filter_account_id"] = account_id
        ctx["filter_date_from"] = date_from or ""
        ctx["filter_date_to"] = date_to or ""
        return ctx


class BalanceSheetReportView(FinancePermissionRequiredMixin, FinanceAdminMixin, FinancePageContextMixin, TemplateView):
    permission_codename = "finance.report.view"
    template_name = "finance/report_balance_sheet.html"
    page_title = "Balance Sheet"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        date_to = self.request.GET.get("date_to") or None
        account_id = self.request.GET.get("account_id") or ""
        assets, liabilities, equity, ta, tl, te = balance_sheet(tenant=tenant, date_to=date_to)
        if account_id.isdigit():
            aid = int(account_id)
            assets = [r for r in assets if r.get("account_id") == aid]
            liabilities = [r for r in liabilities if r.get("account_id") == aid]
            equity = [r for r in equity if r.get("account_id") == aid]
            ta = sum((r.get("amount") or 0 for r in assets), 0)
            tl = sum((r.get("amount") or 0 for r in liabilities), 0)
            te = sum((r.get("amount") or 0 for r in equity), 0)
        ctx["asset_rows"] = assets
        ctx["liability_rows"] = liabilities
        ctx["equity_rows"] = equity
        ctx["total_assets"] = ta
        ctx["total_liabilities"] = tl
        ctx["total_equity"] = te
        ctx["accounts"] = Account.objects.filter(
            tenant=tenant,
            is_active=True,
            account_type__in=[
                Account.AccountType.ASSET,
                Account.AccountType.LIABILITY,
                Account.AccountType.EQUITY,
            ],
        ).order_by("code")
        ctx["filter_account_id"] = account_id
        ctx["filter_date_to"] = date_to or ""
        return ctx


class BudgetVsActualReportView(FinancePermissionRequiredMixin, FinanceAdminMixin, FinancePageContextMixin, TemplateView):
    permission_codename = "finance.report.view"
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

