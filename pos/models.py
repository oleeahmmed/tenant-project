from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class TenantScopedModel(models.Model):
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_rows",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class POSRegister(TenantScopedModel):
    """A physical register / counter (links to default warehouse for stock)."""

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    default_warehouse = models.ForeignKey(
        "foundation.Warehouse",
        on_delete=models.PROTECT,
        related_name="pos_registers",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} — {self.name}"

    def clean(self):
        # Skip until tenant is set (CreateView sets tenant in form_valid after first validation pass).
        if self.tenant_id and self.default_warehouse_id and self.default_warehouse.tenant_id != self.tenant_id:
            raise ValidationError({"default_warehouse": "Warehouse must belong to the same tenant."})


class POSSession(models.Model):
    """Shift session: open register, take sales, close with cash count."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    register = models.ForeignKey(POSRegister, on_delete=models.CASCADE, related_name="sessions")
    opened_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="pos_sessions_opened")
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pos_sessions_closed",
    )
    opening_cash = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    closing_cash = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    expected_cash = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Opening + cash sales (computed on close).",
    )
    cash_difference = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self):
        return f"{self.register.code} @ {self.opened_at:%Y-%m-%d %H:%M}"


class POSSale(TenantScopedModel):
    """A retail ticket (POS sale)."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        COMPLETED = "completed", "Completed"
        VOID = "void", "Void"

    session = models.ForeignKey(POSSession, on_delete=models.PROTECT, related_name="sales")
    doc_no = models.CharField(max_length=50)
    sale_datetime = models.DateTimeField(default=timezone.now)
    customer = models.ForeignKey(
        "foundation.Customer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pos_sales",
    )
    warehouse = models.ForeignKey(
        "foundation.Warehouse",
        on_delete=models.PROTECT,
        related_name="pos_sales",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    subtotal = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    discount_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="pos_sales_created")

    class Meta:
        ordering = ["-sale_datetime", "-id"]
        unique_together = [("tenant", "doc_no")]

    def __str__(self):
        return self.doc_no

    def recalc_totals(self):
        self.subtotal = sum((l.line_total for l in self.lines.all()), Decimal("0"))
        self.total_amount = self.subtotal + (self.tax_amount or Decimal("0")) - (self.discount_amount or Decimal("0"))


class POSSaleLine(models.Model):
    sale = models.ForeignKey(POSSale, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("foundation.Product", on_delete=models.PROTECT, related_name="+")
    product_variant = models.ForeignKey(
        "foundation.ProductVariant",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )
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
        if self.sale_id and self.product_id and self.product.tenant_id != self.sale.tenant_id:
            raise ValidationError({"product": "Product must belong to same tenant."})
        self.line_total = (self.quantity or Decimal("0")) * (self.unit_price or Decimal("0"))


class POSPayment(models.Model):
    sale = models.ForeignKey(POSSale, on_delete=models.CASCADE, related_name="payments")
    payment_method = models.ForeignKey(
        "foundation.PaymentMethod",
        on_delete=models.PROTECT,
        related_name="pos_payments",
    )
    amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    reference = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["id"]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({"amount": "Amount must be positive."})
        if self.payment_method_id and self.sale_id:
            if self.payment_method.tenant_id != self.sale.tenant_id:
                raise ValidationError({"payment_method": "Payment method must belong to same tenant."})


def allocate_pos_doc_no(tenant) -> str:
    """Unique POS doc number per tenant per day."""
    d = timezone.now().date()
    prefix = f"POS-{d.strftime('%Y%m%d')}"
    n = POSSale.objects.filter(tenant=tenant, doc_no__startswith=prefix).count() + 1
    return f"{prefix}-{n:04d}"
