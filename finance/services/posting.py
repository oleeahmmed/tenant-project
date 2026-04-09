from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from finance.models import (
    APInvoice,
    APPayment,
    ARInvoice,
    ARReceipt,
    AssetDepreciation,
    CashTransaction,
    JournalEntry,
    JournalLine,
    LedgerEntry,
)


def _ensure_period_open(journal: JournalEntry):
    if journal.fiscal_period and journal.fiscal_period.is_closed:
        raise ValidationError("Selected fiscal period is closed.")


def _journal_totals(journal: JournalEntry):
    debit = Decimal("0")
    credit = Decimal("0")
    for line in journal.lines.all():
        debit += line.debit
        credit += line.credit
    return debit, credit


@transaction.atomic
def post_journal_entry(*, journal: JournalEntry, posted_by=None):
    if journal.status != JournalEntry.Status.DRAFT:
        raise ValidationError("Only draft journal entries can be posted.")
    _ensure_period_open(journal)
    debit, credit = _journal_totals(journal)
    if debit <= 0 or credit <= 0:
        raise ValidationError("Journal requires debit and credit lines.")
    if debit != credit:
        raise ValidationError("Journal is not balanced (debit must equal credit).")

    lines = list(journal.lines.select_related("account", "cost_center", "project").all())
    if not lines:
        raise ValidationError("Journal has no lines.")

    ledger_rows = []
    for line in lines:
        ledger_rows.append(
            LedgerEntry(
                tenant=journal.tenant,
                posting_date=journal.posting_date,
                journal_entry=journal,
                journal_line=line,
                account=line.account,
                debit=line.debit,
                credit=line.credit,
                cost_center=line.cost_center,
                project=line.project,
                source_document_type=journal.source_document_type,
                source_document_id=journal.source_document_id,
            )
        )
    LedgerEntry.objects.bulk_create(ledger_rows)
    journal.status = JournalEntry.Status.POSTED
    journal.posted_at = timezone.now()
    journal.posted_by = posted_by
    journal.save(update_fields=["status", "posted_at", "posted_by", "updated_at"])
    return journal


@transaction.atomic
def reverse_journal_entry(*, journal: JournalEntry, posted_by=None):
    if journal.status != JournalEntry.Status.POSTED:
        raise ValidationError("Only posted journal entries can be reversed.")
    if journal.reversal_entries.filter(status=JournalEntry.Status.POSTED).exists():
        raise ValidationError("A posted reversal already exists.")

    reversal = JournalEntry.objects.create(
        tenant=journal.tenant,
        entry_no=f"{journal.entry_no}-REV",
        posting_date=timezone.localdate(),
        fiscal_period=journal.fiscal_period,
        memo=f"Reversal of {journal.entry_no}",
        source_document_type=journal.source_document_type,
        source_document_id=journal.source_document_id,
        reversal_of=journal,
    )
    lines = []
    for line in journal.lines.all():
        lines.append(
            JournalLine(
                tenant=journal.tenant,
                journal_entry=reversal,
                line_no=line.line_no,
                account=line.account,
                description=f"Reversal: {line.description}",
                debit=line.credit,
                credit=line.debit,
                cost_center=line.cost_center,
                project=line.project,
            )
        )
    JournalLine.objects.bulk_create(lines)
    post_journal_entry(journal=reversal, posted_by=posted_by)
    journal.status = JournalEntry.Status.REVERSED
    journal.save(update_fields=["status", "updated_at"])
    return reversal


def _post_simple_document(*, tenant, doc_type: str, doc_id: int, posting_date, memo: str, lines, posted_by=None):
    journal = JournalEntry.objects.create(
        tenant=tenant,
        entry_no=f"{doc_type}-{doc_id}",
        posting_date=posting_date,
        memo=memo,
        source_document_type=doc_type,
        source_document_id=doc_id,
    )
    journal_lines = []
    for i, row in enumerate(lines, start=1):
        journal_lines.append(
            JournalLine(
                tenant=tenant,
                journal_entry=journal,
                line_no=i,
                account=row["account"],
                description=row.get("description", ""),
                debit=row.get("debit", Decimal("0")),
                credit=row.get("credit", Decimal("0")),
            )
        )
    JournalLine.objects.bulk_create(journal_lines)
    post_journal_entry(journal=journal, posted_by=posted_by)
    return journal


