"""Tenant-scoped inventory: SAP Business One–style documents (header + lines) and stock ledger."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def _next_document_number(tenant_id: int, model_cls, field_name: str, prefix: str) -> str:
    """Sequential number per tenant: PREFIX-000001."""
    qs = model_cls.objects.filter(tenant_id=tenant_id).values_list(field_name, flat=True)
    max_n = 0
    for val in qs:
        if not val or not str(val).startswith(prefix):
            continue
        try:
            max_n = max(max_n, int(str(val).split("-")[-1]))
        except ValueError:
            pass
    return f"{prefix}-{max_n + 1:06d}"


# ── Warehouse stock (aggregate) ─────────────────────────────────────────────────


class WarehouseStock(models.Model):
    """On-hand quantity per product per warehouse (same tenant as product/warehouse)."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="inventory_warehouse_stocks",
    )
    product = models.ForeignKey(
        "foundation.Product",
        on_delete=models.CASCADE,
        related_name="inventory_warehouse_stocks",
    )
    warehouse = models.ForeignKey(
        "foundation.Warehouse",
        on_delete=models.CASCADE,
        related_name="inventory_warehouse_stocks",
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"))
    min_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Optional reorder / minimum stock level for this warehouse.",
    )
    max_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Optional maximum stock target for this warehouse.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant", "product", "warehouse")]
        ordering = ["warehouse", "product"]
        verbose_name = "Warehouse stock"
        verbose_name_plural = "Warehouse stock"

    def __str__(self):
        return f"{self.product} @ {self.warehouse.code}: {self.quantity}"


# ── Stock ledger ─────────────────────────────────────────────────────────────


class StockTransaction(models.Model):
    """Immutable log of every quantity movement (audit trail)."""

    TRANSACTION_TYPES = [
        ("in", "Stock In"),
        ("out", "Stock Out"),
        ("adjustment", "Adjustment"),
        ("transfer_out", "Transfer Out"),
        ("transfer_in", "Transfer In"),
    ]

    SOURCE_TYPES = [
        ("stock_adjustment", "Stock adjustment"),
        ("goods_issue", "Goods issue"),
        ("inventory_transfer", "Inventory transfer"),
        ("manual", "Manual / opening"),
    ]

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="inventory_stock_transactions",
    )
    product = models.ForeignKey(
        "foundation.Product",
        on_delete=models.PROTECT,
        related_name="inventory_stock_transactions",
    )
    product_variant = models.ForeignKey(
        "foundation.ProductVariant",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="inventory_stock_transactions",
    )
    warehouse = models.ForeignKey(
        "foundation.Warehouse",
        on_delete=models.PROTECT,
        related_name="inventory_stock_transactions",
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        help_text="Absolute quantity moved in the direction of transaction_type.",
    )
    qty_signed = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        help_text="Signed change to on-hand stock (+ increase, − decrease).",
    )
    balance_after = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"))
    source_document_type = models.CharField(max_length=40, choices=SOURCE_TYPES, blank=True)
    source_document_id = models.PositiveIntegerField(null=True, blank=True)
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Stock transaction"
        verbose_name_plural = "Stock transactions"

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.product} {self.qty_signed}"


# ── Stock adjustment (header + lines) ──────────────────────────────────────────


class StockAdjustment(models.Model):
    """
    Document header stores **warehouse_code** + **warehouse_name** (text snapshot), not an FK.
    Matches SAP B1–style inventory documents: fast listing, stable labels on print/history,
    posting resolves rows via code/SKU against master data.
    """

    ADJUSTMENT_TYPES = [
        ("opening", "Opening stock"),
        ("physical_count", "Physical count"),
        ("damage", "Damage / loss"),
        ("correction", "Correction"),
        ("write_off", "Write-off"),
        ("found", "Found / recovered"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("posted", "Posted"),
        ("cancelled", "Cancelled"),
    ]

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="inventory_stock_adjustments",
    )
    adjustment_number = models.CharField(max_length=50, editable=False)
    adjustment_date = models.DateField(default=timezone.localdate)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES, default="physical_count")
    warehouse_code = models.CharField(
        max_length=50,
        db_index=True,
        blank=True,
        default="",
        help_text="Warehouse code (snapshot; validated against master at save/post).",
    )
    warehouse_name = models.CharField(max_length=200, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    reason = models.TextField(blank=True)
    requested_by = models.CharField(max_length=120, blank=True)
    total_increase = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"), editable=False)
    total_decrease = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"), editable=False)
    total_value = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"), editable=False)
    total_amount = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        default=Decimal("0"),
        editable=False,
        help_text="Sum of absolute line value impacts (|Δqty| × unit cost).",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-adjustment_date", "-id"]
        unique_together = [("tenant", "adjustment_number")]

    def __str__(self):
        return f"{self.adjustment_number} - {self.get_adjustment_type_display()}"

    def save(self, *args, **kwargs):
        if not self.adjustment_number:
            self.adjustment_number = _next_document_number(
                self.tenant_id, StockAdjustment, "adjustment_number", "ADJ"
            )
        super().save(*args, **kwargs)


class StockAdjustmentItem(models.Model):
    """Line stores **product_sku** + **product_name** snapshot; posting resolves Product by SKU."""

    stock_adjustment = models.ForeignKey(
        StockAdjustment,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product_sku = models.CharField(
        max_length=100,
        db_index=True,
        blank=True,
        default="",
        help_text="Product SKU (snapshot; validated against master at save/post).",
    )
    product_name = models.CharField(max_length=255, blank=True, default="")
    system_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        default=Decimal("0"),
        editable=False,
    )
    counted_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        default=Decimal("0"),
        help_text="Physical count or new quantity after adjustment.",
    )
    quantity_difference = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"), editable=False)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"))
    value_difference = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"), editable=False)
    line_total = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        default=Decimal("0"),
        editable=False,
        help_text="|Quantity difference| × unit cost.",
    )
    line_reason = models.CharField(max_length=200, blank=True)
    line_no = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["line_no", "id"]

    def __str__(self):
        return f"{self.stock_adjustment.adjustment_number} - {self.product_sku}"

    def save(self, *args, **kwargs):
        from foundation.models import Product, Warehouse
        from inventory.services.stock import get_product_warehouse_qty

        self.system_quantity = Decimal("0")
        if self.stock_adjustment_id and self.product_sku:
            adj = self.stock_adjustment
            wh = (
                Warehouse.objects.filter(
                    tenant_id=adj.tenant_id, code=adj.warehouse_code.strip()
                ).first()
                if adj.warehouse_code
                else None
            )
            prod = Product.objects.filter(
                tenant_id=adj.tenant_id, sku=self.product_sku.strip()
            ).first()
            if wh and prod:
                self.system_quantity = get_product_warehouse_qty(
                    adj.tenant_id, prod.id, wh.id
                )
        self.quantity_difference = self.counted_quantity - self.system_quantity
        self.value_difference = self.quantity_difference * self.unit_cost
        self.line_total = abs(self.value_difference)
        super().save(*args, **kwargs)


