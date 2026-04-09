"""Tenant-scoped ERP / POS / inventory master data."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Warehouse(models.Model):
    """Storage / fulfillment location for stock."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_warehouses",
    )
    code = models.CharField(max_length=50, help_text="Short code, unique within the workspace.")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} — {self.name}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.code:
            self.code = self.code.strip()
        if not self.code:
            raise ValidationError({"code": "Code is required."})


class Category(models.Model):
    """Product category (optional hierarchy)."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_categories",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} — {self.name}"


class UnitOfMeasure(models.Model):
    """Unit of measure (PCS, KG, L, …)."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_uoms",
    )
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    decimal_places = models.PositiveSmallIntegerField(
        default=0,
        help_text="Decimal places allowed for quantities in this UOM.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        unique_together = [("tenant", "code")]
        verbose_name = "Unit of measure"
        verbose_name_plural = "Units of measure"

    def __str__(self):
        return f"{self.code} ({self.name})"


class Product(models.Model):
    """Sellable / stockable product master."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_products",
    )
    sku = models.CharField(max_length=100, help_text="Stock keeping unit — unique per workspace.")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    default_uom = models.ForeignKey(
        UnitOfMeasure,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products_default_uom",
    )
    default_unit_cost = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        default=Decimal("0"),
        help_text="Default inventory / standard cost per unit (used on documents).",
    )
    list_price = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        default=Decimal("0"),
        help_text="Suggested selling price per unit (reference).",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "sku")]

    def __str__(self):
        return f"{self.sku} — {self.name}"


class ProductVariant(models.Model):
    """SKU variant (size / color / style) for per-warehouse variant stock."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_product_variants",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    code = models.CharField(
        max_length=100,
        help_text="Variant code — unique per workspace (e.g. SKU-RED-M).",
    )
    name = models.CharField(max_length=255, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["product", "code"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        if self.name:
            return f"{self.product.sku} / {self.code} — {self.name}"
        return f"{self.product.sku} / {self.code}"


class UomConversion(models.Model):
    """Convert quantity from one UOM to another (same tenant)."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_uom_conversions",
    )
    from_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.CASCADE,
        related_name="conversion_sources",
    )
    to_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.CASCADE,
        related_name="conversion_targets",
    )
    factor = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        help_text="Multiply quantity in from_uom by this factor to get to_uom.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["from_uom__code", "to_uom__code"]
        unique_together = [("tenant", "from_uom", "to_uom")]

    def __str__(self):
        return f"{self.from_uom.code} → {self.to_uom.code} (×{self.factor})"

    def clean(self):
        if self.from_uom_id and self.to_uom_id and self.from_uom_id == self.to_uom_id:
            raise ValidationError({"to_uom": "From and to UOM must differ."})
        if self.factor is not None and self.factor <= 0:
            raise ValidationError({"factor": "Factor must be positive."})


class Customer(models.Model):
    """Sold-to party."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_customers",
    )
    customer_code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "customer_code")]

    def __str__(self):
        return f"{self.customer_code} — {self.name}"


class Supplier(models.Model):
    """Vendor / buy-from party."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_suppliers",
    )
    supplier_code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "supplier_code")]

    def __str__(self):
        return f"{self.supplier_code} — {self.name}"


class SalesPerson(models.Model):
    """Sales rep for orders and commissions."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_sales_persons",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} — {self.name}"


class PaymentMethod(models.Model):
    """Cash, card, bank transfer, mobile wallet, …"""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_payment_methods",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Currency(models.Model):
    """Currency master (ISO-style code per workspace)."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_currencies",
    )
    code = models.CharField(max_length=3, help_text="e.g. USD, BDT")
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} ({self.name})"


class ExchangeRate(models.Model):
    """1 unit of from_currency = rate units of to_currency."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_exchange_rates",
    )
    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="exchange_rates_from",
    )
    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="exchange_rates_to",
    )
    rate = models.DecimalField(max_digits=18, decimal_places=8)
    effective_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_date", "from_currency__code"]
        unique_together = [("tenant", "from_currency", "to_currency", "effective_date")]

    def __str__(self):
        return f"{self.from_currency.code}→{self.to_currency.code} @ {self.effective_date}"

    def clean(self):
        if self.from_currency_id and self.to_currency_id and self.from_currency_id == self.to_currency_id:
            raise ValidationError({"to_currency": "From and to currency must differ."})
        if self.rate is not None and self.rate <= 0:
            raise ValidationError({"rate": "Rate must be positive."})


class TaxType(models.Model):
    """VAT, GST, withholding, …"""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_tax_types",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} — {self.name}"


class TaxRate(models.Model):
    """Percentage rate for a tax type (time-bounded)."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_tax_rates",
    )
    tax_type = models.ForeignKey(
        TaxType,
        on_delete=models.CASCADE,
        related_name="rates",
    )
    rate_percent = models.DecimalField(max_digits=7, decimal_places=4, help_text="Percent, e.g. 15.0000 for 15%.")
    effective_from = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_from", "tax_type__code"]

    def __str__(self):
        return f"{self.tax_type.code} {self.rate_percent}% from {self.effective_from}"


class PaymentTerm(models.Model):
    """Net 30, COD, …"""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="foundation_payment_terms",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    days_until_due = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Days after invoice date (empty for immediate / COD).",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} — {self.name}"
