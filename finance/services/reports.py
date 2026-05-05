from calendar import month_name
from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.db.models import F
from django.db.models import Sum
from django.db.models.functions import Coalesce

from finance.models import Account, APInvoice, ARInvoice, BankAccount, Budget, BudgetLine, LedgerEntry


def general_ledger(*, tenant, date_from: date | None = None, date_to: date | None = None, account_id: int | None = None):
    qs = LedgerEntry.objects.filter(tenant=tenant).select_related("account", "journal_entry")
    if date_from:
        qs = qs.filter(posting_date__gte=date_from)
    if date_to:
        qs = qs.filter(posting_date__lte=date_to)
    if account_id:
        qs = qs.filter(account_id=account_id)
    return qs.order_by("posting_date", "id")


def trial_balance(*, tenant, date_to: date | None = None):
    qs = LedgerEntry.objects.filter(tenant=tenant).values("account_id", "account__code", "account__name")
    if date_to:
        qs = qs.filter(posting_date__lte=date_to)
    rows = qs.annotate(total_debit=Sum("debit"), total_credit=Sum("credit")).order_by("account__code")
    total_debit = sum((r["total_debit"] or Decimal("0") for r in rows), Decimal("0"))
    total_credit = sum((r["total_credit"] or Decimal("0") for r in rows), Decimal("0"))
    return rows, total_debit, total_credit


def profit_and_loss(*, tenant, date_from: date | None = None, date_to: date | None = None):
    qs = LedgerEntry.objects.filter(tenant=tenant).select_related("account")
    if date_from:
        qs = qs.filter(posting_date__gte=date_from)
    if date_to:
        qs = qs.filter(posting_date__lte=date_to)
    account_totals = defaultdict(lambda: Decimal("0"))
    labels = {}
    for row in qs:
        if row.account.account_type not in (Account.AccountType.INCOME, Account.AccountType.EXPENSE):
            continue
        key = row.account_id
        labels[key] = f"{row.account.code} - {row.account.name}"
        balance = row.credit - row.debit if row.account.account_type == Account.AccountType.INCOME else row.debit - row.credit
        account_totals[key] += balance
    income = []
    expense = []
    total_income = Decimal("0")
    total_expense = Decimal("0")
    for acc_id, amt in account_totals.items():
        acc = Account.objects.filter(pk=acc_id).first()
        item = {"account_id": acc_id, "label": labels[acc_id], "amount": amt}
        if acc and acc.account_type == Account.AccountType.INCOME:
            income.append(item)
            total_income += amt
        else:
            expense.append(item)
            total_expense += amt
    net_profit = total_income - total_expense
    return income, expense, total_income, total_expense, net_profit


def balance_sheet(*, tenant, date_to: date | None = None):
    qs = LedgerEntry.objects.filter(tenant=tenant).select_related("account")
    if date_to:
        qs = qs.filter(posting_date__lte=date_to)
    groups = {
        "assets": defaultdict(lambda: Decimal("0")),
        "liabilities": defaultdict(lambda: Decimal("0")),
        "equity": defaultdict(lambda: Decimal("0")),
    }
    labels = {}
    for row in qs:
        atype = row.account.account_type
        if atype not in (Account.AccountType.ASSET, Account.AccountType.LIABILITY, Account.AccountType.EQUITY):
            continue
        labels[row.account_id] = f"{row.account.code} - {row.account.name}"
        if atype == Account.AccountType.ASSET:
            groups["assets"][row.account_id] += row.debit - row.credit
        elif atype == Account.AccountType.LIABILITY:
            groups["liabilities"][row.account_id] += row.credit - row.debit
        else:
            groups["equity"][row.account_id] += row.credit - row.debit

    def _rows(group):
        return [{"account_id": k, "label": labels.get(k, str(k)), "amount": v} for k, v in group.items()]

    assets = _rows(groups["assets"])
    liabilities = _rows(groups["liabilities"])
    equity = _rows(groups["equity"])
    total_assets = sum((r["amount"] for r in assets), Decimal("0"))
    total_liabilities = sum((r["amount"] for r in liabilities), Decimal("0"))
    total_equity = sum((r["amount"] for r in equity), Decimal("0"))
    return assets, liabilities, equity, total_assets, total_liabilities, total_equity


def ap_aging(*, tenant):
    rows = (
        APInvoice.objects.filter(tenant=tenant, status=APInvoice.Status.POSTED)
        .select_related("supplier")
        .annotate(applied_amount=Coalesce(Sum("payment_allocations__amount"), Decimal("0")))
        .annotate(outstanding_amount=F("total_amount") - F("applied_amount"))
        .filter(outstanding_amount__gt=0)
    )
    return rows.order_by("due_date", "posting_date", "id")