@transaction.atomic
def post_ap_invoice(*, invoice: APInvoice, posted_by=None):
    if invoice.status != APInvoice.Status.DRAFT:
        raise ValidationError("Only draft AP invoices can be posted.")
    if not invoice.expense_account_id or not invoice.ap_account_id:
        raise ValidationError("Expense and AP accounts are required.")
    base_amount = invoice.subtotal + invoice.shipping_charge
    lines = [
        {"account": invoice.expense_account, "debit": base_amount, "credit": Decimal("0"), "description": f"AP expense {invoice.doc_no}"},
    ]
    if invoice.tax_amount and invoice.tax_amount > 0 and invoice.tax_account_id:
        lines.append({"account": invoice.tax_account, "debit": invoice.tax_amount, "credit": Decimal("0"), "description": f"AP tax {invoice.doc_no}"})
    lines.append({"account": invoice.ap_account, "debit": Decimal("0"), "credit": invoice.total_amount, "description": f"AP control {invoice.doc_no}"})
    journal = _post_simple_document(
        tenant=invoice.tenant,
        doc_type="ap_invoice",
        doc_id=invoice.id,
        posting_date=invoice.posting_date,
        memo=invoice.memo or f"Post AP invoice {invoice.doc_no}",
        lines=lines,
        posted_by=posted_by,
    )
    invoice.journal_entry = journal
    invoice.status = APInvoice.Status.POSTED
    invoice.save(update_fields=["journal_entry", "status", "updated_at"])
    return journal


@transaction.atomic
def post_ar_invoice(*, invoice: ARInvoice, posted_by=None):
    if invoice.status != ARInvoice.Status.DRAFT:
        raise ValidationError("Only draft AR invoices can be posted.")
    if not invoice.revenue_account_id or not invoice.ar_account_id:
        raise ValidationError("Revenue and AR accounts are required.")
    base_amount = invoice.subtotal + invoice.shipping_charge
    lines = [
        {"account": invoice.ar_account, "debit": invoice.total_amount, "credit": Decimal("0"), "description": f"AR control {invoice.doc_no}"},
        {"account": invoice.revenue_account, "debit": Decimal("0"), "credit": base_amount, "description": f"AR revenue {invoice.doc_no}"},
    ]
    if invoice.tax_amount and invoice.tax_amount > 0 and invoice.tax_account_id:
        lines.append({"account": invoice.tax_account, "debit": Decimal("0"), "credit": invoice.tax_amount, "description": f"AR tax {invoice.doc_no}"})
    journal = _post_simple_document(
        tenant=invoice.tenant,
        doc_type="ar_invoice",
        doc_id=invoice.id,
        posting_date=invoice.posting_date,
        memo=invoice.memo or f"Post AR invoice {invoice.doc_no}",
        lines=lines,
        posted_by=posted_by,
    )
    invoice.journal_entry = journal
    invoice.status = ARInvoice.Status.POSTED
    invoice.save(update_fields=["journal_entry", "status", "updated_at"])
    return journal


@transaction.atomic
def post_ap_payment(*, payment: APPayment, posted_by=None):
    if payment.status != APPayment.Status.DRAFT:
        raise ValidationError("Only draft AP payments can be posted.")
    if not payment.ap_account_id or not payment.cash_account_id:
        raise ValidationError("AP and cash/bank accounts are required.")
    journal = _post_simple_document(
        tenant=payment.tenant,
        doc_type="ap_payment",
        doc_id=payment.id,
        posting_date=payment.posting_date,
        memo=f"Post AP payment {payment.doc_no}",
        lines=[
            {"account": payment.ap_account, "debit": payment.amount, "credit": Decimal("0"), "description": f"AP settlement {payment.doc_no}"},
            {"account": payment.cash_account, "debit": Decimal("0"), "credit": payment.amount, "description": f"Cash out {payment.doc_no}"},
        ],
        posted_by=posted_by,
    )
    payment.journal_entry = journal
    payment.status = APPayment.Status.POSTED
    payment.save(update_fields=["journal_entry", "status", "updated_at"])
    return journal


