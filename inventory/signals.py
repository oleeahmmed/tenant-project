"""Inventory posting signals: enforce stock + transaction history by status transitions."""

from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import GoodsIssue, InventoryTransfer, StockAdjustment
from .services.stock import (
    post_goods_issue,
    post_inventory_transfer,
    post_stock_adjustment,
    reverse_document_transactions,
)


@receiver(pre_save, sender=StockAdjustment)
def _sa_pre_save(sender, instance: StockAdjustment, **kwargs):
    instance._old_status = None
    if instance.pk:
        instance._old_status = (
            sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
        )


@receiver(post_save, sender=StockAdjustment)
def _sa_post_save(sender, instance: StockAdjustment, **kwargs):
    old_status = getattr(instance, "_old_status", None)
    if instance.status == "posted" and old_status != "posted":
        transaction.on_commit(lambda: post_stock_adjustment(instance))
    elif old_status == "posted" and instance.status != "posted":
        transaction.on_commit(
            lambda: reverse_document_transactions(
                tenant_id=instance.tenant_id,
                source_document_type="stock_adjustment",
                source_document_id=instance.pk,
            )
        )


@receiver(pre_save, sender=GoodsIssue)
def _gi_pre_save(sender, instance: GoodsIssue, **kwargs):
    instance._old_status = None
    if instance.pk:
        row = sender.objects.filter(pk=instance.pk).values("status", "stock_posted").first()
        if row:
            instance._old_status = row["status"]
            instance._old_stock_posted = row["stock_posted"]


@receiver(post_save, sender=GoodsIssue)
def _gi_post_save(sender, instance: GoodsIssue, **kwargs):
    old_status = getattr(instance, "_old_status", None)
    old_posted = getattr(instance, "_old_stock_posted", False)
    if instance.status == "released" and (old_status != "released" or not old_posted):
        transaction.on_commit(lambda: post_goods_issue(instance))
    elif old_status == "released" and instance.status != "released" and old_posted:
        def _reverse_gi():
            reverse_document_transactions(
                tenant_id=instance.tenant_id,
                source_document_type="goods_issue",
                source_document_id=instance.pk,
            )
            sender.objects.filter(pk=instance.pk).update(stock_posted=False)

        transaction.on_commit(_reverse_gi)


@receiver(pre_save, sender=InventoryTransfer)
def _it_pre_save(sender, instance: InventoryTransfer, **kwargs):
    instance._old_status = None
    if instance.pk:
        row = sender.objects.filter(pk=instance.pk).values("status", "stock_posted").first()
        if row:
            instance._old_status = row["status"]
            instance._old_stock_posted = row["stock_posted"]


@receiver(post_save, sender=InventoryTransfer)
def _it_post_save(sender, instance: InventoryTransfer, **kwargs):
    old_status = getattr(instance, "_old_status", None)
    old_posted = getattr(instance, "_old_stock_posted", False)
    if instance.status == "completed" and (old_status != "completed" or not old_posted):
        transaction.on_commit(lambda: post_inventory_transfer(instance))
    elif old_status == "completed" and instance.status != "completed" and old_posted:
        def _reverse_it():
            reverse_document_transactions(
                tenant_id=instance.tenant_id,
                source_document_type="inventory_transfer",
                source_document_id=instance.pk,
            )
            sender.objects.filter(pk=instance.pk).update(stock_posted=False)

        transaction.on_commit(_reverse_it)
