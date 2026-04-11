from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class ProductionTimestampedModel(models.Model):
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_rows",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BillOfMaterial(ProductionTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    doc_no = models.CharField(max_length=50)
    product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="production_boms")
    version = models.CharField(max_length=20, default="1.0")
    bom_date = models.DateField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    total_component_cost = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["-bom_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return self.doc_no

    def recalc_totals(self):
        self.total_component_cost = sum((l.line_total for l in self.lines.all()), Decimal("0"))

    def clean(self):
        if self.product_id and self.product.tenant_id != self.tenant_id:
            raise ValidationError({"product": "Product must belong to same tenant."})


class BillOfMaterialLine(models.Model):
    bom = models.ForeignKey(BillOfMaterial, on_delete=models.CASCADE, related_name="lines")
    component_product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    warehouse = models.ForeignKey("foundation.Warehouse", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    scrap_percent = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("0"))
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.scrap_percent < 0:
            raise ValidationError({"scrap_percent": "Scrap % cannot be negative."})
        if self.unit_cost < 0:
            raise ValidationError({"unit_cost": "Unit cost cannot be negative."})
        if self.bom_id and self.component_product_id and self.component_product.tenant_id != self.bom.tenant_id:
            raise ValidationError({"component_product": "Component product must belong to same tenant."})
        if self.bom_id and self.warehouse_id and self.warehouse.tenant_id != self.bom.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})
        effective_qty = (self.quantity or Decimal("0")) * (Decimal("1") + (self.scrap_percent or Decimal("0")) / Decimal("100"))
        self.line_total = effective_qty * (self.unit_cost or Decimal("0"))


class ProductionOrder(ProductionTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        RELEASED = "released", "Released"
        IN_PROCESS = "in_process", "In process"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    doc_no = models.CharField(max_length=50)
    bom = models.ForeignKey(BillOfMaterial, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="production_orders")
    warehouse = models.ForeignKey("foundation.Warehouse", on_delete=models.PROTECT, related_name="production_orders")
    order_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    planned_quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    produced_quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["-order_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return self.doc_no

    def clean(self):
        if self.planned_quantity <= 0:
            raise ValidationError({"planned_quantity": "Planned quantity must be greater than zero."})
        if self.product_id and self.product.tenant_id != self.tenant_id:
            raise ValidationError({"product": "Product must belong to same tenant."})
        if self.warehouse_id and self.warehouse.tenant_id != self.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})
        if self.bom_id:
            if self.bom.tenant_id != self.tenant_id:
                raise ValidationError({"bom": "BOM must belong to same tenant."})
            if self.product_id and self.bom.product_id != self.product_id:
                raise ValidationError({"bom": "BOM product must match production order product."})


class ProductionOrderMaterial(models.Model):
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name="materials")
    component_product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    warehouse = models.ForeignKey("foundation.Warehouse", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    planned_quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    issued_quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    returned_quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.planned_quantity <= 0:
            raise ValidationError({"planned_quantity": "Planned quantity must be greater than zero."})
        if self.unit_cost < 0:
            raise ValidationError({"unit_cost": "Unit cost cannot be negative."})
        if self.production_order_id and self.component_product_id and self.component_product.tenant_id != self.production_order.tenant_id:
            raise ValidationError({"component_product": "Component product must belong to same tenant."})
        if self.production_order_id and self.warehouse_id and self.warehouse.tenant_id != self.production_order.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})
        self.line_total = (self.planned_quantity or Decimal("0")) * (self.unit_cost or Decimal("0"))


class IssueForProduction(ProductionTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    doc_no = models.CharField(max_length=50)
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.PROTECT, related_name="issues")
    issue_date = models.DateField()
    warehouse = models.ForeignKey("foundation.Warehouse", on_delete=models.PROTECT, related_name="production_issues")
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["-issue_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return self.doc_no

    def recalc_totals(self):
        self.total_amount = sum((l.line_total for l in self.lines.all()), Decimal("0"))

    def clean(self):
        if self.production_order_id and self.production_order.tenant_id != self.tenant_id:
            raise ValidationError({"production_order": "Production order must belong to same tenant."})
        if self.warehouse_id and self.warehouse.tenant_id != self.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})


class IssueForProductionLine(models.Model):
    issue = models.ForeignKey(IssueForProduction, on_delete=models.CASCADE, related_name="lines")
    order_material = models.ForeignKey(
        ProductionOrderMaterial, null=True, blank=True, on_delete=models.SET_NULL, related_name="issue_lines"
    )
    component_product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Issue quantity must be greater than zero."})
        if self.unit_cost < 0:
            raise ValidationError({"unit_cost": "Unit cost cannot be negative."})
        if self.issue_id and self.component_product_id and self.component_product.tenant_id != self.issue.tenant_id:
            raise ValidationError({"component_product": "Component product must belong to same tenant."})
        if self.issue_id and self.order_material_id and self.order_material.production_order_id != self.issue.production_order_id:
            raise ValidationError({"order_material": "Order material must belong to selected production order."})
        self.line_total = (self.quantity or Decimal("0")) * (self.unit_cost or Decimal("0"))


class ReceiptFromProduction(ProductionTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    doc_no = models.CharField(max_length=50)
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.PROTECT, related_name="receipts")
    receipt_date = models.DateField()
    warehouse = models.ForeignKey("foundation.Warehouse", on_delete=models.PROTECT, related_name="production_receipts")
    quantity_received = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["-receipt_date", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return self.doc_no

    def clean(self):
        if self.quantity_received <= 0:
            raise ValidationError({"quantity_received": "Receipt quantity must be greater than zero."})
        if self.unit_cost < 0:
            raise ValidationError({"unit_cost": "Unit cost cannot be negative."})
        if self.production_order_id and self.production_order.tenant_id != self.tenant_id:
            raise ValidationError({"production_order": "Production order must belong to same tenant."})
        if self.warehouse_id and self.warehouse.tenant_id != self.tenant_id:
            raise ValidationError({"warehouse": "Warehouse must belong to same tenant."})
        self.total_amount = (self.quantity_received or Decimal("0")) * (self.unit_cost or Decimal("0"))

