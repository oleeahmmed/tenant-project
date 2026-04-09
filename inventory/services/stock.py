"""Stock balances and document posting (SAP-style movements → ledger + on-hand)."""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import F

from foundation.models import Product, Warehouse

from inventory.models import (
    GoodsIssue,
    InventoryTransfer,
    StockAdjustment,
    StockAdjustmentItem,
    StockTransaction,
    WarehouseStock,
)


def purge_empty_stock_adjustment_lines(adj: StockAdjustment) -> int:
    """Delete formset spare rows with no SKU (whitespace-only counts as empty)."""
    to_delete = []
    for row in adj.items.only("pk", "product_sku"):
        if not (row.product_sku or "").strip():
            to_delete.append(row.pk)
    if not to_delete:
        return 0
    return StockAdjustmentItem.objects.filter(pk__in=to_delete).delete()[0]


def get_product_warehouse_qty(tenant_id: int, product_id: int, warehouse_id: int) -> Decimal:
    row = WarehouseStock.objects.filter(
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
    ).first()
    return row.quantity if row else Decimal("0")


def _bump_warehouse_stock(
    tenant_id: int,
    product_id: int,
    warehouse_id: int,
    qty_delta: Decimal,
) -> Decimal:
    """Returns new balance."""
    row, _ = WarehouseStock.objects.get_or_create(
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        defaults={"quantity": Decimal("0")},
    )
    WarehouseStock.objects.filter(pk=row.pk).update(quantity=F("quantity") + qty_delta)
    row.refresh_from_db(fields=["quantity"])
    return row.quantity


def _write_tx(
    *,
    tenant_id: int,
    product_id: int,
    warehouse_id: int,
    transaction_type: str,
    qty_signed: Decimal,
    balance_after: Decimal,
    source_document_type: str,
    source_document_id: int,
    reference: str = "",
    notes: str = "",
    variant_id: int | None = None,
):
    qty_abs = abs(qty_signed)
    StockTransaction.objects.create(
        tenant_id=tenant_id,
        product_id=product_id,
        product_variant_id=variant_id,
        warehouse_id=warehouse_id,
        transaction_type=transaction_type,
        quantity=qty_abs,
        qty_signed=qty_signed,
        balance_after=balance_after,
        source_document_type=source_document_type,
        source_document_id=source_document_id,
        reference=reference[:120],
        notes=notes[:2000] if notes else "",
    )


@transaction.atomic
def reverse_document_transactions(
    *,
    tenant_id: int,
    source_document_type: str,
    source_document_id: int,
) -> int:
    """
    Reverse posted stock by deleting ledger rows and subtracting their signed impact.
    Returns number of transactions removed.
    """
    txs = list(
        StockTransaction.objects.select_for_update().filter(
            tenant_id=tenant_id,
            source_document_type=source_document_type,
            source_document_id=source_document_id,
        )
    )
    if not txs:
        return 0

    for tx in txs:
        # Reverse prior signed effect: qty -= tx.qty_signed
        _bump_warehouse_stock(tx.tenant_id, tx.product_id, tx.warehouse_id, -tx.qty_signed)
    count = len(txs)
    StockTransaction.objects.filter(pk__in=[t.pk for t in txs]).delete()
    return count


@transaction.atomic
def post_stock_adjustment(adj: StockAdjustment) -> None:
    if adj.status not in ("draft", "posted"):
        return
    if (
        adj.status == "posted"
        and StockTransaction.objects.filter(
            source_document_type="stock_adjustment",
            source_document_id=adj.pk,
        ).exists()
    ):
        return
    wh = Warehouse.objects.filter(
        tenant_id=adj.tenant_id, code=adj.warehouse_code.strip()
    ).first()
    if not wh:
        raise ValueError(f"Unknown warehouse code {adj.warehouse_code!r} for this workspace.")
    if wh.tenant_id != adj.tenant_id:
        raise ValueError("Warehouse tenant mismatch.")

    for item in adj.items.all():
        prod = Product.objects.filter(
            tenant_id=adj.tenant_id, sku=item.product_sku.strip()
        ).first()
        if not prod:
            raise ValueError(f"Unknown product SKU {item.product_sku!r}.")
        item.save()
        delta = item.quantity_difference
        if delta == 0:
            continue
        bal = _bump_warehouse_stock(adj.tenant_id, prod.id, wh.id, delta)
        _write_tx(
            tenant_id=adj.tenant_id,
            product_id=prod.id,
            warehouse_id=wh.id,
            transaction_type="adjustment",
            qty_signed=delta,
            balance_after=bal,
            source_document_type="stock_adjustment",
            source_document_id=adj.pk,
            reference=adj.adjustment_number,
        )

    adj.status = "posted"
    adj.save(update_fields=["status", "updated_at"])


