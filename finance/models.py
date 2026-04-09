from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class FinanceTimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Account(FinanceTimestampedModel):
    class AccountType(models.TextChoices):
        ASSET = "asset", "Asset"
        LIABILITY = "liability", "Liability"
        EQUITY = "equity", "Equity"
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    class NaturalSide(models.TextChoices):
        DEBIT = "debit", "Debit"
        CREDIT = "credit", "Credit"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_accounts")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    natural_side = models.CharField(max_length=10, choices=NaturalSide.choices)
    is_postable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        if self.parent_id and self.parent_id == self.id:
            raise ValidationError({"parent": "Account cannot be parent of itself."})


class FiscalYear(FinanceTimestampedModel):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_fiscal_years")
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]
        unique_together = [("tenant", "name")]

    def __str__(self):
        return self.name

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date must be after start date."})


class FiscalPeriod(FinanceTimestampedModel):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_fiscal_periods")
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name="periods")
    period_no = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ["fiscal_year__start_date", "period_no"]
        unique_together = [("tenant", "fiscal_year", "period_no")]

    def __str__(self):
        return f"{self.fiscal_year.name} / {self.name}"

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date must be after start date."})


class CostCenter(FinanceTimestampedModel):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_cost_centers")
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Project(FinanceTimestampedModel):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_projects")
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(FinanceTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        REVERSED = "reversed", "Reversed"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_journals")
    entry_no = models.CharField(max_length=40, db_index=True)
    posting_date = models.DateField(default=timezone.localdate)
    fiscal_period = models.ForeignKey(FiscalPeriod, null=True, blank=True, on_delete=models.SET_NULL, related_name="journal_entries")
    memo = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    source_document_type = models.CharField(max_length=50, blank=True, default="")
    source_document_id = models.PositiveBigIntegerField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey("auth_tenants.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="finance_posted_journals")
    reversal_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="reversal_entries")

    class Meta:
        ordering = ["-posting_date", "-id"]
        unique_together = [("tenant", "entry_no")]

    def __str__(self):
        return self.entry_no

    @property
    def debit_total(self):
        return sum((line.debit for line in self.lines.all()), Decimal("0"))

    @property
    def credit_total(self):
        return sum((line.credit for line in self.lines.all()), Decimal("0"))


class JournalLine(models.Model):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_journal_lines")
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    line_no = models.PositiveIntegerField(default=1)
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="journal_lines")
    description = models.CharField(max_length=255, blank=True)
    debit = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    credit = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    cost_center = models.ForeignKey(CostCenter, null=True, blank=True, on_delete=models.SET_NULL, related_name="journal_lines")
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, related_name="journal_lines")

    class Meta:
        ordering = ["line_no", "id"]

    def clean(self):
        if self.debit < 0 or self.credit < 0:
            raise ValidationError("Debit/credit cannot be negative.")
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("Either debit or credit must be greater than zero.")
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("Line cannot have both debit and credit.")


class LedgerEntry(models.Model):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_ledger_entries")
    posting_date = models.DateField()
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, related_name="ledger_entries")
    journal_line = models.ForeignKey(JournalLine, on_delete=models.PROTECT, related_name="ledger_entries")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="ledger_entries")
    debit = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    credit = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    cost_center = models.ForeignKey(CostCenter, null=True, blank=True, on_delete=models.SET_NULL, related_name="ledger_entries")
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, related_name="ledger_entries")
    source_document_type = models.CharField(max_length=50, blank=True, default="")
    source_document_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["posting_date", "id"]
        indexes = [models.Index(fields=["tenant", "posting_date"]), models.Index(fields=["tenant", "account"])]


class APInvoice(FinanceTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_ap_invoices")
    doc_no = models.CharField(max_length=40)
    supplier = models.ForeignKey("foundation.Supplier", on_delete=models.PROTECT, related_name="ap_invoices")
    posting_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)
    currency = models.ForeignKey("foundation.Currency", null=True, blank=True, on_delete=models.SET_NULL)
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("1"))
    subtotal = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    shipping_charge = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    memo = models.CharField(max_length=255, blank=True)
    expense_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="ap_expense_docs")
    ap_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="ap_control_docs")
    tax_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="ap_tax_docs")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    journal_entry = models.ForeignKey(JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="ap_documents")

    class Meta:
        ordering = ["-posting_date", "-id"]
        unique_together = [("tenant", "doc_no")]


class APInvoiceLine(models.Model):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_ap_invoice_lines")
    invoice = models.ForeignKey(APInvoice, on_delete=models.CASCADE, related_name="lines")
    line_no = models.PositiveIntegerField(default=1)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("1"))
    unit_price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))


class APPayment(FinanceTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_ap_payments")
    doc_no = models.CharField(max_length=40)
    supplier = models.ForeignKey("foundation.Supplier", on_delete=models.PROTECT, related_name="ap_payments")
    posting_date = models.DateField(default=timezone.localdate)
    amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    payment_method = models.ForeignKey("foundation.PaymentMethod", null=True, blank=True, on_delete=models.SET_NULL)
    bank_account = models.ForeignKey("finance.BankAccount", null=True, blank=True, on_delete=models.SET_NULL, related_name="ap_payments")
    ap_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="ap_payment_control_docs")
    cash_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="ap_payment_cash_docs")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    journal_entry = models.ForeignKey(JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="ap_payment_documents")

    class Meta:
        ordering = ["-posting_date", "-id"]
        unique_together = [("tenant", "doc_no")]


