from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from finance.models import Account, APInvoice, ARInvoice, Budget, BudgetLine, LedgerEntry


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
    rows = APInvoice.objects.filter(tenant=tenant, status=APInvoice.Status.POSTED).select_related("supplier")
    return rows


def ar_aging(*, tenant):
    rows = ARInvoice.objects.filter(tenant=tenant, status=ARInvoice.Status.POSTED).select_related("customer")
    return rows


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