def ar_aging(*, tenant):
    rows = (
        ARInvoice.objects.filter(tenant=tenant, status=ARInvoice.Status.POSTED)
        .select_related("customer")
        .annotate(applied_amount=Coalesce(Sum("receipt_allocations__amount"), Decimal("0")))
        .annotate(outstanding_amount=F("total_amount") - F("applied_amount"))
        .filter(outstanding_amount__gt=0)
    )
    return rows.order_by("due_date", "posting_date", "id")


def budget_vs_actual(*, tenant, budget_id: int):
    budget = Budget.objects.filter(tenant=tenant, pk=budget_id).first()
    if not budget:
        return None, []
    lines = BudgetLine.objects.filter(tenant=tenant, budget=budget).select_related("account", "fiscal_period")
    out = []
    for line in lines:
        actual = (
            LedgerEntry.objects.filter(tenant=tenant, account=line.account, posting_date__gte=line.fiscal_period.start_date, posting_date__lte=line.fiscal_period.end_date)
            .aggregate(dr=Sum("debit"), cr=Sum("credit"))
        )
        if line.account.account_type in (Account.AccountType.INCOME, Account.AccountType.LIABILITY, Account.AccountType.EQUITY):
            actual_amount = (actual["cr"] or Decimal("0")) - (actual["dr"] or Decimal("0"))
        else:
            actual_amount = (actual["dr"] or Decimal("0")) - (actual["cr"] or Decimal("0"))
        variance = line.amount - actual_amount
        out.append(
            {
                "period": line.fiscal_period.name,
                "account": f"{line.account.code} - {line.account.name}",
                "budget_amount": line.amount,
                "actual_amount": actual_amount,
                "variance": variance,
            }
        )
    return budget, out


def monthly_tax_summary(*, tenant, year: int | None = None):
    """Posted AP/AR only: VAT/tax and net amounts by calendar month."""
    ap_qs = APInvoice.objects.filter(tenant=tenant, status=APInvoice.Status.POSTED)
    ar_qs = ARInvoice.objects.filter(tenant=tenant, status=ARInvoice.Status.POSTED)
    if year:
        ap_qs = ap_qs.filter(posting_date__year=year)
        ar_qs = ar_qs.filter(posting_date__year=year)
    by_month: dict[int, dict[str, Decimal]] = defaultdict(
        lambda: {
            "ap_tax": Decimal("0"),
            "ar_tax": Decimal("0"),
            "ap_net": Decimal("0"),
            "ar_net": Decimal("0"),
        }
    )
    for inv in ap_qs:
        m = inv.posting_date.month
        by_month[m]["ap_tax"] += inv.tax_amount or Decimal("0")
        by_month[m]["ap_net"] += (inv.subtotal or Decimal("0")) + (inv.shipping_charge or Decimal("0"))
    for inv in ar_qs:
        m = inv.posting_date.month
        by_month[m]["ar_tax"] += inv.tax_amount or Decimal("0")
        by_month[m]["ar_net"] += (inv.subtotal or Decimal("0")) + (inv.shipping_charge or Decimal("0"))
    rows = []
    for m in sorted(by_month.keys()):
        d = by_month[m]
        rows.append(
            {
                "month": m,
                "month_label": month_name[m],
                "ap_tax": d["ap_tax"],
                "ar_tax": d["ar_tax"],
                "ap_net": d["ap_net"],
                "ar_net": d["ar_net"],
            }
        )
    return rows


def bank_gl_register(*, tenant, bank_account_id: int, date_from: date | None = None, date_to: date | None = None):
    ba = BankAccount.objects.select_related("gl_account").get(pk=bank_account_id, tenant=tenant)
    qs = LedgerEntry.objects.filter(tenant=tenant, account_id=ba.gl_account_id).select_related(
        "journal_entry", "account"
    )
    if date_from:
        qs = qs.filter(posting_date__gte=date_from)
    if date_to:
        qs = qs.filter(posting_date__lte=date_to)
    qs = qs.order_by("posting_date", "id")
    running = Decimal("0")
    rows = []
    for e in qs:
        running += e.debit - e.credit
        rows.append(
            {
                "posting_date": e.posting_date,
                "entry_no": e.journal_entry.entry_no,
                "memo": e.journal_entry.memo or "",
                "debit": e.debit,
                "credit": e.credit,
                "balance": running,
            }
        )
    return ba, rows