class ARInvoice(FinanceTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_ar_invoices")
    doc_no = models.CharField(max_length=40)
    customer = models.ForeignKey("foundation.Customer", on_delete=models.PROTECT, related_name="ar_invoices")
    posting_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)
    currency = models.ForeignKey("foundation.Currency", null=True, blank=True, on_delete=models.SET_NULL)
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("1"))
    subtotal = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    shipping_charge = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    memo = models.CharField(max_length=255, blank=True)
    revenue_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="ar_revenue_docs")
    ar_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="ar_control_docs")
    tax_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="ar_tax_docs")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    journal_entry = models.ForeignKey(JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="ar_documents")

    class Meta:
        ordering = ["-posting_date", "-id"]
        unique_together = [("tenant", "doc_no")]


class ARInvoiceLine(models.Model):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_ar_invoice_lines")
    invoice = models.ForeignKey(ARInvoice, on_delete=models.CASCADE, related_name="lines")
    line_no = models.PositiveIntegerField(default=1)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("1"))
    unit_price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))


class ARReceipt(FinanceTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_ar_receipts")
    doc_no = models.CharField(max_length=40)
    customer = models.ForeignKey("foundation.Customer", on_delete=models.PROTECT, related_name="ar_receipts")
    posting_date = models.DateField(default=timezone.localdate)
    amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    payment_method = models.ForeignKey("foundation.PaymentMethod", null=True, blank=True, on_delete=models.SET_NULL)
    bank_account = models.ForeignKey("finance.BankAccount", null=True, blank=True, on_delete=models.SET_NULL, related_name="ar_receipts")
    ar_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="ar_receipt_control_docs")
    cash_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="ar_receipt_cash_docs")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    journal_entry = models.ForeignKey(JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="ar_receipt_documents")

    class Meta:
        ordering = ["-posting_date", "-id"]
        unique_together = [("tenant", "doc_no")]


class BankAccount(FinanceTimestampedModel):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_bank_accounts")
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=120)
    account_number = models.CharField(max_length=80, blank=True)
    gl_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="bank_accounts")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} - {self.name}"


class CashTransaction(FinanceTimestampedModel):
    class Direction(models.TextChoices):
        IN = "in", "Cash In"
        OUT = "out", "Cash Out"
        TRANSFER = "transfer", "Transfer"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_cash_transactions")
    doc_no = models.CharField(max_length=40)
    posting_date = models.DateField(default=timezone.localdate)
    direction = models.CharField(max_length=20, choices=Direction.choices)
    amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    from_bank_account = models.ForeignKey(BankAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name="cash_out_transactions")
    to_bank_account = models.ForeignKey(BankAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name="cash_in_transactions")
    counterparty_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="cash_counterparty_transactions")
    memo = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    journal_entry = models.ForeignKey(JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="cash_documents")

    class Meta:
        ordering = ["-posting_date", "-id"]
        unique_together = [("tenant", "doc_no")]


class FixedAsset(FinanceTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        DISPOSED = "disposed", "Disposed"

    class DepreciationMethod(models.TextChoices):
        STRAIGHT_LINE = "straight_line", "Straight line"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_fixed_assets")
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=200)
    capitalization_date = models.DateField(default=timezone.localdate)
    cost = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    salvage_value = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    useful_life_months = models.PositiveIntegerField(default=60)
    depreciation_method = models.CharField(max_length=30, choices=DepreciationMethod.choices, default=DepreciationMethod.STRAIGHT_LINE)
    asset_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="fixed_asset_accounts")
    accumulated_depreciation_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="accumulated_depreciation_accounts")
    depreciation_expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="depreciation_expense_accounts")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["code"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} - {self.name}"


class AssetDepreciation(FinanceTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_asset_depreciations")
    asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name="depreciation_entries")
    period = models.ForeignKey(FiscalPeriod, null=True, blank=True, on_delete=models.SET_NULL, related_name="asset_depreciations")
    posting_date = models.DateField(default=timezone.localdate)
    amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    journal_entry = models.ForeignKey(JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="asset_depreciation_documents")


class Budget(FinanceTimestampedModel):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_budgets")
    name = models.CharField(max_length=120)
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name="budgets")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-fiscal_year__start_date", "name"]
        unique_together = [("tenant", "name", "fiscal_year")]

    def __str__(self):
        return self.name


class BudgetLine(models.Model):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="finance_budget_lines")
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="lines")
    fiscal_period = models.ForeignKey(FiscalPeriod, on_delete=models.CASCADE, related_name="budget_lines")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="budget_lines")
    cost_center = models.ForeignKey(CostCenter, null=True, blank=True, on_delete=models.SET_NULL, related_name="budget_lines")
    amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        unique_together = [("budget", "fiscal_period", "account", "cost_center")]