@transaction.atomic
def post_goods_issue(issue: GoodsIssue) -> None:
    if issue.stock_posted:
        return
    if issue.status not in ("draft", "released"):
        return
    wh = issue.warehouse
    if wh.tenant_id != issue.tenant_id:
        raise ValueError("Warehouse tenant mismatch.")

    for item in issue.items.select_related("product"):
        if item.product.tenant_id != issue.tenant_id:
            raise ValueError("Product tenant mismatch.")
        qty = item.quantity
        if qty <= 0:
            continue
        on_hand = get_product_warehouse_qty(issue.tenant_id, item.product_id, wh.id)
        if qty > on_hand:
            raise ValueError(
                f"Insufficient stock for {item.product}: need {qty}, have {on_hand}."
            )
        neg = -qty
        bal = _bump_warehouse_stock(issue.tenant_id, item.product_id, wh.id, neg)
        _write_tx(
            tenant_id=issue.tenant_id,
            product_id=item.product_id,
            warehouse_id=wh.id,
            transaction_type="out",
            qty_signed=neg,
            balance_after=bal,
            source_document_type="goods_issue",
            source_document_id=issue.pk,
            reference=issue.issue_number,
        )

    issue.stock_posted = True
    issue.status = "released"
    issue.save(update_fields=["stock_posted", "status", "updated_at"])


@transaction.atomic
def post_inventory_transfer(tr: InventoryTransfer) -> None:
    if tr.stock_posted:
        return
    if tr.status not in ("draft", "completed"):
        return
    fw, tw = tr.from_warehouse, tr.to_warehouse
    if fw.tenant_id != tr.tenant_id or tw.tenant_id != tr.tenant_id:
        raise ValueError("Warehouse tenant mismatch.")
    if fw.id == tw.id:
        raise ValueError("Invalid warehouses.")

    for item in tr.items.select_related("product"):
        if item.product.tenant_id != tr.tenant_id:
            raise ValueError("Product tenant mismatch.")
        qty = item.quantity
        if qty <= 0:
            continue
        on_hand = get_product_warehouse_qty(tr.tenant_id, item.product_id, fw.id)
        if qty > on_hand:
            raise ValueError(
                f"Insufficient stock at source for {item.product}: need {qty}, have {on_hand}."
            )
        neg = -qty
        bal_out = _bump_warehouse_stock(tr.tenant_id, item.product_id, fw.id, neg)
        _write_tx(
            tenant_id=tr.tenant_id,
            product_id=item.product_id,
            warehouse_id=fw.id,
            transaction_type="transfer_out",
            qty_signed=neg,
            balance_after=bal_out,
            source_document_type="inventory_transfer",
            source_document_id=tr.pk,
            reference=tr.transfer_number,
        )
        bal_in = _bump_warehouse_stock(tr.tenant_id, item.product_id, tw.id, qty)
        _write_tx(
            tenant_id=tr.tenant_id,
            product_id=item.product_id,
            warehouse_id=tw.id,
            transaction_type="transfer_in",
            qty_signed=qty,
            balance_after=bal_in,
            source_document_type="inventory_transfer",
            source_document_id=tr.pk,
            reference=tr.transfer_number,
        )

    tr.stock_posted = True
    tr.status = "completed"
    tr.save(update_fields=["stock_posted", "status", "updated_at"])


def recalculate_adjustment_totals(adj: StockAdjustment) -> None:
    inc = Decimal("0")
    dec = Decimal("0")
    val = Decimal("0")
    amt = Decimal("0")
    for it in adj.items.all():
        it.save()
        d = it.quantity_difference
        if d > 0:
            inc += d
        elif d < 0:
            dec += abs(d)
        val += it.value_difference
        amt += it.line_total
    adj.total_increase = inc
    adj.total_decrease = dec
    adj.total_value = val
    adj.total_amount = amt
    adj.save(
        update_fields=[
            "total_increase",
            "total_decrease",
            "total_value",
            "total_amount",
            "updated_at",
        ]
    )