# ── Goods issue ────────────────────────────────────────────────────────────────


class GoodsIssue(models.Model):
    ISSUE_TYPES = [
        ("sales", "Sales / delivery"),
        ("production", "Production"),
        ("transfer", "Transfer out"),
        ("damage", "Damage / loss"),
        ("internal", "Internal use"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("released", "Released"),
        ("cancelled", "Cancelled"),
    ]

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="inventory_goods_issues",
    )
    issue_number = models.CharField(max_length=50, editable=False)
    issue_date = models.DateField(default=timezone.localdate)
    issue_type = models.CharField(max_length=20, choices=ISSUE_TYPES, default="sales")
    warehouse = models.ForeignKey(
        "foundation.Warehouse",
        on_delete=models.PROTECT,
        related_name="inventory_goods_issues",
    )
    customer = models.ForeignKey(
        "foundation.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_goods_issues",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    reference = models.CharField(max_length=120, blank=True)
    issued_to = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    stock_posted = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date", "-id"]
        unique_together = [("tenant", "issue_number")]

    def __str__(self):
        return f"{self.issue_number} - {self.warehouse}"

    def save(self, *args, **kwargs):
        if not self.issue_number:
            self.issue_number = _next_document_number(self.tenant_id, GoodsIssue, "issue_number", "GI")
        super().save(*args, **kwargs)


class GoodsIssueItem(models.Model):
    goods_issue = models.ForeignKey(GoodsIssue, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "foundation.Product",
        on_delete=models.PROTECT,
        related_name="inventory_goods_issue_items",
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("1"))
    unit_cost = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"), editable=False)
    line_no = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["line_no", "id"]

    def __str__(self):
        return f"{self.goods_issue.issue_number} - {self.product}"

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_cost
        super().save(*args, **kwargs)


# ── Inventory transfer ──────────────────────────────────────────────────────────


class InventoryTransfer(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="inventory_transfers",
    )
    transfer_number = models.CharField(max_length=50, editable=False)
    transfer_date = models.DateField(default=timezone.localdate)
    from_warehouse = models.ForeignKey(
        "foundation.Warehouse",
        on_delete=models.PROTECT,
        related_name="inventory_transfers_out",
    )
    to_warehouse = models.ForeignKey(
        "foundation.Warehouse",
        on_delete=models.PROTECT,
        related_name="inventory_transfers_in",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    stock_posted = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-transfer_date", "-id"]
        unique_together = [("tenant", "transfer_number")]

    def __str__(self):
        return f"{self.transfer_number} - {self.from_warehouse} → {self.to_warehouse}"

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            self.transfer_number = _next_document_number(
                self.tenant_id, InventoryTransfer, "transfer_number", "IT"
            )
        super().save(*args, **kwargs)

    def clean(self):
        if self.from_warehouse_id and self.to_warehouse_id and self.from_warehouse_id == self.to_warehouse_id:
            raise ValidationError({"to_warehouse": "From and to warehouse must differ."})


class InventoryTransferItem(models.Model):
    inventory_transfer = models.ForeignKey(
        InventoryTransfer,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "foundation.Product",
        on_delete=models.PROTECT,
        related_name="inventory_transfer_items",
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("1"))
    unit_cost = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"), editable=False)
    line_no = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["line_no", "id"]

    def __str__(self):
        return f"{self.inventory_transfer.transfer_number} - {self.product}"

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
