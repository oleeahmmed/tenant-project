from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class PurchaseTimestampedModel(models.Model):
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_rows",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PurchaseRequest(PurchaseTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        CANCELLED = "cancelled", "Cancelled"

    doc_no = models.CharField(max_length=50)
    requester_name = models.CharField(max_length=120, blank=True)
    request_date = models.DateField()
    needed_by = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["-request_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return f"{self.doc_no}"


class PurchaseRequestLine(models.Model):
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.request_id and self.product_id and self.product.tenant_id != self.request.tenant_id:
            raise ValidationError({"product": "Product must belong to same tenant."})


class PurchaseOrder(PurchaseTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    doc_no = models.CharField(max_length=50)
    supplier = models.ForeignKey("foundation.Supplier", on_delete=models.PROTECT, related_name="purchase_orders")
    purchase_request = models.ForeignKey(
        PurchaseRequest, null=True, blank=True, on_delete=models.SET_NULL, related_name="purchase_orders"
    )
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    subtotal = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["-order_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return f"{self.doc_no}"

    def recalc_totals(self):
        subtotal = sum((l.line_total for l in self.lines.all()), Decimal("0"))
        self.subtotal = subtotal
        self.total_amount = subtotal + (self.tax_amount or Decimal("0"))


class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    warehouse = models.ForeignKey("foundation.Warehouse", null=True, blank=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.unit_cost < 0:
            raise ValidationError({"unit_cost": "Unit cost cannot be negative."})
        if self.purchase_order_id and self.product_id and self.product.tenant_id != self.purchase_order.tenant_id:
            raise ValidationError({"product": "Product must belong to same tenant."})
        if self.purchase_order_id and self.warehouse_id and self.warehouse.tenant_id != self.purchase_order.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})
        self.line_total = (self.quantity or Decimal("0")) * (self.unit_cost or Decimal("0"))


class GoodsReceipt(PurchaseTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    class FinanceSyncStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SYNCED = "synced", "Synced"
        SKIPPED = "skipped", "Skipped"
        ERROR = "error", "Error"

    doc_no = models.CharField(max_length=50)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="receipts")
    supplier = models.ForeignKey("foundation.Supplier", on_delete=models.PROTECT, related_name="goods_receipts")
    receipt_date = models.DateField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    finance_ap_invoice = models.ForeignKey(
        "finance.APInvoice", null=True, blank=True, on_delete=models.SET_NULL, related_name="source_goods_receipts"
    )
    finance_sync_status = models.CharField(
        max_length=20, choices=FinanceSyncStatus.choices, default=FinanceSyncStatus.PENDING
    )
    finance_sync_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-receipt_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return f"{self.doc_no}"

    def recalc_totals(self):
        self.total_amount = sum((l.line_total for l in self.lines.all()), Decimal("0"))

    def clean(self):
        if self.purchase_order_id and self.supplier_id and self.purchase_order.supplier_id != self.supplier_id:
            raise ValidationError({"supplier": "Supplier must match selected purchase order."})
        if self.purchase_order_id and self.purchase_order.tenant_id != self.tenant_id:
            raise ValidationError({"purchase_order": "Purchase order must belong to same tenant."})


class GoodsReceiptLine(models.Model):
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="lines")
    purchase_order_line = models.ForeignKey(
        PurchaseOrderLine, null=True, blank=True, on_delete=models.SET_NULL, related_name="receipt_lines"
    )
    product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    warehouse = models.ForeignKey("foundation.Warehouse", null=True, blank=True, on_delete=models.PROTECT)
    quantity_received = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.quantity_received <= 0:
            raise ValidationError({"quantity_received": "Received quantity must be greater than zero."})
        if self.unit_cost < 0:
            raise ValidationError({"unit_cost": "Unit cost cannot be negative."})
        if self.receipt_id and self.product_id and self.product.tenant_id != self.receipt.tenant_id:
            raise ValidationError({"product": "Product must belong to same tenant."})
        if self.receipt_id and self.warehouse_id and self.warehouse.tenant_id != self.receipt.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})
        if (
            self.receipt_id
            and self.purchase_order_line_id
            and self.purchase_order_line.purchase_order_id != self.receipt.purchase_order_id
        ):
            raise ValidationError({"purchase_order_line": "Selected PO line is not from this purchase order."})
        self.line_total = (self.quantity_received or Decimal("0")) * (self.unit_cost or Decimal("0"))


class PurchaseReturn(PurchaseTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    doc_no = models.CharField(max_length=50)
    supplier = models.ForeignKey("foundation.Supplier", on_delete=models.PROTECT, related_name="purchase_returns")
    goods_receipt = models.ForeignKey(
        GoodsReceipt, null=True, blank=True, on_delete=models.SET_NULL, related_name="returns"
    )
    return_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["-return_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return f"{self.doc_no}"

    def recalc_totals(self):
        self.total_amount = sum((l.line_total for l in self.lines.all()), Decimal("0"))

    def clean(self):
        if self.goods_receipt_id and self.goods_receipt.tenant_id != self.tenant_id:
            raise ValidationError({"goods_receipt": "Goods receipt must belong to same tenant."})
        if self.goods_receipt_id and self.supplier_id and self.goods_receipt.supplier_id != self.supplier_id:
            raise ValidationError({"supplier": "Supplier must match selected goods receipt."})


class PurchaseReturnLine(models.Model):
    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name="lines")
    goods_receipt_line = models.ForeignKey(
        GoodsReceiptLine, null=True, blank=True, on_delete=models.SET_NULL, related_name="return_lines"
    )
    product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    warehouse = models.ForeignKey("foundation.Warehouse", null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Return quantity must be greater than zero."})
        if self.unit_cost < 0:
            raise ValidationError({"unit_cost": "Unit cost cannot be negative."})
        if self.purchase_return_id and self.product_id and self.product.tenant_id != self.purchase_return.tenant_id:
            raise ValidationError({"product": "Product must belong to same tenant."})
        if self.purchase_return_id and self.warehouse_id and self.warehouse.tenant_id != self.purchase_return.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})
        if (
            self.purchase_return_id
            and self.goods_receipt_line_id
            and self.purchase_return.goods_receipt_id
            and self.goods_receipt_line.receipt_id != self.purchase_return.goods_receipt_id
        ):
            raise ValidationError({"goods_receipt_line": "Selected GRN line is not from this goods receipt."})
        self.line_total = (self.quantity or Decimal("0")) * (self.unit_cost or Decimal("0"))

