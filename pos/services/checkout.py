"""Create POS sale + lines + payments in one transaction."""

from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from foundation.models import Customer, PaymentMethod, Product, Warehouse

from ..models import POSPayment, POSSale, POSSaleLine, POSSession, allocate_pos_doc_no


def _dec(val, default="0"):
    if val is None or val == "":
        return Decimal(default)
    return Decimal(str(val))


def _q2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@transaction.atomic
def create_sale_from_checkout(
    *,
    tenant,
    session: POSSession,
    user,
    warehouse: Warehouse,
    lines_payload,
    payments_payload,
    customer_id=None,
    tax_amount=None,
    discount_amount=None,
    notes="",
):
    """
    lines_payload: [{"product_id": int, "quantity": str|Decimal, "unit_price": str|Decimal, "description": str?}]
    payments_payload: [{"payment_method_id": int, "amount": str|Decimal, "reference": str?}]
    """
    if session.status != POSSession.Status.OPEN:
        raise ValidationError("Session is not open.")
    if session.register.tenant_id != tenant.id:
        raise ValidationError("Invalid session.")
    if warehouse.tenant_id != tenant.id:
        raise ValidationError("Invalid warehouse.")

    subtotal = Decimal("0")
    line_objs = []
    for row in lines_payload:
        pid = int(row["product_id"])
        qty = _dec(row.get("quantity", "1"))
        price = _dec(row.get("unit_price", "0"))
        if qty <= 0:
            raise ValidationError("Line quantity must be positive.")
        product = Product.objects.filter(tenant=tenant, pk=pid, is_active=True).first()
        if not product:
            raise ValidationError(f"Invalid product id {pid}.")
        lt = qty * price
        subtotal += lt
        line_objs.append(
            {
                "product": product,
                "product_variant_id": row.get("product_variant_id"),
                "description": (row.get("description") or "")[:255],
                "quantity": qty,
                "unit_price": price,
                "line_total": lt,
            }
        )

    tax = _dec(tax_amount, "0")
    discount = _dec(discount_amount, "0")
    total = subtotal + tax - discount
    if total < 0:
        raise ValidationError("Total cannot be negative.")

    pay_sum = Decimal("0")
    pay_rows = []
    for row in payments_payload:
        mid = int(row["payment_method_id"])
        amt = _dec(row.get("amount", "0"))
        if amt <= 0:
            continue
        pm = PaymentMethod.objects.filter(tenant=tenant, pk=mid, is_active=True).first()
        if not pm:
            raise ValidationError(f"Invalid payment method {mid}.")
        pay_sum += amt
        pay_rows.append(
            {
                "payment_method": pm,
                "amount": amt,
                "reference": (row.get("reference") or "")[:120],
            }
        )

    if _q2(pay_sum) != _q2(total):
        raise ValidationError(f"Payments ({pay_sum}) must equal total ({total}).")

    customer = None
    if customer_id:
        customer = Customer.objects.filter(tenant=tenant, pk=int(customer_id), is_active=True).first()
        if not customer:
            raise ValidationError("Invalid customer.")

    doc_no = allocate_pos_doc_no(tenant)
    sale = POSSale(
        tenant=tenant,
        session=session,
        doc_no=doc_no,
        customer=customer,
        warehouse=warehouse,
        status=POSSale.Status.COMPLETED,
        subtotal=subtotal,
        tax_amount=tax,
        discount_amount=discount,
        total_amount=total,
        notes=notes or "",
        created_by=user,
    )
    sale.save()

    for lo in line_objs:
        pv_id = lo.get("product_variant_id")
        line = POSSaleLine(
            sale=sale,
            product=lo["product"],
            description=lo["description"],
            quantity=lo["quantity"],
            unit_price=lo["unit_price"],
            line_total=lo["line_total"],
        )
        if pv_id:
            line.product_variant_id = int(pv_id)
        line.save()

    for pr in pay_rows:
        POSPayment.objects.create(sale=sale, **pr)

    return sale
