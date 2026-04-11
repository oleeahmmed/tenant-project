from decimal import Decimal

from django.db import transaction


def sync_grn_to_finance_ap_invoice(*, receipt):
    """
    Create/update a draft AP invoice in Finance from posted GRN.
    Returns tuple: (status, note)
    """
    tenant = receipt.tenant
    if not tenant.is_module_enabled("finance"):
        return ("skipped", "Finance module disabled for tenant.")

    try:
        from finance.models import APInvoice, APInvoiceLine
    except Exception:
        return ("skipped", "Finance app not available.")

    with transaction.atomic():
        if receipt.finance_ap_invoice_id:
            ap = receipt.finance_ap_invoice
            if ap.status != APInvoice.Status.DRAFT:
                return ("skipped", "Linked AP invoice is not draft.")
            ap.lines.all().delete()
        else:
            ap = APInvoice.objects.create(
                tenant=tenant,
                doc_no=f"AP-{receipt.doc_no}",
                supplier=receipt.supplier,
                posting_date=receipt.receipt_date,
                subtotal=Decimal("0"),
                total_amount=Decimal("0"),
                memo=f"Auto-created from GRN {receipt.doc_no}",
            )

        subtotal = Decimal("0")
        for idx, line in enumerate(receipt.lines.all(), start=1):
            lt = line.line_total or (line.quantity_received * line.unit_cost)
            APInvoiceLine.objects.create(
                tenant=tenant,
                invoice=ap,
                line_no=idx,
                description=line.product.name,
                quantity=line.quantity_received,
                unit_price=line.unit_cost,
                line_total=lt,
            )
            subtotal += lt

        ap.subtotal = subtotal
        ap.tax_amount = Decimal("0")
        ap.total_amount = subtotal
        ap.save(update_fields=["subtotal", "tax_amount", "total_amount", "updated_at"])

        receipt.finance_ap_invoice = ap
        receipt.finance_sync_status = "synced"
        receipt.finance_sync_note = f"AP invoice {ap.doc_no} ready as draft."
        receipt.save(update_fields=["finance_ap_invoice", "finance_sync_status", "finance_sync_note", "updated_at"])
        return ("synced", receipt.finance_sync_note)

