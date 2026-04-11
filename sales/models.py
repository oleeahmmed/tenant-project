from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class SalesTimestampedModel(models.Model):
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_rows",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SalesQuotation(SalesTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        CANCELLED = "cancelled", "Cancelled"

    doc_no = models.CharField(max_length=50)
    customer = models.ForeignKey("foundation.Customer", on_delete=models.PROTECT, related_name="sales_quotations")
    quote_date = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    subtotal = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["-quote_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return self.doc_no

    def recalc_totals(self):
        self.subtotal = sum((l.line_total for l in self.lines.all()), Decimal("0"))
        self.total_amount = self.subtotal + (self.tax_amount or Decimal("0"))


class SalesQuotationLine(models.Model):
    quotation = models.ForeignKey(SalesQuotation, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    warehouse = models.ForeignKey("foundation.Warehouse", null=True, blank=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    unit_price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.unit_price < 0:
            raise ValidationError({"unit_price": "Unit price cannot be negative."})
        if self.quotation_id and self.product_id and self.product.tenant_id != self.quotation.tenant_id:
            raise ValidationError({"product": "Product must belong to same tenant."})
        if self.quotation_id and self.warehouse_id and self.warehouse.tenant_id != self.quotation.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})
        self.line_total = (self.quantity or Decimal("0")) * (self.unit_price or Decimal("0"))


class SalesOrder(SalesTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    doc_no = models.CharField(max_length=50)
    customer = models.ForeignKey("foundation.Customer", on_delete=models.PROTECT, related_name="sales_orders")
    quotation = models.ForeignKey(SalesQuotation, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    order_date = models.DateField()
    expected_delivery = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    subtotal = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["-order_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return self.doc_no

    def recalc_totals(self):
        self.subtotal = sum((l.line_total for l in self.lines.all()), Decimal("0"))
        self.total_amount = self.subtotal + (self.tax_amount or Decimal("0"))


class SalesOrderLine(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    warehouse = models.ForeignKey("foundation.Warehouse", null=True, blank=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    unit_price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.unit_price < 0:
            raise ValidationError({"unit_price": "Unit price cannot be negative."})
        if self.order_id and self.product_id and self.product.tenant_id != self.order.tenant_id:
            raise ValidationError({"product": "Product must belong to same tenant."})
        if self.order_id and self.warehouse_id and self.warehouse.tenant_id != self.order.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})
        self.line_total = (self.quantity or Decimal("0")) * (self.unit_price or Decimal("0"))


class DeliveryNote(SalesTimestampedModel):
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
    order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name="deliveries")
    customer = models.ForeignKey("foundation.Customer", on_delete=models.PROTECT, related_name="delivery_notes")
    delivery_date = models.DateField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    finance_ar_invoice = models.ForeignKey(
        "finance.ARInvoice", null=True, blank=True, on_delete=models.SET_NULL, related_name="source_delivery_notes"
    )
    finance_sync_status = models.CharField(max_length=20, choices=FinanceSyncStatus.choices, default=FinanceSyncStatus.PENDING)
    finance_sync_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-delivery_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return self.doc_no

    def recalc_totals(self):
        self.total_amount = sum((l.line_total for l in self.lines.all()), Decimal("0"))

    def clean(self):
        if self.order_id and self.customer_id and self.order.customer_id != self.customer_id:
            raise ValidationError({"customer": "Customer must match selected sales order."})
        if self.order_id and self.order.tenant_id != self.tenant_id:
            raise ValidationError({"order": "Sales order must belong to same tenant."})


class DeliveryNoteLine(models.Model):
    delivery = models.ForeignKey(DeliveryNote, on_delete=models.CASCADE, related_name="lines")
    order_line = models.ForeignKey(SalesOrderLine, null=True, blank=True, on_delete=models.SET_NULL, related_name="delivery_lines")
    product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    warehouse = models.ForeignKey("foundation.Warehouse", null=True, blank=True, on_delete=models.PROTECT)
    quantity_delivered = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    unit_price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.quantity_delivered <= 0:
            raise ValidationError({"quantity_delivered": "Delivered quantity must be greater than zero."})
        if self.unit_price < 0:
            raise ValidationError({"unit_price": "Unit price cannot be negative."})
        if self.delivery_id and self.product_id and self.product.tenant_id != self.delivery.tenant_id:
            raise ValidationError({"product": "Product must belong to same tenant."})
        if self.delivery_id and self.warehouse_id and self.warehouse.tenant_id != self.delivery.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})
        if self.delivery_id and self.order_line_id and self.order_line.order_id != self.delivery.order_id:
            raise ValidationError({"order_line": "Selected sales order line is not from this order."})
        self.line_total = (self.quantity_delivered or Decimal("0")) * (self.unit_price or Decimal("0"))


class SalesReturn(SalesTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    doc_no = models.CharField(max_length=50)
    customer = models.ForeignKey("foundation.Customer", on_delete=models.PROTECT, related_name="sales_returns")
    delivery = models.ForeignKey(DeliveryNote, null=True, blank=True, on_delete=models.SET_NULL, related_name="returns")
    return_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["-return_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return self.doc_no

    def recalc_totals(self):
        self.total_amount = sum((l.line_total for l in self.lines.all()), Decimal("0"))

    def clean(self):
        if self.delivery_id and self.delivery.tenant_id != self.tenant_id:
            raise ValidationError({"delivery": "Delivery note must belong to same tenant."})
        if self.delivery_id and self.customer_id and self.delivery.customer_id != self.customer_id:
            raise ValidationError({"customer": "Customer must match selected delivery note."})


class SalesReturnLine(models.Model):
    sales_return = models.ForeignKey(SalesReturn, on_delete=models.CASCADE, related_name="lines")
    delivery_line = models.ForeignKey(DeliveryNoteLine, null=True, blank=True, on_delete=models.SET_NULL, related_name="return_lines")
    product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    warehouse = models.ForeignKey("foundation.Warehouse", null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    unit_price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Return quantity must be greater than zero."})
        if self.unit_price < 0:
            raise ValidationError({"unit_price": "Unit price cannot be negative."})
        if self.sales_return_id and self.product_id and self.product.tenant_id != self.sales_return.tenant_id:
            raise ValidationError({"product": "Product must belong to same tenant."})
        if self.sales_return_id and self.warehouse_id and self.warehouse.tenant_id != self.sales_return.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})
        if self.sales_return_id and self.delivery_line_id and self.sales_return.delivery_id and self.delivery_line.delivery_id != self.sales_return.delivery_id:
            raise ValidationError({"delivery_line": "Selected delivery line is not from this delivery note."})
        self.line_total = (self.quantity or Decimal("0")) * (self.unit_price or Decimal("0"))

