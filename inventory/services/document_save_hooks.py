"""Stock posting side effects for inventory documents.

Invoked from ``StockAdjustment``, ``GoodsIssue``, and ``InventoryTransfer`` ``save()``
after ``super().save()`` so behavior stays on the model instead of global signals.

Bulk updates (``QuerySet.update``) still bypass these hooks—same as with signals.
"""

from __future__ import annotations

from django.db import transaction

from .stock import (
    post_goods_issue,
    post_inventory_transfer,
    post_stock_adjustment,
    reverse_document_transactions,
)


def schedule_stock_adjustment_posting(instance, *, old_status: str | None) -> None:
    if instance.status == "posted" and old_status != "posted":
        transaction.on_commit(lambda inst=instance: post_stock_adjustment(inst))
    elif old_status == "posted" and instance.status != "posted":
        tid, doc_id = instance.tenant_id, instance.pk
        transaction.on_commit(
            lambda: reverse_document_transactions(
                tenant_id=tid,
                source_document_type="stock_adjustment",
                source_document_id=doc_id,
            )
        )


def schedule_goods_issue_posting(instance, *, old_status: str | None, old_stock_posted: bool) -> None:
    if instance.status == "released" and (old_status != "released" or not old_stock_posted):
        transaction.on_commit(lambda inst=instance: post_goods_issue(inst))
    elif old_status == "released" and instance.status != "released" and old_stock_posted:
        cls = instance.__class__
        pk, tid = instance.pk, instance.tenant_id

        def _reverse():
            reverse_document_transactions(
                tenant_id=tid,
                source_document_type="goods_issue",
                source_document_id=pk,
            )
            cls.objects.filter(pk=pk).update(stock_posted=False)

        transaction.on_commit(_reverse)


def schedule_inventory_transfer_posting(instance, *, old_status: str | None, old_stock_posted: bool) -> None:
    if instance.status == "completed" and (old_status != "completed" or not old_stock_posted):
        transaction.on_commit(lambda inst=instance: post_inventory_transfer(inst))
    elif old_status == "completed" and instance.status != "completed" and old_stock_posted:
        cls = instance.__class__
        pk, tid = instance.pk, instance.tenant_id

        def _reverse():
            reverse_document_transactions(
                tenant_id=tid,
                source_document_type="inventory_transfer",
                source_document_id=pk,
            )
            cls.objects.filter(pk=pk).update(stock_posted=False)

        transaction.on_commit(_reverse)