@transaction.atomic
def post_ar_receipt(*, receipt: ARReceipt, posted_by=None):
    if receipt.status != ARReceipt.Status.DRAFT:
        raise ValidationError("Only draft AR receipts can be posted.")
    if not receipt.ar_account_id or not receipt.cash_account_id:
        raise ValidationError("AR and cash/bank accounts are required.")
    journal = _post_simple_document(
        tenant=receipt.tenant,
        doc_type="ar_receipt",
        doc_id=receipt.id,
        posting_date=receipt.posting_date,
        memo=f"Post AR receipt {receipt.doc_no}",
        lines=[
            {"account": receipt.cash_account, "debit": receipt.amount, "credit": Decimal("0"), "description": f"Cash in {receipt.doc_no}"},
            {"account": receipt.ar_account, "debit": Decimal("0"), "credit": receipt.amount, "description": f"AR settlement {receipt.doc_no}"},
        ],
        posted_by=posted_by,
    )
    receipt.journal_entry = journal
    receipt.status = ARReceipt.Status.POSTED
    receipt.save(update_fields=["journal_entry", "status", "updated_at"])
    return journal


@transaction.atomic
def post_cash_transaction(*, txn: CashTransaction, posted_by=None):
    if txn.status != CashTransaction.Status.DRAFT:
        raise ValidationError("Only draft cash transactions can be posted.")
    if txn.direction == CashTransaction.Direction.TRANSFER:
        if not txn.from_bank_account_id or not txn.to_bank_account_id:
            raise ValidationError("Transfer requires both from and to bank accounts.")
        lines = [
            {"account": txn.to_bank_account.gl_account, "debit": txn.amount, "credit": Decimal("0"), "description": f"Transfer in {txn.doc_no}"},
            {"account": txn.from_bank_account.gl_account, "debit": Decimal("0"), "credit": txn.amount, "description": f"Transfer out {txn.doc_no}"},
        ]
    elif txn.direction == CashTransaction.Direction.IN:
        if not txn.to_bank_account_id or not txn.counterparty_account_id:
            raise ValidationError("Cash in requires destination bank and counterparty account.")
        lines = [
            {"account": txn.to_bank_account.gl_account, "debit": txn.amount, "credit": Decimal("0"), "description": f"Cash in {txn.doc_no}"},
            {"account": txn.counterparty_account, "debit": Decimal("0"), "credit": txn.amount, "description": f"Counterparty {txn.doc_no}"},
        ]
    else:
        if not txn.from_bank_account_id or not txn.counterparty_account_id:
            raise ValidationError("Cash out requires source bank and counterparty account.")
        lines = [
            {"account": txn.counterparty_account, "debit": txn.amount, "credit": Decimal("0"), "description": f"Counterparty {txn.doc_no}"},
            {"account": txn.from_bank_account.gl_account, "debit": Decimal("0"), "credit": txn.amount, "description": f"Cash out {txn.doc_no}"},
        ]
    journal = _post_simple_document(
        tenant=txn.tenant,
        doc_type="cash_transaction",
        doc_id=txn.id,
        posting_date=txn.posting_date,
        memo=txn.memo or f"Post cash transaction {txn.doc_no}",
        lines=lines,
        posted_by=posted_by,
    )
    txn.journal_entry = journal
    txn.status = CashTransaction.Status.POSTED
    txn.save(update_fields=["journal_entry", "status", "updated_at"])
    return journal


@transaction.atomic
def post_asset_depreciation(*, dep: AssetDepreciation, posted_by=None):
    if dep.status != AssetDepreciation.Status.DRAFT:
        raise ValidationError("Only draft depreciation rows can be posted.")
    asset = dep.asset
    journal = _post_simple_document(
        tenant=dep.tenant,
        doc_type="asset_depreciation",
        doc_id=dep.id,
        posting_date=dep.posting_date,
        memo=f"Depreciation for {asset.code}",
        lines=[
            {"account": asset.depreciation_expense_account, "debit": dep.amount, "credit": Decimal("0"), "description": f"Dep expense {asset.code}"},
            {"account": asset.accumulated_depreciation_account, "debit": Decimal("0"), "credit": dep.amount, "description": f"Accum dep {asset.code}"},
        ],
        posted_by=posted_by,
    )
    dep.journal_entry = journal
    dep.status = AssetDepreciation.Status.POSTED
    dep.save(update_fields=["journal_entry", "status", "updated_at"])
    return journal

