from decimal import Decimal

from django.db import transaction


def sync_delivery_to_finance_ar_invoice(*, delivery):
    tenant = delivery.tenant
    if not tenant.is_module_enabled("finance"):
        return ("skipped", "Finance module disabled for tenant.")

    try:
        from finance.models import ARInvoice, ARInvoiceLine
    except Exception:
        return ("skipped", "Finance app not available.")

    with transaction.atomic():
        if delivery.finance_ar_invoice_id:
            inv = delivery.finance_ar_invoice
            if inv.status != ARInvoice.Status.DRAFT:
                return ("skipped", "Linked AR invoice is not draft.")
            inv.lines.all().delete()
        else:
            inv = ARInvoice.objects.create(
                tenant=tenant,
                doc_no=f"AR-{delivery.doc_no}",
                customer=delivery.customer,
                posting_date=delivery.delivery_date,
                subtotal=Decimal("0"),
                total_amount=Decimal("0"),
                memo=f"Auto-created from Delivery {delivery.doc_no}",
            )

        subtotal = Decimal("0")
        for idx, line in enumerate(delivery.lines.all(), start=1):
            lt = line.line_total or (line.quantity_delivered * line.unit_price)
            ARInvoiceLine.objects.create(
                tenant=tenant,
                invoice=inv,
                line_no=idx,
                description=line.product.name,
                quantity=line.quantity_delivered,
                unit_price=line.unit_price,
                line_total=lt,
            )
            subtotal += lt

        inv.subtotal = subtotal
        inv.tax_amount = Decimal("0")
        inv.total_amount = subtotal
        inv.save(update_fields=["subtotal", "tax_amount", "total_amount", "updated_at"])

        delivery.finance_ar_invoice = inv
        delivery.finance_sync_status = "synced"
        delivery.finance_sync_note = f"AR invoice {inv.doc_no} ready as draft."
        delivery.save(update_fields=["finance_ar_invoice", "finance_sync_status", "finance_sync_note", "updated_at"])
        return ("synced", delivery.finance_sync_note)

