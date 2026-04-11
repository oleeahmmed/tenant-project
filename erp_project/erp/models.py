"""
ERP Models - Restructured with Info/Item pattern
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal


class TimeStampedModel(models.Model):
    """Abstract base model with created and updated timestamps"""
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        abstract = True
        get_latest_by = 'created_at'
        ordering = ['-created_at']


# ==================== COMPANY MODEL ====================
class Company(TimeStampedModel):
    """Company/Organization Information"""
    name = models.CharField(_("Company Name"), max_length=200)
    logo = models.ImageField(_("Logo"), upload_to='company/', blank=True, null=True)
    address = models.TextField(_("Address"))
    city = models.CharField(_("City"), max_length=100)
    country = models.CharField(_("Country"), max_length=100)
    phone = models.CharField(_("Phone"), max_length=20)
    email = models.EmailField(_("Email"))
    website = models.URLField(_("Website"), blank=True)
    tax_number = models.CharField(_("Tax Number"), max_length=50, blank=True)
    
    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
    
    def __str__(self):
        return self.name


# ==================== WAREHOUSE MODEL ====================
class Warehouse(TimeStampedModel):
    """Warehouse/Location Master"""
    name = models.CharField(_("Warehouse Name"), max_length=100, unique=True, db_index=True)
    code = models.CharField(_("Warehouse Code"), max_length=20, unique=True, db_index=True)
    address = models.TextField(_("Address"), blank=True)
    city = models.CharField(_("City"), max_length=100, blank=True, db_index=True)
    country = models.CharField(_("Country"), max_length=100, blank=True, db_index=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    manager = models.CharField(_("Manager"), max_length=100, blank=True, db_index=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Warehouse")
        verbose_name_plural = _("Warehouses")
        ordering = ['name']
        indexes = [
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['is_active', 'name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


# ==================== CATEGORY MODEL ====================
class Category(TimeStampedModel):
    """Product Category"""
    name = models.CharField(_("Category Name"), max_length=100, unique=True, db_index=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
        ]
    
    def __str__(self):
        return self.name


# ==================== PRODUCT MODEL ====================
class Product(TimeStampedModel):
    """Product/Item Master"""
    name = models.CharField(_("Product Name"), max_length=200, db_index=True)
    sku = models.CharField(_("SKU"), max_length=50, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name=_("Category"), db_index=True)
    description = models.TextField(_("Description"), blank=True)
    unit = models.CharField(_("Unit"), max_length=20, default='PCS', db_index=True)
    
    # Warehouse
    default_warehouse = models.ForeignKey('Warehouse', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_products', verbose_name=_("Default Warehouse"), db_index=True)
    
    # Default BOM for Quick Sale - when sold, BOM components will be deducted from stock
    default_bom = models.ForeignKey('BillOfMaterials', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_products', verbose_name=_("Default BOM"), help_text=_("If set, Quick Sale will deduct BOM components instead of this product"), db_index=True)
    
    # Pricing
    purchase_price = models.DecimalField(_("Purchase Price"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    selling_price = models.DecimalField(_("Selling Price"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Stock settings (actual stock is in ProductWarehouseStock)
    min_stock_level = models.DecimalField(_("Minimum Stock Level"), max_digits=10, decimal_places=2, default=Decimal('10.00'))
    
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ['name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['default_warehouse', 'is_active']),
            models.Index(fields=['is_active', 'name']),
            models.Index(fields=['sku', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def current_stock(self):
        """Total stock across all warehouses (calculated from ProductWarehouseStock)"""
        from django.db.models import Sum
        total = self.warehouse_stocks.aggregate(total=Sum('quantity'))['total']
        return total or Decimal('0.00')
    
    @property
    def default_warehouse_stock(self):
        """Stock in default warehouse only"""
        if self.default_warehouse:
            return self.get_warehouse_stock(self.default_warehouse)
        return Decimal('0.00')
    
    def get_warehouse_stock(self, warehouse):
        """Get stock quantity for a specific warehouse"""
        stock = ProductWarehouseStock.objects.filter(product=self, warehouse=warehouse).first()
        return stock.quantity if stock else Decimal('0.00')
    
    def update_warehouse_stock(self, warehouse, quantity_change):
        """Update stock for a specific warehouse (+ or -)"""
        stock, created = ProductWarehouseStock.objects.get_or_create(
            product=self,
            warehouse=warehouse,
            defaults={'quantity': Decimal('0.00')}
        )
        stock.quantity += quantity_change
        if stock.quantity < 0:
            stock.quantity = Decimal('0.00')
        stock.save()
        return stock.quantity
    
    def clean(self):
        """Validate that default_bom belongs to this product"""
        from django.core.exceptions import ValidationError
        if self.default_bom and self.default_bom.product_id != self.pk:
            raise ValidationError({
                'default_bom': _("Selected BOM must belong to this product. This BOM is for: %(product)s") % {'product': self.default_bom.product.name}
            })
    
    def save(self, *args, **kwargs):
        # Set default warehouse to first warehouse if not set
        if not self.default_warehouse:
            first_warehouse = Warehouse.objects.filter(is_active=True).first()
            if first_warehouse:
                self.default_warehouse = first_warehouse
        super().save(*args, **kwargs)


# ==================== SIZE MODEL ====================
class Size(TimeStampedModel):
    """Size Master (S, M, L, XL, etc.)"""
    name = models.CharField(_("Size Name"), max_length=50, unique=True, db_index=True)
    code = models.CharField(_("Size Code"), max_length=20, unique=True, db_index=True)
    sort_order = models.IntegerField(_("Sort Order"), default=0, db_index=True, help_text=_("Display order (smaller number appears first)"))
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Size")
        verbose_name_plural = _("Sizes")
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['sort_order', 'is_active']),
            models.Index(fields=['is_active', 'name']),
        ]
    
    def __str__(self):
        return self.name


# ==================== COLOR MODEL ====================
class Color(TimeStampedModel):
    """Color Master"""
    name = models.CharField(_("Color Name"), max_length=50, unique=True, db_index=True)
    code = models.CharField(_("Color Code"), max_length=20, unique=True, db_index=True)
    hex_code = models.CharField(_("Hex Code"), max_length=7, blank=True, help_text=_("e.g., #FF0000 for Red"))
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Color")
        verbose_name_plural = _("Colors")
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
        ]
    
    def __str__(self):
        return self.name


# ==================== PRODUCT VARIANT MODEL ====================
class ProductVariant(TimeStampedModel):
    """Product Variants (Size-Color combinations)"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name=_("Product"), db_index=True)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name='product_variants', verbose_name=_("Size"), db_index=True)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='product_variants', verbose_name=_("Color"), db_index=True)
    
    # Variant-specific details
    sku = models.CharField(_("Variant SKU"), max_length=100, unique=True, db_index=True, help_text=_("Auto-generated: Product SKU + Size + Color"))
    barcode = models.CharField(_("Barcode"), max_length=100, blank=True, unique=True, null=True, db_index=True)
    
    # Pricing (can override product pricing)
    purchase_price = models.DecimalField(_("Purchase Price"), max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.00'))], help_text=_("Leave blank to use product price"))
    selling_price = models.DecimalField(_("Selling Price"), max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.00'))], help_text=_("Leave blank to use product price"))
    
    # Stock (actual stock is in ProductVariantWarehouseStock)
    min_stock_level = models.DecimalField(_("Minimum Stock Level"), max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Product Variant")
        verbose_name_plural = _("Product Variants")
        ordering = ['product', 'size__sort_order', 'color__name']
        unique_together = [['product', 'size', 'color']]
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['size', 'color']),
            models.Index(fields=['is_active', 'sku']),
            models.Index(fields=['product', 'size', 'color']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.size.name} - {self.color.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided
        if not self.sku:
            self.sku = f"{self.product.sku}-{self.size.code}-{self.color.code}"
        super().save(*args, **kwargs)
    
    @property
    def current_stock(self):
        """Total stock across all warehouses"""
        from django.db.models import Sum
        total = self.warehouse_stocks.aggregate(total=Sum('quantity'))['total']
        return total or Decimal('0.00')
    
    @property
    def effective_purchase_price(self):
        """Return variant price or fall back to product price"""
        return self.purchase_price if self.purchase_price else self.product.purchase_price
    
    @property
    def effective_selling_price(self):
        """Return variant price or fall back to product price"""
        return self.selling_price if self.selling_price else self.product.selling_price
    
    @property
    def effective_min_stock_level(self):
        """Return variant min stock or fall back to product min stock"""
        return self.min_stock_level if self.min_stock_level else self.product.min_stock_level
    
    def get_warehouse_stock(self, warehouse):
        """Get stock quantity for a specific warehouse"""
        stock = ProductVariantWarehouseStock.objects.filter(variant=self, warehouse=warehouse).first()
        return stock.quantity if stock else Decimal('0.00')
    
    def update_warehouse_stock(self, warehouse, quantity_change):
        """Update stock for a specific warehouse (+ or -)"""
        stock, created = ProductVariantWarehouseStock.objects.get_or_create(
            variant=self,
            warehouse=warehouse,
            defaults={'quantity': Decimal('0.00')}
        )
        stock.quantity += quantity_change
        if stock.quantity < 0:
            stock.quantity = Decimal('0.00')
        stock.save()
        return stock.quantity


# ==================== CUSTOMER MODEL ====================
class Customer(TimeStampedModel):
    """Customer Master"""
    name = models.CharField(_("Customer Name"), max_length=200, db_index=True)
    email = models.EmailField(_("Email"), blank=True, db_index=True)
    phone = models.CharField(_("Phone"), max_length=20, db_index=True)
    address = models.TextField(_("Address"), blank=True)
    city = models.CharField(_("City"), max_length=100, blank=True, db_index=True)
    country = models.CharField(_("Country"), max_length=100, blank=True, db_index=True)
    tax_number = models.CharField(_("Tax Number"), max_length=50, blank=True)
    credit_limit = models.DecimalField(_("Credit Limit"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['email', 'is_active']),
        ]
    
    def __str__(self):
        return self.name


# ==================== SUPPLIER MODEL ====================
class Supplier(TimeStampedModel):
    """Supplier/Vendor Master"""
    name = models.CharField(_("Supplier Name"), max_length=200, db_index=True)
    email = models.EmailField(_("Email"), blank=True, db_index=True)
    phone = models.CharField(_("Phone"), max_length=20, db_index=True)
    address = models.TextField(_("Address"), blank=True)
    city = models.CharField(_("City"), max_length=100, blank=True, db_index=True)
    country = models.CharField(_("Country"), max_length=100, blank=True, db_index=True)
    tax_number = models.CharField(_("Tax Number"), max_length=50, blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['email', 'is_active']),
        ]
    
    def __str__(self):
        return self.name


# ==================== SALESPERSON MODEL ====================
class SalesPerson(TimeStampedModel):
    """Sales Person/Representative"""
    name = models.CharField(_("Sales Person Name"), max_length=200, db_index=True)
    email = models.EmailField(_("Email"), blank=True, db_index=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True, db_index=True)
    employee_id = models.CharField(_("Employee ID"), max_length=50, blank=True, db_index=True)
    commission_rate = models.DecimalField(_("Commission Rate (%)"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Sales Person")
        verbose_name_plural = _("Sales Persons")
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
            models.Index(fields=['email', 'is_active']),
        ]
    
    def __str__(self):
        return self.name


# ==================== SALES QUOTATION ====================
class SalesQuotation(TimeStampedModel):
    """Sales Quotation - Header/Info"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('sent', _('Sent')),
        ('accepted', _('Accepted')),
        ('converted', _('Converted to Order')),
        ('rejected', _('Rejected')),
        ('expired', _('Expired')),
    ]
    
    quotation_number = models.CharField(_("Quotation Number"), max_length=50, unique=True, editable=False)
    quotation_date = models.DateField(_("Quotation Date"), default=timezone.now)
    valid_until = models.DateField(_("Valid Until"), null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales_quotations', verbose_name=_("Customer"))
    salesperson = models.ForeignKey('SalesPerson', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_quotations', verbose_name=_("Sales Person"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    job_reference = models.CharField(_("Job Reference"), max_length=100, blank=True)
    shipping_method = models.CharField(_("Shipping Method"), max_length=100, blank=True, default="Standard")
    delivery_terms = models.CharField(_("Delivery Terms"), max_length=100, blank=True, default="FOB")
    payment_terms = models.CharField(_("Payment Terms"), max_length=100, blank=True, default="Net 30")
    
    # Amounts (calculated from items)
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(_("Tax Rate (%)"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='sales_quotations', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this salesquotation"))

    class Meta:
        verbose_name = _("Sales Quotation")
        verbose_name_plural = _("Sales Quotations")
        ordering = ['-quotation_date', '-created_at']
    
    def __str__(self):
        return f"{self.quotation_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        if not self.quotation_number:
            # Generate quotation number
            last_quotation = SalesQuotation.objects.order_by('-id').first()
            if last_quotation:
                last_num = int(last_quotation.quotation_number.split('-')[-1])
                self.quotation_number = f"SQ-{last_num + 1:06d}"
            else:
                self.quotation_number = "SQ-000001"
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        self.save(update_fields=['subtotal', 'total_amount'])


class SalesQuotationItem(TimeStampedModel):
    """Sales Quotation Item - Line Item"""
    sales_quotation = models.ForeignKey(SalesQuotation, on_delete=models.CASCADE, related_name='items', verbose_name=_("Sales Quotation"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Sales Quotation Item")
        verbose_name_plural = _("Sales Quotation Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.sales_quotation.quotation_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Update parent totals
        self.sales_quotation.calculate_totals()


# ==================== SALES ORDER ====================
class SalesOrder(TimeStampedModel):
    """Sales Order - Header/Info"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('confirmed', _('Confirmed')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    order_number = models.CharField(_("Order Number"), max_length=50, unique=True, editable=False)
    order_date = models.DateField(_("Order Date"), default=timezone.now)
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, related_name='sales_orders', verbose_name=_("Branch"), help_text=_("Branch/Warehouse for this order"))
    sales_quotation = models.ForeignKey(SalesQuotation, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders', verbose_name=_("Sales Quotation"))
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales_orders', verbose_name=_("Customer"))
    salesperson = models.ForeignKey('SalesPerson', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders', verbose_name=_("Sales Person"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    job_reference = models.CharField(_("Job Reference"), max_length=100, blank=True)
    shipping_method = models.CharField(_("Shipping Method"), max_length=100, blank=True, default="Standard")
    delivery_terms = models.CharField(_("Delivery Terms"), max_length=100, blank=True, default="FOB")
    delivery_date = models.DateField(_("Delivery Date"), null=True, blank=True)
    payment_terms = models.CharField(_("Payment Terms"), max_length=100, blank=True, default="Net 30")
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    
    # Amounts (calculated from items)
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(_("Tax Rate (%)"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Sales Order")
        verbose_name_plural = _("Sales Orders")
        ordering = ['-order_date', '-created_at']
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            last_order = SalesOrder.objects.order_by('-id').first()
            if last_order:
                last_num = int(last_order.order_number.split('-')[-1])
                self.order_number = f"SO-{last_num + 1:06d}"
            else:
                self.order_number = "SO-000001"
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        self.save(update_fields=['subtotal', 'total_amount'])


class SalesOrderItem(TimeStampedModel):
    """Sales Order Item - Line Item"""
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items', verbose_name=_("Sales Order"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Sales Order Item")
        verbose_name_plural = _("Sales Order Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.sales_order.order_number} - {self.product.name}"
    
    @property
    def delivered_quantity(self):
        """Calculate total delivered quantity for this product"""
        from django.db.models import Sum
        total = DeliveryItem.objects.filter(
            delivery__sales_order=self.sales_order,
            product=self.product
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')
        return total
    
    @property
    def invoiced_quantity(self):
        """Calculate total invoiced quantity for this product"""
        from django.db.models import Sum
        total = InvoiceItem.objects.filter(
            invoice__sales_order=self.sales_order,
            product=self.product
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')
        return total
    
    @property
    def returned_quantity(self):
        """Calculate total returned quantity for this product"""
        from django.db.models import Sum
        total = SalesReturnItem.objects.filter(
            sales_return__sales_order=self.sales_order,
            product=self.product
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')
        return total
    
    @property
    def remaining_to_deliver(self):
        """Calculate remaining quantity to deliver"""
        return self.quantity - self.delivered_quantity
    
    @property
    def remaining_to_invoice(self):
        """Calculate remaining quantity to invoice"""
        return self.quantity - self.invoiced_quantity
    
    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Update parent totals
        self.sales_order.calculate_totals()


# ==================== INVOICE ====================
class Invoice(TimeStampedModel):
    """Invoice - Header/Info"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('sent', _('Sent')),
        ('paid', _('Paid')),
        ('partially_paid', _('Partially Paid')),
        ('overdue', _('Overdue')),
        ('cancelled', _('Cancelled')),
    ]
    
    invoice_number = models.CharField(_("Invoice Number"), max_length=50, unique=True, editable=False)
    invoice_date = models.DateField(_("Invoice Date"), default=timezone.now)
    due_date = models.DateField(_("Due Date"))
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, related_name='invoices', verbose_name=_("Branch"), help_text=_("Branch/Warehouse for this invoice"))
    
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name='invoices', verbose_name=_("Sales Order"))
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices', verbose_name=_("Customer"))
    salesperson = models.ForeignKey('SalesPerson', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name=_("Sales Person"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Amounts
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(_("Due Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ['-invoice_date', '-created_at']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last_invoice = Invoice.objects.order_by('-id').first()
            if last_invoice:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                self.invoice_number = f"INV-{last_num + 1:06d}"
            else:
                self.invoice_number = "INV-000001"
        
        self.due_amount = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        self.due_amount = self.total_amount - self.paid_amount
        self.save(update_fields=['subtotal', 'total_amount', 'due_amount'])


class InvoiceItem(TimeStampedModel):
    """Invoice Item - Line Item"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name=_("Invoice"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.product.name}"
    
    def get_sales_order_item(self):
        """Find matching sales order item by product"""
        if self.invoice.sales_order:
            return self.invoice.sales_order.items.filter(product=self.product).first()
        return None
    
    @property
    def sales_order_item(self):
        """Get sales order item for this product"""
        return self.get_sales_order_item()
    
    @property
    def available_quantity(self):
        """Get available quantity from sales order"""
        so_item = self.get_sales_order_item()
        if so_item:
            return so_item.remaining_to_invoice
        return Decimal('0.00')
    
    def clean(self):
        """Validate invoice quantity"""
        from django.core.exceptions import ValidationError
        
        if not self.invoice.sales_order:
            raise ValidationError('Invoice must have a Sales Order.')
        
        # Find matching sales order item
        so_item = self.get_sales_order_item()
        if not so_item:
            raise ValidationError({
                'product': f'Product "{self.product.name}" is not in Sales Order {self.invoice.sales_order.order_number}.'
            })
        
        # Check if quantity exceeds available
        from django.db.models import Sum
        other_invoices = InvoiceItem.objects.filter(
            invoice__sales_order=self.invoice.sales_order,
            product=self.product
        ).exclude(pk=self.pk).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')
        
        total_invoiced = other_invoices + self.quantity
        
        if total_invoiced > so_item.quantity:
            raise ValidationError({
                'quantity': f'Cannot invoice {self.quantity}. Only {so_item.remaining_to_invoice} remaining for this product.'
            })
    
    def save(self, *args, **kwargs):
        # Auto-set unit price from sales order if not set
        if self.unit_price == Decimal('0.00'):
            so_item = self.get_sales_order_item()
            if so_item:
                self.unit_price = so_item.unit_price
        
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.invoice.calculate_totals()


# ==================== SALES RETURN ====================
class SalesReturn(TimeStampedModel):
    """Sales Return - Header/Info (Stock IN when completed - goods returned by customer)"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('completed', _('Completed')),
    ]
    
    return_number = models.CharField(_("Return Number"), max_length=50, unique=True, editable=False)
    return_date = models.DateField(_("Return Date"), default=timezone.now)
    
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name='returns', verbose_name=_("Sales Order"))
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='returns', verbose_name=_("Invoice"))
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales_returns', verbose_name=_("Customer"))
    salesperson = models.ForeignKey('SalesPerson', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_returns', verbose_name=_("Sales Person"))
    warehouse = models.ForeignKey('Warehouse', on_delete=models.PROTECT, related_name='sales_returns', verbose_name=_("Warehouse"), help_text=_("Returned goods will be added to this warehouse"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    reason = models.TextField(_("Return Reason"), blank=True)
    
    # Amounts
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    refund_amount = models.DecimalField(_("Refund Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Stock tracking
    stock_updated = models.BooleanField(_("Stock Updated"), default=False, editable=False)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Sales Return")
        verbose_name_plural = _("Sales Returns")
        ordering = ['-return_date', '-created_at']
    
    def __str__(self):
        return f"{self.return_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        if not self.return_number:
            last_return = SalesReturn.objects.order_by('-id').first()
            if last_return:
                last_num = int(last_return.return_number.split('-')[-1])
                self.return_number = f"SR-{last_num + 1:06d}"
            else:
                self.return_number = "SR-000001"
        
        # Set default warehouse
        if not self.warehouse_id:
            first_warehouse = Warehouse.objects.filter(is_active=True).first()
            if first_warehouse:
                self.warehouse = first_warehouse
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.total_amount = self.subtotal
        self.save(update_fields=['subtotal', 'total_amount'])


class SalesReturnItem(TimeStampedModel):
    """Sales Return Item - Line Item"""
    sales_return = models.ForeignKey(SalesReturn, on_delete=models.CASCADE, related_name='items', verbose_name=_("Sales Return"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Sales Return Item")
        verbose_name_plural = _("Sales Return Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.sales_return.return_number} - {self.product.name}"
    
    def get_sales_order_item(self):
        """Find matching sales order item by product"""
        if self.sales_return.sales_order:
            return self.sales_return.sales_order.items.filter(product=self.product).first()
        return None
    
    @property
    def sales_order_item(self):
        """Get sales order item for this product"""
        return self.get_sales_order_item()
    
    @property
    def available_quantity(self):
        """Get available quantity to return (delivered - already returned)"""
        so_item = self.get_sales_order_item()
        if so_item:
            return so_item.delivered_quantity - so_item.returned_quantity
        return Decimal('0.00')
    
    def clean(self):
        """Validate return quantity"""
        from django.core.exceptions import ValidationError
        
        if not self.sales_return.sales_order:
            raise ValidationError('Sales Return must have a Sales Order.')
        
        # Find matching sales order item
        so_item = self.get_sales_order_item()
        if not so_item:
            raise ValidationError({
                'product': f'Product "{self.product.name}" is not in Sales Order {self.sales_return.sales_order.order_number}.'
            })
        
        # Check if quantity exceeds delivered
        from django.db.models import Sum
        other_returns = SalesReturnItem.objects.filter(
            sales_return__sales_order=self.sales_return.sales_order,
            product=self.product
        ).exclude(pk=self.pk).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')
        
        total_returned = other_returns + self.quantity
        delivered = so_item.delivered_quantity
        
        if total_returned > delivered:
            raise ValidationError({
                'quantity': f'Cannot return {self.quantity}. Only {delivered - other_returns} available to return for this product.'
            })
    
    def save(self, *args, **kwargs):
        # Auto-set unit price from sales order if not set
        if self.unit_price == Decimal('0.00'):
            so_item = self.get_sales_order_item()
            if so_item:
                self.unit_price = so_item.unit_price
        
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.sales_return.calculate_totals()


# ==================== DELIVERY ====================
class Delivery(TimeStampedModel):
    """Delivery - Header/Info (Stock OUT when delivered)"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('in_transit', _('In Transit')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    ]
    
    delivery_number = models.CharField(_("Delivery Number"), max_length=50, unique=True, editable=False)
    delivery_date = models.DateField(_("Delivery Date"), default=timezone.now)
    
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name='deliveries', verbose_name=_("Sales Order"))
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='deliveries', verbose_name=_("Customer"))
    salesperson = models.ForeignKey('SalesPerson', on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries', verbose_name=_("Sales Person"))
    warehouse = models.ForeignKey('Warehouse', on_delete=models.PROTECT, related_name='deliveries', verbose_name=_("Warehouse"), help_text=_("Stock will be deducted from this warehouse"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Delivery Details
    delivery_address = models.TextField(_("Delivery Address"), blank=True)
    tracking_number = models.CharField(_("Tracking Number"), max_length=100, blank=True)
    carrier = models.CharField(_("Carrier"), max_length=100, blank=True)
    shipping_cost = models.DecimalField(_("Shipping Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Stock tracking
    stock_updated = models.BooleanField(_("Stock Updated"), default=False, editable=False, help_text=_("Whether stock has been deducted"))
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Delivery")
        verbose_name_plural = _("Deliveries")
        ordering = ['-delivery_date', '-created_at']
    
    def __str__(self):
        return f"{self.delivery_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        if not self.delivery_number:
            last_delivery = Delivery.objects.order_by('-id').first()
            if last_delivery:
                last_num = int(last_delivery.delivery_number.split('-')[-1])
                self.delivery_number = f"DL-{last_num + 1:06d}"
            else:
                self.delivery_number = "DL-000001"
        
        # Set default warehouse from first item's product or first active warehouse
        if not self.warehouse_id:
            first_warehouse = Warehouse.objects.filter(is_active=True).first()
            if first_warehouse:
                self.warehouse = first_warehouse
        
        super().save(*args, **kwargs)


class DeliveryItem(TimeStampedModel):
    """Delivery Item - Line Item"""
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='items', verbose_name=_("Delivery"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Delivery Item")
        verbose_name_plural = _("Delivery Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.delivery.delivery_number} - {self.product.name}"
    
    def get_sales_order_item(self):
        """Find matching sales order item by product"""
        if self.delivery.sales_order:
            return self.delivery.sales_order.items.filter(product=self.product).first()
        return None
    
    @property
    def sales_order_item(self):
        """Get sales order item for this product"""
        return self.get_sales_order_item()
    
    @property
    def available_quantity(self):
        """Get available quantity from sales order"""
        so_item = self.get_sales_order_item()
        if so_item:
            return so_item.remaining_to_deliver
        return Decimal('0.00')
    
    def clean(self):
        """Validate delivery quantity"""
        from django.core.exceptions import ValidationError
        
        if not self.delivery.sales_order:
            raise ValidationError('Delivery must have a Sales Order.')
        
        # Find matching sales order item
        so_item = self.get_sales_order_item()
        if not so_item:
            raise ValidationError({
                'product': f'Product "{self.product.name}" is not in Sales Order {self.delivery.sales_order.order_number}.'
            })
        
        # Check if quantity exceeds available
        from django.db.models import Sum
        other_deliveries = DeliveryItem.objects.filter(
            delivery__sales_order=self.delivery.sales_order,
            product=self.product
        ).exclude(pk=self.pk).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')
        
        total_delivered = other_deliveries + self.quantity
        
        if total_delivered > so_item.quantity:
            raise ValidationError({
                'quantity': f'Cannot deliver {self.quantity}. Only {so_item.remaining_to_deliver} remaining for this product.'
            })
    
    def save(self, *args, **kwargs):
        # Auto-set unit price from sales order if not set
        if self.unit_price == Decimal('0.00'):
            so_item = self.get_sales_order_item()
            if so_item:
                self.unit_price = so_item.unit_price
        
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ==================== PURCHASE QUOTATION ====================
class PurchaseQuotation(TimeStampedModel):
    """Purchase Quotation (RFQ - Request for Quotation) - Header/Info"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('sent', _('Sent')),
        ('received', _('Received')),
        ('accepted', _('Accepted')),
        ('converted', _('Converted to Order')),
        ('rejected', _('Rejected')),
        ('expired', _('Expired')),
    ]
    
    quotation_number = models.CharField(_("Quotation Number"), max_length=50, unique=True, editable=False)
    quotation_date = models.DateField(_("Quotation Date"), default=timezone.now)
    valid_until = models.DateField(_("Valid Until"), null=True, blank=True)
    
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_quotations', verbose_name=_("Supplier"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Amounts
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='purchase_quotations', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this purchasequotation"))

    class Meta:
        verbose_name = _("Purchase Quotation")
        verbose_name_plural = _("Purchase Quotations")
        ordering = ['-quotation_date', '-created_at']
    
    def __str__(self):
        return f"{self.quotation_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        if not self.quotation_number:
            last_quotation = PurchaseQuotation.objects.order_by('-id').first()
            if last_quotation:
                last_num = int(last_quotation.quotation_number.split('-')[-1])
                self.quotation_number = f"PQ-{last_num + 1:06d}"
            else:
                self.quotation_number = "PQ-000001"
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        self.save(update_fields=['subtotal', 'total_amount'])


class PurchaseQuotationItem(TimeStampedModel):
    """Purchase Quotation Item - Line Item"""
    purchase_quotation = models.ForeignKey(PurchaseQuotation, on_delete=models.CASCADE, related_name='items', verbose_name=_("Purchase Quotation"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Purchase Quotation Item")
        verbose_name_plural = _("Purchase Quotation Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.purchase_quotation.quotation_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.purchase_quotation.calculate_totals()


# ==================== PURCHASE ORDER ====================
class PurchaseOrder(TimeStampedModel):
    """Purchase Order - Header/Info"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('sent', _('Sent')),
        ('confirmed', _('Confirmed')),
        ('received', _('Received')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    order_number = models.CharField(_("Order Number"), max_length=50, unique=True, editable=False)
    order_date = models.DateField(_("Order Date"), default=timezone.now)
    expected_date = models.DateField(_("Expected Delivery Date"), null=True, blank=True)
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, related_name='purchase_orders', verbose_name=_("Branch"), help_text=_("Branch/Warehouse for this order"))
    
    purchase_quotation = models.ForeignKey(PurchaseQuotation, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders', verbose_name=_("Purchase Quotation"))
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders', verbose_name=_("Supplier"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Amounts
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(_("Due Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Purchase Order")
        verbose_name_plural = _("Purchase Orders")
        ordering = ['-order_date', '-created_at']
    
    def __str__(self):
        return f"{self.order_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            last_order = PurchaseOrder.objects.order_by('-id').first()
            if last_order:
                last_num = int(last_order.order_number.split('-')[-1])
                self.order_number = f"PO-{last_num + 1:06d}"
            else:
                self.order_number = "PO-000001"
        
        self.due_amount = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        self.due_amount = self.total_amount - self.paid_amount
        self.save(update_fields=['subtotal', 'total_amount', 'due_amount'])


class PurchaseOrderItem(TimeStampedModel):
    """Purchase Order Item - Line Item"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items', verbose_name=_("Purchase Order"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Purchase Order Item")
        verbose_name_plural = _("Purchase Order Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.purchase_order.order_number} - {self.product.name}"
    
    @property
    def received_quantity(self):
        """Calculate total received quantity for this product"""
        from django.db.models import Sum
        total = GoodsReceiptPOItem.objects.filter(
            goods_receipt_po__purchase_order=self.purchase_order,
            product=self.product
        ).aggregate(total=Sum('received_quantity'))['total'] or Decimal('0.00')
        return total
    
    @property
    def returned_quantity(self):
        """Calculate total returned quantity for this product"""
        from django.db.models import Sum
        total = PurchaseReturnItem.objects.filter(
            purchase_return__purchase_order=self.purchase_order,
            product=self.product
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')
        return total
    
    @property
    def remaining_to_receive(self):
        """Calculate remaining quantity to receive"""
        return self.quantity - self.received_quantity
    
    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.purchase_order.calculate_totals()


# ==================== GOODS RECEIPT (GRN) ====================
class GoodsReceipt(TimeStampedModel):
    """Goods Receipt Note (GRN) - General Stock IN (without Purchase Order)
    
    Use for:
    - Opening Stock
    - Stock Adjustment (increase)
    - Found/Recovered items
    - Transfer In (from other location)
    """
    RECEIPT_TYPE_CHOICES = [
        ('opening', _('Opening Stock')),
        ('adjustment', _('Stock Adjustment')),
        ('found', _('Found/Recovered')),
        ('transfer', _('Transfer In')),
        ('other', _('Other')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('received', _('Received')),
        ('cancelled', _('Cancelled')),
    ]
    
    receipt_number = models.CharField(_("Receipt Number"), max_length=50, unique=True, editable=False)
    receipt_date = models.DateField(_("Receipt Date"), default=timezone.now)
    receipt_type = models.CharField(_("Receipt Type"), max_length=20, choices=RECEIPT_TYPE_CHOICES, default='opening')
    
    warehouse = models.ForeignKey('Warehouse', on_delete=models.PROTECT, related_name='goods_receipts', verbose_name=_("Warehouse"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    received_by = models.CharField(_("Received By"), max_length=100, blank=True)
    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    
    stock_updated = models.BooleanField(_("Stock Updated"), default=False, editable=False)
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Goods Receipt")
        verbose_name_plural = _("Goods Receipts")
        ordering = ['-receipt_date', '-created_at']
    
    def __str__(self):
        return f"{self.receipt_number} - {self.get_receipt_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            last = GoodsReceipt.objects.order_by('-id').first()
            if last:
                last_num = int(last.receipt_number.split('-')[-1])
                self.receipt_number = f"GRN-{last_num + 1:06d}"
            else:
                self.receipt_number = "GRN-000001"
        
        if not self.warehouse_id:
            first_warehouse = Warehouse.objects.filter(is_active=True).first()
            if first_warehouse:
                self.warehouse = first_warehouse
        
        super().save(*args, **kwargs)


class GoodsReceiptItem(TimeStampedModel):
    """Goods Receipt Item - Line Item (General)"""
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='items', verbose_name=_("Goods Receipt"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Goods Receipt Item")
        verbose_name_plural = _("Goods Receipt Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.goods_receipt.receipt_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        if self.unit_price == Decimal('0.00') and self.product:
            self.unit_price = self.product.purchase_price
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ==================== GOODS RECEIPT PO (FROM PURCHASE ORDER) ====================
class GoodsReceiptPO(TimeStampedModel):
    """Goods Receipt from Purchase Order - Stock IN when received from supplier"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('partial', _('Partially Received')),
        ('received', _('Received')),
        ('inspected', _('Inspected')),
        ('completed', _('Completed')),
        ('rejected', _('Rejected')),
    ]
    
    receipt_number = models.CharField(_("Receipt Number"), max_length=50, unique=True, editable=False)
    receipt_date = models.DateField(_("Receipt Date"), default=timezone.now)
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='goods_receipts_po', verbose_name=_("Purchase Order"))
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='goods_receipts_po', verbose_name=_("Supplier"))
    warehouse = models.ForeignKey('Warehouse', on_delete=models.PROTECT, related_name='goods_receipts_po', verbose_name=_("Warehouse"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    received_by = models.CharField(_("Received By"), max_length=100, blank=True)
    inspected_by = models.CharField(_("Inspected By"), max_length=100, blank=True)
    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    supplier_delivery_note = models.CharField(_("Supplier Delivery Note"), max_length=100, blank=True)
    
    stock_updated = models.BooleanField(_("Stock Updated"), default=False, editable=False)
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='goods_receipt_pos', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this goodsreceiptpo"))

    class Meta:
        verbose_name = _("Goods Receipt (PO)")
        verbose_name_plural = _("Goods Receipts (PO)")
        ordering = ['-receipt_date', '-created_at']
    
    def __str__(self):
        return f"{self.receipt_number} - PO:{self.purchase_order.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            last = GoodsReceiptPO.objects.order_by('-id').first()
            if last:
                last_num = int(last.receipt_number.split('-')[-1])
                self.receipt_number = f"GRPO-{last_num + 1:06d}"
            else:
                self.receipt_number = "GRPO-000001"
        
        # Auto-fill supplier from PO
        if not self.supplier_id and self.purchase_order:
            self.supplier = self.purchase_order.supplier
        
        if not self.warehouse_id:
            first_warehouse = Warehouse.objects.filter(is_active=True).first()
            if first_warehouse:
                self.warehouse = first_warehouse
        
        super().save(*args, **kwargs)


class GoodsReceiptPOItem(TimeStampedModel):
    """Goods Receipt PO Item - Line Item"""
    goods_receipt_po = models.ForeignKey(GoodsReceiptPO, on_delete=models.CASCADE, related_name='items', verbose_name=_("Goods Receipt PO"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    ordered_quantity = models.DecimalField(_("Ordered Qty"), max_digits=10, decimal_places=2, default=Decimal('0.00'), editable=False)
    received_quantity = models.DecimalField(_("Received Qty"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], default=Decimal('0.00'))
    rejected_quantity = models.DecimalField(_("Rejected Qty"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    accepted_quantity = models.DecimalField(_("Accepted Qty"), max_digits=10, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    rejection_reason = models.CharField(_("Rejection Reason"), max_length=200, blank=True)
    
    class Meta:
        verbose_name = _("Goods Receipt PO Item")
        verbose_name_plural = _("Goods Receipt PO Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.goods_receipt_po.receipt_number} - {self.product.name}"
    
    def get_purchase_order_item(self):
        """Find matching purchase order item"""
        return self.goods_receipt_po.purchase_order.items.filter(product=self.product).first()
    
    @property
    def remaining_to_receive(self):
        """Calculate remaining quantity to receive from PO"""
        po_item = self.get_purchase_order_item()
        if po_item:
            # Get total already received for this product
            from django.db.models import Sum
            total_received = GoodsReceiptPOItem.objects.filter(
                goods_receipt_po__purchase_order=self.goods_receipt_po.purchase_order,
                product=self.product,
                goods_receipt_po__status__in=['received', 'inspected', 'completed']
            ).exclude(pk=self.pk).aggregate(total=Sum('accepted_quantity'))['total'] or Decimal('0.00')
            return po_item.quantity - total_received
        return Decimal('0.00')
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        po_item = self.get_purchase_order_item()
        if not po_item:
            raise ValidationError({
                'product': f'Product "{self.product.name}" is not in Purchase Order.'
            })
        
        if self.received_quantity > self.remaining_to_receive + (self.accepted_quantity if self.pk else Decimal('0')):
            raise ValidationError({
                'received_quantity': f'Cannot receive {self.received_quantity}. Only {self.remaining_to_receive} remaining.'
            })
    
    def save(self, *args, **kwargs):
        # Auto-fill from PO item
        po_item = self.get_purchase_order_item()
        if po_item:
            self.ordered_quantity = po_item.quantity
            if self.unit_price == Decimal('0.00'):
                self.unit_price = po_item.unit_price
        
        # Calculate accepted quantity
        self.accepted_quantity = self.received_quantity - self.rejected_quantity
        if self.accepted_quantity < 0:
            self.accepted_quantity = Decimal('0.00')
        
        self.line_total = self.accepted_quantity * self.unit_price
        super().save(*args, **kwargs)


# ==================== PURCHASE INVOICE (AP INVOICE) ====================
class PurchaseInvoice(TimeStampedModel):
    """Purchase Invoice (AP Invoice) - Header/Info"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('received', _('Received')),
        ('paid', _('Paid')),
        ('partially_paid', _('Partially Paid')),
        ('overdue', _('Overdue')),
        ('cancelled', _('Cancelled')),
    ]
    
    invoice_number = models.CharField(_("Invoice Number"), max_length=50, unique=True, editable=False)
    invoice_date = models.DateField(_("Invoice Date"), default=timezone.now)
    due_date = models.DateField(_("Due Date"))
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, related_name='purchase_invoices', verbose_name=_("Branch"), help_text=_("Branch/Warehouse for this invoice"))
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='invoices', verbose_name=_("Purchase Order"))
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='invoices', verbose_name=_("Supplier"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Amounts
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(_("Due Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Purchase Invoice")
        verbose_name_plural = _("Purchase Invoices")
        ordering = ['-invoice_date', '-created_at']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last_invoice = PurchaseInvoice.objects.order_by('-id').first()
            if last_invoice:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                self.invoice_number = f"PINV-{last_num + 1:06d}"
            else:
                self.invoice_number = "PINV-000001"
        
        self.due_amount = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        self.due_amount = self.total_amount - self.paid_amount
        self.save(update_fields=['subtotal', 'total_amount', 'due_amount'])


class PurchaseInvoiceItem(TimeStampedModel):
    """Purchase Invoice Item - Line Item"""
    purchase_invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='items', verbose_name=_("Purchase Invoice"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Purchase Invoice Item")
        verbose_name_plural = _("Purchase Invoice Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.purchase_invoice.invoice_number} - {self.product.name}"
    
    def get_purchase_order_item(self):
        """Find matching purchase order item by product"""
        if self.purchase_invoice.purchase_order:
            return self.purchase_invoice.purchase_order.items.filter(product=self.product).first()
        return None
    
    @property
    def purchase_order_item(self):
        """Get purchase order item for this product"""
        return self.get_purchase_order_item()
    
    @property
    def available_quantity(self):
        """Get available quantity from purchase order"""
        po_item = self.get_purchase_order_item()
        if po_item:
            # Calculate how much has been invoiced already
            from django.db.models import Sum
            invoiced = PurchaseInvoiceItem.objects.filter(
                purchase_invoice__purchase_order=self.purchase_invoice.purchase_order,
                product=self.product
            ).exclude(pk=self.pk).aggregate(total=Sum('quantity'))['total'] or Decimal('0.00')
            return po_item.quantity - invoiced
        return Decimal('0.00')
    
    def clean(self):
        """Validate invoice quantity"""
        from django.core.exceptions import ValidationError
        
        if not self.purchase_invoice.purchase_order:
            return  # Allow saving without validation
        
        # Find matching purchase order item
        po_item = self.get_purchase_order_item()
        if not po_item:
            raise ValidationError({
                'product': f'Product "{self.product.name}" is not in Purchase Order {self.purchase_invoice.purchase_order.order_number}.'
            })
    
    def save(self, *args, **kwargs):
        # Auto-set unit price from purchase order if not set
        if self.unit_price == Decimal('0.00'):
            po_item = self.get_purchase_order_item()
            if po_item:
                self.unit_price = po_item.unit_price
        
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.purchase_invoice.calculate_totals()


# ==================== PURCHASE RETURN ====================
class PurchaseReturn(TimeStampedModel):
    """Purchase Return - Header/Info (Stock OUT when completed - goods returned to supplier)"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('completed', _('Completed')),
    ]
    
    return_number = models.CharField(_("Return Number"), max_length=50, unique=True, editable=False)
    return_date = models.DateField(_("Return Date"), default=timezone.now)
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='returns', verbose_name=_("Purchase Order"))
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_returns', verbose_name=_("Supplier"))
    warehouse = models.ForeignKey('Warehouse', on_delete=models.PROTECT, related_name='purchase_returns', verbose_name=_("Warehouse"), help_text=_("Stock will be deducted from this warehouse"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    reason = models.TextField(_("Return Reason"), blank=True)
    
    # Amounts
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    refund_amount = models.DecimalField(_("Refund Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Stock tracking
    stock_updated = models.BooleanField(_("Stock Updated"), default=False, editable=False)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Purchase Return")
        verbose_name_plural = _("Purchase Returns")
        ordering = ['-return_date', '-created_at']
    
    def __str__(self):
        return f"{self.return_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        # Set default warehouse
        if not self.warehouse_id:
            first_warehouse = Warehouse.objects.filter(is_active=True).first()
            if first_warehouse:
                self.warehouse = first_warehouse
        
        if not self.return_number:
            last_return = PurchaseReturn.objects.order_by('-id').first()
            if last_return:
                last_num = int(last_return.return_number.split('-')[-1])
                self.return_number = f"PR-{last_num + 1:06d}"
            else:
                self.return_number = "PR-000001"
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.total_amount = self.subtotal
        self.save(update_fields=['subtotal', 'total_amount'])


class PurchaseReturnItem(TimeStampedModel):
    """Purchase Return Item - Line Item"""
    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name='items', verbose_name=_("Purchase Return"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Purchase Return Item")
        verbose_name_plural = _("Purchase Return Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.purchase_return.return_number} - {self.product.name}"
    
    def get_purchase_order_item(self):
        """Find matching purchase order item by product"""
        if self.purchase_return.purchase_order:
            return self.purchase_return.purchase_order.items.filter(product=self.product).first()
        return None
    
    @property
    def purchase_order_item(self):
        """Get purchase order item for this product"""
        return self.get_purchase_order_item()
    
    @property
    def available_quantity(self):
        """Get available quantity to return (received quantity)"""
        po_item = self.get_purchase_order_item()
        if po_item:
            return po_item.received_quantity - po_item.returned_quantity
        return Decimal('0.00')
    
    def clean(self):
        """Validate return quantity"""
        from django.core.exceptions import ValidationError
        
        if not self.purchase_return.purchase_order:
            return  # Allow saving without validation
        
        # Find matching purchase order item
        po_item = self.get_purchase_order_item()
        if not po_item:
            raise ValidationError({
                'product': f'Product "{self.product.name}" is not in Purchase Order {self.purchase_return.purchase_order.order_number}.'
            })
    
    def save(self, *args, **kwargs):
        # Auto-set unit price from purchase order if not set
        if self.unit_price == Decimal('0.00'):
            po_item = self.get_purchase_order_item()
            if po_item:
                self.unit_price = po_item.unit_price
        
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.purchase_return.calculate_totals()


# ==================== BILL OF MATERIALS (BOM) ====================
class BillOfMaterials(TimeStampedModel):
    """Bill of Materials - Header/Info"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('obsolete', _('Obsolete')),
    ]
    
    bom_number = models.CharField(_("BOM Number"), max_length=50, unique=True, editable=False)
    name = models.CharField(_("BOM Name"), max_length=200)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='boms', verbose_name=_("Finished Product"))
    version = models.CharField(_("Version"), max_length=20, default='1.0')
    quantity = models.DecimalField(_("Production Quantity"), max_digits=10, decimal_places=2, default=Decimal('1.00'), validators=[MinValueValidator(Decimal('0.01'))])
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Cost tracking
    material_cost = models.DecimalField(_("Material Cost"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    labor_cost = models.DecimalField(_("Labor Cost"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    overhead_cost = models.DecimalField(_("Overhead Cost"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(_("Total Cost"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='bill_of_materials', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this billofmaterials"))

    class Meta:
        verbose_name = _("Bill of Materials")
        verbose_name_plural = _("Bills of Materials")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.bom_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        if not self.bom_number:
            last_bom = BillOfMaterials.objects.order_by('-id').first()
            if last_bom:
                last_num = int(last_bom.bom_number.split('-')[-1])
                self.bom_number = f"BOM-{last_num + 1:06d}"
            else:
                self.bom_number = "BOM-000001"
        
        super().save(*args, **kwargs)
    
    def calculate_costs(self):
        """Calculate total costs from components"""
        components = self.components.all()
        self.material_cost = sum(comp.line_total for comp in components)
        self.total_cost = self.material_cost + self.labor_cost + self.overhead_cost
        self.save(update_fields=['material_cost', 'total_cost'])


class BOMComponent(TimeStampedModel):
    """BOM Component - Line Item (Raw Materials/Components)"""
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='components', verbose_name=_("BOM"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Component/Material"))
    
    quantity = models.DecimalField(_("Quantity Required"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    unit_cost = models.DecimalField(_("Unit Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    scrap_percentage = models.DecimalField(_("Scrap %"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = _("BOM Component")
        verbose_name_plural = _("BOM Components")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.bom.bom_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Auto-set unit cost from product if not set
        if self.unit_cost == Decimal('0.00'):
            self.unit_cost = self.product.purchase_price
        
        # Calculate with scrap
        quantity_with_scrap = self.quantity * (Decimal('1.00') + (self.scrap_percentage / Decimal('100.00')))
        self.line_total = quantity_with_scrap * self.unit_cost
        super().save(*args, **kwargs)
        # Update parent costs
        self.bom.calculate_costs()


# ==================== PRODUCTION ORDER ====================
class ProductionOrder(TimeStampedModel):
    """Production Order - Header/Info"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('planned', _('Planned')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    order_number = models.CharField(_("Order Number"), max_length=50, unique=True, editable=False)
    order_date = models.DateField(_("Order Date"), default=timezone.now)
    planned_start_date = models.DateField(_("Planned Start Date"), null=True, blank=True)
    planned_end_date = models.DateField(_("Planned End Date"), null=True, blank=True)
    actual_start_date = models.DateField(_("Actual Start Date"), null=True, blank=True)
    actual_end_date = models.DateField(_("Actual End Date"), null=True, blank=True)
    
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.PROTECT, related_name='production_orders', verbose_name=_("Bill of Materials"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='production_orders', verbose_name=_("Product to Produce"))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='production_orders', verbose_name=_("Production Warehouse"))
    
    quantity_to_produce = models.DecimalField(_("Quantity to Produce"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    quantity_produced = models.DecimalField(_("Quantity Produced"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Reference
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='production_orders', verbose_name=_("Sales Order"))
    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Production Order")
        verbose_name_plural = _("Production Orders")
        ordering = ['-order_date', '-created_at']
    
    def __str__(self):
        return f"{self.order_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            last_order = ProductionOrder.objects.order_by('-id').first()
            if last_order:
                last_num = int(last_order.order_number.split('-')[-1])
                self.order_number = f"PRO-{last_num + 1:06d}"
            else:
                self.order_number = "PRO-000001"
        
        # Auto-set product from BOM if not set
        if not self.product_id and self.bom:
            self.product = self.bom.product
        
        super().save(*args, **kwargs)
    
    @property
    def remaining_to_produce(self):
        """Calculate remaining quantity to produce"""
        return self.quantity_to_produce - self.quantity_produced


class ProductionOrderComponent(TimeStampedModel):
    """Production Order Component - Required Materials"""
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name='components', verbose_name=_("Production Order"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Component/Material"))
    
    quantity_required = models.DecimalField(_("Quantity Required"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    quantity_consumed = models.DecimalField(_("Quantity Consumed"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    unit_cost = models.DecimalField(_("Unit Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Production Order Component")
        verbose_name_plural = _("Production Order Components")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.production_order.order_number} - {self.product.name}"
    
    @property
    def remaining_to_consume(self):
        """Calculate remaining quantity to consume"""
        return self.quantity_required - self.quantity_consumed
    
    def save(self, *args, **kwargs):
        # Auto-set unit cost from product if not set
        if self.unit_cost == Decimal('0.00'):
            self.unit_cost = self.product.purchase_price
        
        self.line_total = self.quantity_required * self.unit_cost
        super().save(*args, **kwargs)


# ==================== PRODUCTION RECEIPT ====================
class ProductionReceipt(TimeStampedModel):
    """Production Receipt - Finished Goods Receipt"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('received', _('Received')),
        ('inspected', _('Inspected')),
        ('completed', _('Completed')),
    ]
    
    receipt_number = models.CharField(_("Receipt Number"), max_length=50, unique=True, editable=False)
    receipt_date = models.DateField(_("Receipt Date"), default=timezone.now)
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.PROTECT, related_name='receipts', verbose_name=_("Production Order"))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='production_receipts', verbose_name=_("Warehouse"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    received_by = models.CharField(_("Received By"), max_length=100, blank=True)
    inspected_by = models.CharField(_("Inspected By"), max_length=100, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Production Receipt")
        verbose_name_plural = _("Production Receipts")
        ordering = ['-receipt_date', '-created_at']
    
    def __str__(self):
        return f"{self.receipt_number} - {self.production_order.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            last_receipt = ProductionReceipt.objects.order_by('-id').first()
            if last_receipt:
                last_num = int(last_receipt.receipt_number.split('-')[-1])
                self.receipt_number = f"PRR-{last_num + 1:06d}"
            else:
                self.receipt_number = "PRR-000001"
        
        # Auto-set warehouse from production order
        if not self.warehouse_id and self.production_order:
            self.warehouse = self.production_order.warehouse
        
        super().save(*args, **kwargs)


class ProductionReceiptItem(TimeStampedModel):
    """Production Receipt Item - Finished Goods Lines"""
    production_receipt = models.ForeignKey(ProductionReceipt, on_delete=models.CASCADE, related_name='items', verbose_name=_("Production Receipt"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Finished Product"))
    
    planned_quantity = models.DecimalField(_("Planned Quantity"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    received_quantity = models.DecimalField(_("Received Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    rejected_quantity = models.DecimalField(_("Rejected Quantity"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    unit_cost = models.DecimalField(_("Unit Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Production Receipt Item")
        verbose_name_plural = _("Production Receipt Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.production_receipt.receipt_number} - {self.product.name}"
    
    @property
    def accepted_quantity(self):
        return self.received_quantity - self.rejected_quantity
    
    def save(self, *args, **kwargs):
        if self.unit_cost == Decimal('0.00'):
            self.unit_cost = self.product.purchase_price
        
        self.line_total = self.received_quantity * self.unit_cost
        super().save(*args, **kwargs)


# ==================== GOODS ISSUE ====================
class GoodsIssue(TimeStampedModel):
    """Goods Issue - Header/Info (Stock OUT when issued)"""
    ISSUE_TYPE_CHOICES = [
        ('sales', _('For Sales Order')),
        ('production', _('For Production')),
        ('adjustment', _('Stock Adjustment')),
        ('transfer', _('Transfer Out')),
        ('damage', _('Damage/Loss')),
        ('internal', _('Internal Use')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('issued', _('Issued')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    issue_number = models.CharField(_("Issue Number"), max_length=50, unique=True, editable=False)
    issue_date = models.DateField(_("Issue Date"), default=timezone.now)
    issue_type = models.CharField(_("Issue Type"), max_length=20, choices=ISSUE_TYPE_CHOICES, default='sales')
    
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, null=True, blank=True, related_name='goods_issues', verbose_name=_("Sales Order"))
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True, related_name='goods_issues', verbose_name=_("Customer"))
    warehouse = models.ForeignKey('Warehouse', on_delete=models.PROTECT, related_name='goods_issues', verbose_name=_("Warehouse"), help_text=_("Stock will be deducted from this warehouse"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Issue Details
    issued_by = models.CharField(_("Issued By"), max_length=100, blank=True)
    issued_to = models.CharField(_("Issued To"), max_length=100, blank=True)
    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    
    # Stock tracking
    stock_updated = models.BooleanField(_("Stock Updated"), default=False, editable=False, help_text=_("Whether stock has been deducted"))
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Goods Issue")
        verbose_name_plural = _("Goods Issues")
        ordering = ['-issue_date', '-created_at']
    
    def __str__(self):
        return f"{self.issue_number} - {self.get_issue_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.issue_number:
            last_issue = GoodsIssue.objects.order_by('-id').first()
            if last_issue:
                last_num = int(last_issue.issue_number.split('-')[-1])
                self.issue_number = f"GI-{last_num + 1:06d}"
            else:
                self.issue_number = "GI-000001"
        
        # Set default warehouse
        if not self.warehouse_id:
            first_warehouse = Warehouse.objects.filter(is_active=True).first()
            if first_warehouse:
                self.warehouse = first_warehouse
        
        super().save(*args, **kwargs)


class GoodsIssueItem(TimeStampedModel):
    """Goods Issue Item - Line Item"""
    goods_issue = models.ForeignKey(GoodsIssue, on_delete=models.CASCADE, related_name='items', verbose_name=_("Goods Issue"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Goods Issue Item")
        verbose_name_plural = _("Goods Issue Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.goods_issue.issue_number} - {self.product.name}"
    
    def get_sales_order_item(self):
        """Find matching sales order item by product"""
        if self.goods_issue.sales_order:
            return self.goods_issue.sales_order.items.filter(product=self.product).first()
        return None
    
    @property
    def sales_order_item(self):
        """Get sales order item for this product"""
        return self.get_sales_order_item()
    
    @property
    def available_stock(self):
        """Get available stock for this product"""
        return self.product.current_stock
    
    def clean(self):
        """Validate issue quantity"""
        from django.core.exceptions import ValidationError
        
        # Check if quantity exceeds available stock
        if self.quantity > self.product.current_stock:
            raise ValidationError({
                'quantity': f'Cannot issue {self.quantity}. Only {self.product.current_stock} available in stock.'
            })
        
        # If linked to sales order, validate against order quantity
        if self.goods_issue.sales_order:
            so_item = self.get_sales_order_item()
            if not so_item:
                raise ValidationError({
                    'product': f'Product "{self.product.name}" is not in Sales Order {self.goods_issue.sales_order.order_number}.'
                })
    
    def save(self, *args, **kwargs):
        # Auto-set unit price from product if not set
        if self.unit_price == Decimal('0.00'):
            self.unit_price = self.product.selling_price
        
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ==================== PRODUCTION ISSUE ====================
class ProductionIssue(TimeStampedModel):
    """Production Issue - Material Issue for Production Order"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('issued', _('Issued')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    issue_number = models.CharField(_("Issue Number"), max_length=50, unique=True, editable=False)
    issue_date = models.DateField(_("Issue Date"), default=timezone.now)
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.PROTECT, related_name='issues', verbose_name=_("Production Order"))
    warehouse = models.ForeignKey('Warehouse', on_delete=models.PROTECT, related_name='production_issues', verbose_name=_("Warehouse"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    issued_by = models.CharField(_("Issued By"), max_length=100, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Production Issue")
        verbose_name_plural = _("Production Issues")
        ordering = ['-issue_date', '-created_at']
    
    def __str__(self):
        return f"{self.issue_number} - {self.production_order.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.issue_number:
            last_issue = ProductionIssue.objects.order_by('-id').first()
            if last_issue:
                last_num = int(last_issue.issue_number.split('-')[-1])
                self.issue_number = f"PI-{last_num + 1:06d}"
            else:
                self.issue_number = "PI-000001"
        super().save(*args, **kwargs)


class ProductionIssueItem(TimeStampedModel):
    """Production Issue Item - Component/Material Lines"""
    production_issue = models.ForeignKey(ProductionIssue, on_delete=models.CASCADE, related_name='items', verbose_name=_("Production Issue"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Component/Material"))
    
    base_quantity = models.DecimalField(_("Base Quantity"), max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text=_("Required quantity from BOM"))
    issued_quantity = models.DecimalField(_("Issued Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    unit_cost = models.DecimalField(_("Unit Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Production Issue Item")
        verbose_name_plural = _("Production Issue Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.production_issue.issue_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        if self.unit_cost == Decimal('0.00'):
            self.unit_cost = self.product.purchase_price
        
        self.line_total = self.issued_quantity * self.unit_cost
        super().save(*args, **kwargs)


# ==================== PRODUCT WAREHOUSE STOCK ====================
class ProductWarehouseStock(TimeStampedModel):
    """Product Stock by Warehouse"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='warehouse_stocks', verbose_name=_("Product"))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='product_stocks', verbose_name=_("Warehouse"))
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = _("Product Warehouse Stock")
        verbose_name_plural = _("Product Warehouse Stocks")
        unique_together = ['product', 'warehouse']
        ordering = ['product', 'warehouse']
    
    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name}: {self.quantity}"


# ==================== PRODUCT VARIANT WAREHOUSE STOCK ====================
class ProductVariantWarehouseStock(TimeStampedModel):
    """Product Variant Stock by Warehouse (Size-Color combinations)"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='warehouse_stocks', verbose_name=_("Product Variant"))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='variant_stocks', verbose_name=_("Warehouse"))
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = _("Product Variant Warehouse Stock")
        verbose_name_plural = _("Product Variant Warehouse Stocks")
        unique_together = ['variant', 'warehouse']
        ordering = ['variant', 'warehouse']
    
    def __str__(self):
        return f"{self.variant} @ {self.warehouse.name}: {self.quantity}"


# ==================== INVENTORY TRANSFER ====================
class InventoryTransfer(TimeStampedModel):
    """Inventory Transfer between Warehouses - Header/Info"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('in_transit', _('In Transit')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    transfer_number = models.CharField(_("Transfer Number"), max_length=50, unique=True, editable=False)
    transfer_date = models.DateField(_("Transfer Date"), default=timezone.now)
    
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='transfers_out', verbose_name=_("From Warehouse"))
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='transfers_in', verbose_name=_("To Warehouse"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Transfer Details
    transferred_by = models.CharField(_("Transferred By"), max_length=100, blank=True)
    received_by = models.CharField(_("Received By"), max_length=100, blank=True)
    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Inventory Transfer")
        verbose_name_plural = _("Inventory Transfers")
        ordering = ['-transfer_date', '-created_at']
    
    def __str__(self):
        return f"{self.transfer_number} - {self.from_warehouse.name} → {self.to_warehouse.name}"
    
    def save(self, *args, **kwargs):
        if not self.transfer_number:
            last_transfer = InventoryTransfer.objects.order_by('-id').first()
            if last_transfer:
                last_num = int(last_transfer.transfer_number.split('-')[-1])
                self.transfer_number = f"IT-{last_num + 1:06d}"
            else:
                self.transfer_number = "IT-000001"
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate transfer"""
        from django.core.exceptions import ValidationError
        
        if self.from_warehouse == self.to_warehouse:
            raise ValidationError({
                'to_warehouse': 'Cannot transfer to the same warehouse.'
            })


class InventoryTransferItem(TimeStampedModel):
    """Inventory Transfer Item - Line Item"""
    inventory_transfer = models.ForeignKey(InventoryTransfer, on_delete=models.CASCADE, related_name='items', verbose_name=_("Inventory Transfer"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], default=Decimal('1.00'))
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(_("Line Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = _("Inventory Transfer Item")
        verbose_name_plural = _("Inventory Transfer Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.inventory_transfer.transfer_number} - {self.product.name}"
    
    @property
    def available_stock(self):
        """Get available stock in source warehouse"""
        return self.product.get_warehouse_stock(self.inventory_transfer.from_warehouse)
    
    def clean(self):
        """Validate transfer quantity"""
        from django.core.exceptions import ValidationError
        
        # Check if quantity exceeds available stock in source warehouse
        available = self.available_stock
        if self.quantity > available:
            raise ValidationError({
                'quantity': f'Cannot transfer {self.quantity}. Only {available} available in {self.inventory_transfer.from_warehouse.name}.'
            })
    
    def save(self, *args, **kwargs):
        # Auto-set unit price from product if not set
        if self.unit_price == Decimal('0.00'):
            self.unit_price = self.product.purchase_price
        
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ==================== STOCK TRANSACTION ====================
class StockTransaction(TimeStampedModel):
    """Stock Movement Tracking"""
    TRANSACTION_TYPES = [
        ('in', _('Stock In')),
        ('out', _('Stock Out')),
        ('adjustment', _('Adjustment')),
        ('transfer_out', _('Transfer Out')),
        ('transfer_in', _('Transfer In')),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions', verbose_name=_("Product"))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='transactions', verbose_name=_("Warehouse"))
    transaction_type = models.CharField(_("Transaction Type"), max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(_("Balance After"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='stock_transactions', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this stocktransaction"))

    class Meta:
        verbose_name = _("Stock Transaction")
        verbose_name_plural = _("Stock Transactions")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name} - {self.get_transaction_type_display()} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Set warehouse to product's default warehouse if not set
        if not self.warehouse_id:
            if self.product.default_warehouse:
                self.warehouse = self.product.default_warehouse
            else:
                # Fallback to first active warehouse
                first_warehouse = Warehouse.objects.filter(is_active=True).first()
                if first_warehouse:
                    self.warehouse = first_warehouse
        super().save(*args, **kwargs)


# ==================== BANKING MODULE ====================

class BankAccount(TimeStampedModel):
    """Bank Account Master"""
    ACCOUNT_TYPE_CHOICES = [
        ('checking', _('Checking Account')),
        ('savings', _('Savings Account')),
        ('credit', _('Credit Card')),
        ('cash', _('Cash Account')),
    ]
    
    account_name = models.CharField(_("Account Name"), max_length=200)
    account_number = models.CharField(_("Account Number"), max_length=50, unique=True)
    account_type = models.CharField(_("Account Type"), max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='checking')
    bank_name = models.CharField(_("Bank Name"), max_length=200, blank=True)
    branch = models.CharField(_("Branch"), max_length=200, blank=True)
    currency = models.CharField(_("Currency"), max_length=10, default='USD')
    
    opening_balance = models.DecimalField(_("Opening Balance"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    current_balance = models.DecimalField(_("Current Balance"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    is_active = models.BooleanField(_("Active"), default=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Bank Account")
        verbose_name_plural = _("Bank Accounts")
        ordering = ['account_name']
    
    def __str__(self):
        return f"{self.account_name} ({self.account_number})"
    
    def save(self, *args, **kwargs):
        # Set current balance to opening balance on first save
        if not self.pk and self.current_balance == Decimal('0.00'):
            self.current_balance = self.opening_balance
        super().save(*args, **kwargs)


class IncomingPayment(TimeStampedModel):
    """Incoming Payment (Money In) - Header/Info"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', _('Cash')),
        ('check', _('Check')),
        ('bank_transfer', _('Bank Transfer')),
        ('credit_card', _('Credit Card')),
        ('online', _('Online Payment')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('received', _('Received')),
        ('cleared', _('Cleared')),
        ('cancelled', _('Cancelled')),
    ]
    
    payment_number = models.CharField(_("Payment Number"), max_length=50, unique=True, editable=False)
    payment_date = models.DateField(_("Payment Date"), default=timezone.now)
    
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='incoming_payments', verbose_name=_("Customer"))
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name='incoming_payments', verbose_name=_("Bank Account"))
    
    payment_method = models.CharField(_("Payment Method"), max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Payment Details
    amount = models.DecimalField(_("Amount"), max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    check_number = models.CharField(_("Check Number"), max_length=50, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='incoming_payments', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this incomingpayment"))

    class Meta:
        verbose_name = _("Incoming Payment")
        verbose_name_plural = _("Incoming Payments")
        ordering = ['-payment_date', '-created_at']
    
    def __str__(self):
        return f"{self.payment_number} - {self.customer.name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.payment_number:
            last_payment = IncomingPayment.objects.order_by('-id').first()
            if last_payment:
                last_num = int(last_payment.payment_number.split('-')[-1])
                self.payment_number = f"IP-{last_num + 1:06d}"
            else:
                self.payment_number = "IP-000001"
        super().save(*args, **kwargs)


class IncomingPaymentInvoice(TimeStampedModel):
    """Incoming Payment Invoice Allocation - Line Item"""
    incoming_payment = models.ForeignKey(IncomingPayment, on_delete=models.CASCADE, related_name='invoices', verbose_name=_("Incoming Payment"))
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='incoming_payments', verbose_name=_("Invoice"))
    
    amount_allocated = models.DecimalField(_("Amount Allocated"), max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    class Meta:
        verbose_name = _("Incoming Payment Invoice")
        verbose_name_plural = _("Incoming Payment Invoices")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.incoming_payment.payment_number} - {self.invoice.invoice_number} - {self.amount_allocated}"
    
    def clean(self):
        """Validate allocation amount"""
        from django.core.exceptions import ValidationError
        
        if self.amount_allocated > self.invoice.due_amount:
            raise ValidationError({
                'amount_allocated': f'Cannot allocate {self.amount_allocated}. Invoice due amount is {self.invoice.due_amount}.'
            })


class OutgoingPayment(TimeStampedModel):
    """Outgoing Payment (Money Out) - Header/Info"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', _('Cash')),
        ('check', _('Check')),
        ('bank_transfer', _('Bank Transfer')),
        ('credit_card', _('Credit Card')),
        ('online', _('Online Payment')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('cleared', _('Cleared')),
        ('cancelled', _('Cancelled')),
    ]
    
    payment_number = models.CharField(_("Payment Number"), max_length=50, unique=True, editable=False)
    payment_date = models.DateField(_("Payment Date"), default=timezone.now)
    
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='outgoing_payments', verbose_name=_("Supplier"))
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name='outgoing_payments', verbose_name=_("Bank Account"))
    
    payment_method = models.CharField(_("Payment Method"), max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Payment Details
    amount = models.DecimalField(_("Amount"), max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    check_number = models.CharField(_("Check Number"), max_length=50, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='outgoing_payments', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this outgoingpayment"))

    class Meta:
        verbose_name = _("Outgoing Payment")
        verbose_name_plural = _("Outgoing Payments")
        ordering = ['-payment_date', '-created_at']
    
    def __str__(self):
        return f"{self.payment_number} - {self.supplier.name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.payment_number:
            last_payment = OutgoingPayment.objects.order_by('-id').first()
            if last_payment:
                last_num = int(last_payment.payment_number.split('-')[-1])
                self.payment_number = f"OP-{last_num + 1:06d}"
            else:
                self.payment_number = "OP-000001"
        super().save(*args, **kwargs)


class OutgoingPaymentInvoice(TimeStampedModel):
    """Outgoing Payment Invoice Allocation - Line Item"""
    outgoing_payment = models.ForeignKey(OutgoingPayment, on_delete=models.CASCADE, related_name='invoices', verbose_name=_("Outgoing Payment"))
    purchase_invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.PROTECT, related_name='outgoing_payments', verbose_name=_("Purchase Invoice"))
    
    amount_allocated = models.DecimalField(_("Amount Allocated"), max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    class Meta:
        verbose_name = _("Outgoing Payment Invoice")
        verbose_name_plural = _("Outgoing Payment Invoices")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.outgoing_payment.payment_number} - {self.purchase_invoice.invoice_number} - {self.amount_allocated}"
    
    def clean(self):
        """Validate allocation amount"""
        from django.core.exceptions import ValidationError
        
        if self.amount_allocated > self.purchase_invoice.due_amount:
            raise ValidationError({
                'amount_allocated': f'Cannot allocate {self.amount_allocated}. Invoice due amount is {self.purchase_invoice.due_amount}.'
            })


# ==================== ACCOUNTING/FINANCE MODULE ====================

class AccountType(TimeStampedModel):
    """Account Type Classification"""
    TYPE_CHOICES = [
        ('asset', _('Asset')),
        ('liability', _('Liability')),
        ('equity', _('Equity')),
        ('revenue', _('Revenue')),
        ('expense', _('Expense')),
    ]
    
    name = models.CharField(_("Type Name"), max_length=100, unique=True)
    type_category = models.CharField(_("Category"), max_length=20, choices=TYPE_CHOICES)
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Account Type")
        verbose_name_plural = _("Account Types")
        ordering = ['type_category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_category_display()})"


class ChartOfAccounts(TimeStampedModel):
    """Chart of Accounts - GL Accounts"""
    account_code = models.CharField(_("Account Code"), max_length=20, unique=True)
    account_name = models.CharField(_("Account Name"), max_length=200)
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT, related_name='accounts', verbose_name=_("Account Type"))
    parent_account = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_accounts', verbose_name=_("Parent Account"))
    
    currency = models.CharField(_("Currency"), max_length=10, default='USD')
    opening_balance = models.DecimalField(_("Opening Balance"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    current_balance = models.DecimalField(_("Current Balance"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    is_active = models.BooleanField(_("Active"), default=True)
    description = models.TextField(_("Description"), blank=True)
    
    class Meta:
        verbose_name = _("Chart of Account")
        verbose_name_plural = _("Chart of Accounts")
        ordering = ['account_code']
    
    def __str__(self):
        return f"{self.account_code} - {self.account_name}"
    
    def save(self, *args, **kwargs):
        if not self.pk and self.current_balance == Decimal('0.00'):
            self.current_balance = self.opening_balance
        super().save(*args, **kwargs)


class CostCenter(TimeStampedModel):
    """Cost Center for expense tracking"""
    code = models.CharField(_("Cost Center Code"), max_length=20, unique=True)
    name = models.CharField(_("Cost Center Name"), max_length=200)
    parent_cost_center = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_cost_centers', verbose_name=_("Parent Cost Center"))
    
    manager = models.CharField(_("Manager"), max_length=100, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    description = models.TextField(_("Description"), blank=True)
    
    class Meta:
        verbose_name = _("Cost Center")
        verbose_name_plural = _("Cost Centers")
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Project(TimeStampedModel):
    """Project for tracking revenues and expenses"""
    STATUS_CHOICES = [
        ('planning', _('Planning')),
        ('active', _('Active')),
        ('on_hold', _('On Hold')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    project_code = models.CharField(_("Project Code"), max_length=20, unique=True)
    project_name = models.CharField(_("Project Name"), max_length=200)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', verbose_name=_("Customer"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='planning')
    start_date = models.DateField(_("Start Date"), null=True, blank=True)
    end_date = models.DateField(_("End Date"), null=True, blank=True)
    
    project_manager = models.CharField(_("Project Manager"), max_length=100, blank=True)
    budget_amount = models.DecimalField(_("Budget Amount"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    actual_cost = models.DecimalField(_("Actual Cost"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    is_active = models.BooleanField(_("Active"), default=True)
    description = models.TextField(_("Description"), blank=True)
    
    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.project_code} - {self.project_name}"
    
    @property
    def budget_variance(self):
        """Calculate budget variance"""
        return self.budget_amount - self.actual_cost
    
    @property
    def budget_utilization_percentage(self):
        """Calculate budget utilization percentage"""
        if self.budget_amount > 0:
            return (self.actual_cost / self.budget_amount) * 100
        return Decimal('0.00')


class JournalEntry(TimeStampedModel):
    """Journal Entry - Header/Info"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('posted', _('Posted')),
        ('cancelled', _('Cancelled')),
    ]
    
    entry_number = models.CharField(_("Entry Number"), max_length=50, unique=True, editable=False)
    entry_date = models.DateField(_("Entry Date"), default=timezone.now)
    posting_date = models.DateField(_("Posting Date"), null=True, blank=True)
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    
    # Optional links
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_entries', verbose_name=_("Project"))
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_entries', verbose_name=_("Cost Center"))
    
    # Totals
    total_debit = models.DecimalField(_("Total Debit"), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    total_credit = models.DecimalField(_("Total Credit"), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='journal_entries', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this journalentry"))

    class Meta:
        verbose_name = _("Journal Entry")
        verbose_name_plural = _("Journal Entries")
        ordering = ['-entry_date', '-created_at']
    
    def __str__(self):
        return f"{self.entry_number} - {self.entry_date}"
    
    def save(self, *args, **kwargs):
        if not self.entry_number:
            last_entry = JournalEntry.objects.order_by('-id').first()
            if last_entry:
                last_num = int(last_entry.entry_number.split('-')[-1])
                self.entry_number = f"JE-{last_num + 1:06d}"
            else:
                self.entry_number = "JE-000001"
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate total debit and credit"""
        lines = self.lines.all()
        self.total_debit = sum(line.debit for line in lines)
        self.total_credit = sum(line.credit for line in lines)
        self.save(update_fields=['total_debit', 'total_credit'])
    
    @property
    def is_balanced(self):
        """Check if entry is balanced"""
        return self.total_debit == self.total_credit
    
    def clean(self):
        """Validate journal entry"""
        from django.core.exceptions import ValidationError
        
        if self.status == 'posted':
            if not self.is_balanced:
                raise ValidationError('Journal entry must be balanced (Debit = Credit) before posting.')


class JournalEntryLine(TimeStampedModel):
    """Journal Entry Line - Line Item"""
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Journal Entry"))
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, related_name='journal_lines', verbose_name=_("Account"))
    
    description = models.CharField(_("Description"), max_length=200, blank=True)
    debit = models.DecimalField(_("Debit"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    credit = models.DecimalField(_("Credit"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Optional dimensions
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_lines', verbose_name=_("Project"))
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_lines', verbose_name=_("Cost Center"))
    
    class Meta:
        verbose_name = _("Journal Entry Line")
        verbose_name_plural = _("Journal Entry Lines")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.journal_entry.entry_number} - {self.account.account_code}"
    
    def clean(self):
        """Validate journal line"""
        from django.core.exceptions import ValidationError
        
        if self.debit > 0 and self.credit > 0:
            raise ValidationError('A line cannot have both debit and credit amounts.')
        
        if self.debit == 0 and self.credit == 0:
            raise ValidationError('A line must have either debit or credit amount.')
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update parent totals
        self.journal_entry.calculate_totals()


class FiscalYear(TimeStampedModel):
    """Fiscal Year"""
    year_name = models.CharField(_("Year Name"), max_length=50, unique=True)
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    is_closed = models.BooleanField(_("Closed"), default=False)
    
    class Meta:
        verbose_name = _("Fiscal Year")
        verbose_name_plural = _("Fiscal Years")
        ordering = ['-start_date']
    
    def __str__(self):
        return self.year_name
    
    def clean(self):
        """Validate fiscal year"""
        from django.core.exceptions import ValidationError
        
        if self.start_date >= self.end_date:
            raise ValidationError('End date must be after start date.')


class Budget(TimeStampedModel):
    """Budget Planning"""
    budget_name = models.CharField(_("Budget Name"), max_length=200)
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, related_name='budgets', verbose_name=_("Fiscal Year"))
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, related_name='budgets', verbose_name=_("Account"))
    
    # Optional dimensions
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='budgets', verbose_name=_("Project"))
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='budgets', verbose_name=_("Cost Center"))
    
    budget_amount = models.DecimalField(_("Budget Amount"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    actual_amount = models.DecimalField(_("Actual Amount"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    is_active = models.BooleanField(_("Active"), default=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='budgets', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this budget"))

    class Meta:
        verbose_name = _("Budget")
        verbose_name_plural = _("Budgets")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.budget_name} - {self.account.account_code}"
    
    @property
    def variance(self):
        """Calculate budget variance"""
        return self.budget_amount - self.actual_amount
    
    @property
    def utilization_percentage(self):
        """Calculate budget utilization percentage"""
        if self.budget_amount > 0:
            return (self.actual_amount / self.budget_amount) * 100
        return Decimal('0.00')


# ==================== CURRENCY & EXCHANGE RATE ====================

class Currency(TimeStampedModel):
    """Currency Master"""
    code = models.CharField(_("Currency Code"), max_length=3, unique=True, help_text=_("ISO 4217 code (e.g., USD, BDT, EUR)"))
    name = models.CharField(_("Currency Name"), max_length=100)
    symbol = models.CharField(_("Symbol"), max_length=10, help_text=_("e.g., $, ৳, €"))
    decimal_places = models.PositiveSmallIntegerField(_("Decimal Places"), default=2)
    is_base_currency = models.BooleanField(_("Base Currency"), default=False, help_text=_("Only one currency can be base"))
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")
        ordering = ['-is_base_currency', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one base currency
        if self.is_base_currency:
            Currency.objects.filter(is_base_currency=True).exclude(pk=self.pk).update(is_base_currency=False)
        super().save(*args, **kwargs)


class ExchangeRate(TimeStampedModel):
    """Exchange Rate for Currency Conversion"""
    from_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='rates_from', verbose_name=_("From Currency"))
    to_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='rates_to', verbose_name=_("To Currency"))
    rate = models.DecimalField(_("Exchange Rate"), max_digits=18, decimal_places=6, validators=[MinValueValidator(Decimal('0.000001'))])
    effective_date = models.DateField(_("Effective Date"), default=timezone.now)
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Exchange Rate")
        verbose_name_plural = _("Exchange Rates")
        ordering = ['-effective_date', 'from_currency']
        unique_together = ['from_currency', 'to_currency', 'effective_date']
    
    def __str__(self):
        return f"1 {self.from_currency.code} = {self.rate} {self.to_currency.code} ({self.effective_date})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.from_currency == self.to_currency:
            raise ValidationError(_("From and To currency cannot be the same."))


# ==================== TAX CONFIGURATION ====================

class TaxType(TimeStampedModel):
    """Tax Type Master (VAT, GST, etc.)"""
    TAX_CATEGORY_CHOICES = [
        ('sales', _('Sales Tax')),
        ('purchase', _('Purchase Tax')),
        ('both', _('Both Sales & Purchase')),
    ]
    
    name = models.CharField(_("Tax Name"), max_length=100, unique=True)
    code = models.CharField(_("Tax Code"), max_length=20, unique=True)
    category = models.CharField(_("Category"), max_length=20, choices=TAX_CATEGORY_CHOICES, default='both')
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    
    # Accounting Integration
    sales_account = models.ForeignKey(ChartOfAccounts, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_tax_types', verbose_name=_("Sales Tax Account"))
    purchase_account = models.ForeignKey(ChartOfAccounts, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_tax_types', verbose_name=_("Purchase Tax Account"))
    
    class Meta:
        verbose_name = _("Tax Type")
        verbose_name_plural = _("Tax Types")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class TaxRate(TimeStampedModel):
    """Tax Rate Configuration"""
    tax_type = models.ForeignKey(TaxType, on_delete=models.PROTECT, related_name='rates', verbose_name=_("Tax Type"))
    name = models.CharField(_("Rate Name"), max_length=100, help_text=_("e.g., Standard Rate, Reduced Rate"))
    rate = models.DecimalField(_("Rate (%)"), max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    is_default = models.BooleanField(_("Default Rate"), default=False)
    is_active = models.BooleanField(_("Active"), default=True)
    effective_from = models.DateField(_("Effective From"), default=timezone.now)
    effective_to = models.DateField(_("Effective To"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Tax Rate")
        verbose_name_plural = _("Tax Rates")
        ordering = ['tax_type', '-is_default', 'rate']
    
    def __str__(self):
        return f"{self.tax_type.code} - {self.name} ({self.rate}%)"
    
    def save(self, *args, **kwargs):
        # Ensure only one default rate per tax type
        if self.is_default:
            TaxRate.objects.filter(tax_type=self.tax_type, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ==================== PAYMENT TERMS ====================

class PaymentTerm(TimeStampedModel):
    """Payment Terms Master"""
    name = models.CharField(_("Term Name"), max_length=100, unique=True)
    code = models.CharField(_("Term Code"), max_length=20, unique=True)
    days = models.PositiveIntegerField(_("Days"), default=0, help_text=_("Number of days for payment"))
    description = models.TextField(_("Description"), blank=True)
    is_default = models.BooleanField(_("Default"), default=False)
    is_active = models.BooleanField(_("Active"), default=True)
    
    # Discount for early payment
    discount_days = models.PositiveIntegerField(_("Discount Days"), default=0, help_text=_("Days within which discount applies"))
    discount_percentage = models.DecimalField(_("Discount (%)"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = _("Payment Term")
        verbose_name_plural = _("Payment Terms")
        ordering = ['days', 'name']
    
    def __str__(self):
        if self.days == 0:
            return f"{self.code} - {self.name} (Immediate)"
        return f"{self.code} - {self.name} ({self.days} days)"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            PaymentTerm.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ==================== UNIT OF MEASURE (UOM) ====================

class UnitOfMeasure(TimeStampedModel):
    """Unit of Measure Master"""
    UOM_TYPE_CHOICES = [
        ('unit', _('Unit')),
        ('weight', _('Weight')),
        ('volume', _('Volume')),
        ('length', _('Length')),
        ('area', _('Area')),
        ('time', _('Time')),
    ]
    
    name = models.CharField(_("Unit Name"), max_length=50, unique=True)
    code = models.CharField(_("Unit Code"), max_length=10, unique=True)
    uom_type = models.CharField(_("Type"), max_length=20, choices=UOM_TYPE_CHOICES, default='unit')
    is_base_unit = models.BooleanField(_("Base Unit"), default=False, help_text=_("Base unit for this type"))
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Unit of Measure")
        verbose_name_plural = _("Units of Measure")
        ordering = ['uom_type', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class UOMConversion(TimeStampedModel):
    """UOM Conversion Rules"""
    from_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name='conversions_from', verbose_name=_("From UOM"))
    to_uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name='conversions_to', verbose_name=_("To UOM"))
    conversion_factor = models.DecimalField(_("Conversion Factor"), max_digits=18, decimal_places=6, validators=[MinValueValidator(Decimal('0.000001'))], help_text=_("1 From UOM = X To UOM"))
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("UOM Conversion")
        verbose_name_plural = _("UOM Conversions")
        unique_together = ['from_uom', 'to_uom']
        ordering = ['from_uom', 'to_uom']
    
    def __str__(self):
        return f"1 {self.from_uom.code} = {self.conversion_factor} {self.to_uom.code}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.from_uom == self.to_uom:
            raise ValidationError(_("From and To UOM cannot be the same."))


# ==================== PRICE LIST ====================

class PriceList(TimeStampedModel):
    """Price List Master"""
    PRICE_TYPE_CHOICES = [
        ('sales', _('Sales Price')),
        ('purchase', _('Purchase Price')),
    ]
    
    name = models.CharField(_("Price List Name"), max_length=100, unique=True)
    code = models.CharField(_("Price List Code"), max_length=20, unique=True)
    price_type = models.CharField(_("Price Type"), max_length=20, choices=PRICE_TYPE_CHOICES, default='sales')
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='price_lists', verbose_name=_("Currency"), null=True, blank=True)
    
    is_default = models.BooleanField(_("Default"), default=False)
    is_active = models.BooleanField(_("Active"), default=True)
    
    # Validity
    valid_from = models.DateField(_("Valid From"), default=timezone.now)
    valid_to = models.DateField(_("Valid To"), null=True, blank=True)
    
    description = models.TextField(_("Description"), blank=True)
    
    class Meta:
        verbose_name = _("Price List")
        verbose_name_plural = _("Price Lists")
        ordering = ['price_type', '-is_default', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.get_price_type_display()})"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            PriceList.objects.filter(price_type=self.price_type, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class PriceListItem(TimeStampedModel):
    """Price List Item - Product Prices"""
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='items', verbose_name=_("Price List"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_list_items', verbose_name=_("Product"))
    
    unit_price = models.DecimalField(_("Unit Price"), max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    min_quantity = models.DecimalField(_("Minimum Quantity"), max_digits=10, decimal_places=2, default=Decimal('1.00'), help_text=_("Minimum quantity for this price"))
    
    # Optional discount
    discount_percentage = models.DecimalField(_("Discount (%)"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Price List Item")
        verbose_name_plural = _("Price List Items")
        unique_together = ['price_list', 'product', 'min_quantity']
        ordering = ['price_list', 'product', 'min_quantity']
    
    def __str__(self):
        return f"{self.price_list.code} - {self.product.name}: {self.unit_price}"
    
    @property
    def net_price(self):
        """Calculate net price after discount"""
        if self.discount_percentage > 0:
            discount = self.unit_price * (self.discount_percentage / Decimal('100'))
            return self.unit_price - discount
        return self.unit_price


# ==================== DISCOUNT MANAGEMENT ====================

class DiscountType(TimeStampedModel):
    """Discount Type Master"""
    DISCOUNT_METHOD_CHOICES = [
        ('percentage', _('Percentage')),
        ('fixed', _('Fixed Amount')),
    ]
    
    APPLY_ON_CHOICES = [
        ('order', _('Whole Order')),
        ('product', _('Specific Product')),
        ('category', _('Product Category')),
        ('customer', _('Specific Customer')),
        ('customer_group', _('Customer Group')),
    ]
    
    name = models.CharField(_("Discount Name"), max_length=100, unique=True)
    code = models.CharField(_("Discount Code"), max_length=20, unique=True)
    discount_method = models.CharField(_("Method"), max_length=20, choices=DISCOUNT_METHOD_CHOICES, default='percentage')
    apply_on = models.CharField(_("Apply On"), max_length=20, choices=APPLY_ON_CHOICES, default='order')
    
    value = models.DecimalField(_("Value"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], help_text=_("Percentage or Fixed Amount"))
    max_discount_amount = models.DecimalField(_("Max Discount Amount"), max_digits=10, decimal_places=2, null=True, blank=True, help_text=_("Maximum discount cap for percentage"))
    min_order_amount = models.DecimalField(_("Min Order Amount"), max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text=_("Minimum order value to apply discount"))
    
    # Validity
    valid_from = models.DateField(_("Valid From"), default=timezone.now)
    valid_to = models.DateField(_("Valid To"), null=True, blank=True)
    
    # Usage limits
    usage_limit = models.PositiveIntegerField(_("Usage Limit"), null=True, blank=True, help_text=_("Total times this discount can be used"))
    usage_count = models.PositiveIntegerField(_("Usage Count"), default=0, editable=False)
    per_customer_limit = models.PositiveIntegerField(_("Per Customer Limit"), null=True, blank=True)
    
    is_active = models.BooleanField(_("Active"), default=True)
    description = models.TextField(_("Description"), blank=True)
    
    class Meta:
        verbose_name = _("Discount Type")
        verbose_name_plural = _("Discount Types")
        ordering = ['name']
    
    def __str__(self):
        if self.discount_method == 'percentage':
            return f"{self.code} - {self.name} ({self.value}%)"
        return f"{self.code} - {self.name} ({self.value} fixed)"
    
    def is_valid(self):
        """Check if discount is currently valid"""
        from django.utils import timezone
        today = timezone.now().date()
        if not self.is_active:
            return False
        if self.valid_from and today < self.valid_from:
            return False
        if self.valid_to and today > self.valid_to:
            return False
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        return True
    
    def calculate_discount(self, amount):
        """Calculate discount amount"""
        if self.discount_method == 'percentage':
            discount = amount * (self.value / Decimal('100'))
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount
        return min(self.value, amount)


class DiscountRule(TimeStampedModel):
    """Discount Rules - Conditions for applying discounts"""
    discount_type = models.ForeignKey(DiscountType, on_delete=models.CASCADE, related_name='rules', verbose_name=_("Discount Type"))
    
    # Conditions
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='discount_rules', verbose_name=_("Product"))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='discount_rules', verbose_name=_("Category"))
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name='discount_rules', verbose_name=_("Customer"))
    
    min_quantity = models.DecimalField(_("Min Quantity"), max_digits=10, decimal_places=2, default=Decimal('1.00'))
    
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Discount Rule")
        verbose_name_plural = _("Discount Rules")
        ordering = ['discount_type', 'id']
    
    def __str__(self):
        return f"{self.discount_type.code} - Rule #{self.id}"


# ==================== STOCK ADJUSTMENT ====================

class StockAdjustment(TimeStampedModel):
    """Stock Adjustment - Header/Info"""
    ADJUSTMENT_TYPE_CHOICES = [
        ('opening', _('Opening Stock')),
        ('physical_count', _('Physical Count')),
        ('damage', _('Damage/Loss')),
        ('correction', _('Correction')),
        ('write_off', _('Write Off')),
        ('found', _('Found/Recovered')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending Approval')),
        ('approved', _('Approved')),
        ('posted', _('Posted')),
        ('rejected', _('Rejected')),
        ('cancelled', _('Cancelled')),
    ]
    
    adjustment_number = models.CharField(_("Adjustment Number"), max_length=50, unique=True, editable=False)
    adjustment_date = models.DateField(_("Adjustment Date"), default=timezone.now)
    adjustment_type = models.CharField(_("Adjustment Type"), max_length=20, choices=ADJUSTMENT_TYPE_CHOICES, default='physical_count')
    
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='stock_adjustments', verbose_name=_("Warehouse"))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    reason = models.TextField(_("Reason"), blank=True)
    
    # Approval
    requested_by = models.CharField(_("Requested By"), max_length=100, blank=True)
    approved_by = models.CharField(_("Approved By"), max_length=100, blank=True)
    approved_date = models.DateTimeField(_("Approved Date"), null=True, blank=True)
    
    # Totals
    total_increase = models.DecimalField(_("Total Increase"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    total_decrease = models.DecimalField(_("Total Decrease"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    total_value = models.DecimalField(_("Total Value"), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Stock Adjustment")
        verbose_name_plural = _("Stock Adjustments")
        ordering = ['-adjustment_date', '-created_at']
    
    def __str__(self):
        return f"{self.adjustment_number} - {self.get_adjustment_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.adjustment_number:
            last = StockAdjustment.objects.order_by('-id').first()
            if last:
                last_num = int(last.adjustment_number.split('-')[-1])
                self.adjustment_number = f"ADJ-{last_num + 1:06d}"
            else:
                self.adjustment_number = "ADJ-000001"
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate totals from items"""
        items = self.items.all()
        self.total_increase = sum(item.quantity_difference for item in items if item.quantity_difference > 0)
        self.total_decrease = abs(sum(item.quantity_difference for item in items if item.quantity_difference < 0))
        self.total_value = sum(item.value_difference for item in items)
        self.save(update_fields=['total_increase', 'total_decrease', 'total_value'])


class StockAdjustmentItem(TimeStampedModel):
    """Stock Adjustment Item - Line Item"""
    stock_adjustment = models.ForeignKey(StockAdjustment, on_delete=models.CASCADE, related_name='items', verbose_name=_("Stock Adjustment"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    system_quantity = models.DecimalField(_("System Quantity"), max_digits=10, decimal_places=2, default=Decimal('0.00'), editable=False, help_text=_("Current stock in system (auto-filled)"))
    actual_quantity = models.DecimalField(_("Actual/New Quantity"), max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text=_("Enter the actual/new quantity"))
    quantity_difference = models.DecimalField(_("Difference"), max_digits=10, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    unit_cost = models.DecimalField(_("Unit Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    value_difference = models.DecimalField(_("Value Difference"), max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    reason = models.CharField(_("Item Reason"), max_length=200, blank=True)
    
    class Meta:
        verbose_name = _("Stock Adjustment Item")
        verbose_name_plural = _("Stock Adjustment Items")
        ordering = ['id']
    
    def __str__(self):
        return f"{self.stock_adjustment.adjustment_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Auto-set system quantity from current warehouse stock
        if self.product and self.stock_adjustment.warehouse:
            warehouse_stock = ProductWarehouseStock.objects.filter(
                product=self.product, 
                warehouse=self.stock_adjustment.warehouse
            ).first()
            self.system_quantity = warehouse_stock.quantity if warehouse_stock else Decimal('0.00')
        
        # Auto-set unit cost from product if not set
        if self.unit_cost == Decimal('0.00') and self.product:
            self.unit_cost = self.product.purchase_price
        
        # Calculate difference (actual - system)
        self.quantity_difference = self.actual_quantity - self.system_quantity
        self.value_difference = self.quantity_difference * self.unit_cost
        
        super().save(*args, **kwargs)
        self.stock_adjustment.calculate_totals()


# ==================== APPROVAL WORKFLOW ====================

class ApprovalWorkflow(TimeStampedModel):
    """Approval Workflow Configuration"""
    DOCUMENT_TYPE_CHOICES = [
        ('sales_quotation', _('Sales Quotation')),
        ('sales_order', _('Sales Order')),
        ('purchase_quotation', _('Purchase Quotation')),
        ('purchase_order', _('Purchase Order')),
        ('invoice', _('Invoice')),
        ('purchase_invoice', _('Purchase Invoice')),
        ('stock_adjustment', _('Stock Adjustment')),
        ('journal_entry', _('Journal Entry')),
        ('payment', _('Payment')),
    ]
    
    name = models.CharField(_("Workflow Name"), max_length=100)
    document_type = models.CharField(_("Document Type"), max_length=30, choices=DOCUMENT_TYPE_CHOICES, unique=True)
    
    is_active = models.BooleanField(_("Active"), default=True)
    description = models.TextField(_("Description"), blank=True)
    
    class Meta:
        verbose_name = _("Approval Workflow")
        verbose_name_plural = _("Approval Workflows")
        ordering = ['document_type']
    
    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"


class ApprovalLevel(TimeStampedModel):
    """Approval Levels within a Workflow"""
    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.CASCADE, related_name='levels', verbose_name=_("Workflow"))
    
    level = models.PositiveSmallIntegerField(_("Level"), default=1)
    name = models.CharField(_("Level Name"), max_length=100)
    
    # Conditions
    min_amount = models.DecimalField(_("Min Amount"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    max_amount = models.DecimalField(_("Max Amount"), max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Approvers (can be user or role based)
    approver_user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approval_levels', verbose_name=_("Approver User"))
    approver_role = models.CharField(_("Approver Role"), max_length=100, blank=True, help_text=_("Role/Group name for approval"))
    
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Approval Level")
        verbose_name_plural = _("Approval Levels")
        ordering = ['workflow', 'level']
        unique_together = ['workflow', 'level']
    
    def __str__(self):
        return f"{self.workflow.name} - Level {self.level}: {self.name}"


class ApprovalRequest(TimeStampedModel):
    """Approval Request - Tracks approval status for documents"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('cancelled', _('Cancelled')),
    ]
    
    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.PROTECT, related_name='requests', verbose_name=_("Workflow"))
    
    # Generic relation to any document
    document_type = models.CharField(_("Document Type"), max_length=30)
    document_id = models.PositiveIntegerField(_("Document ID"))
    document_number = models.CharField(_("Document Number"), max_length=50)
    document_amount = models.DecimalField(_("Document Amount"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    current_level = models.PositiveSmallIntegerField(_("Current Level"), default=1)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    requested_by = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='approval_requests', verbose_name=_("Requested By"))
    requested_date = models.DateTimeField(_("Requested Date"), auto_now_add=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Approval Request")
        verbose_name_plural = _("Approval Requests")
        ordering = ['-requested_date']
    
    def __str__(self):
        return f"{self.document_number} - {self.get_status_display()}"


class ApprovalHistory(TimeStampedModel):
    """Approval History - Audit trail for approvals"""
    ACTION_CHOICES = [
        ('submitted', _('Submitted')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('returned', _('Returned for Revision')),
        ('cancelled', _('Cancelled')),
    ]
    
    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='history', verbose_name=_("Approval Request"))
    
    level = models.PositiveSmallIntegerField(_("Level"))
    action = models.CharField(_("Action"), max_length=20, choices=ACTION_CHOICES)
    action_by = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='approval_actions', verbose_name=_("Action By"))
    action_date = models.DateTimeField(_("Action Date"), auto_now_add=True)
    
    comments = models.TextField(_("Comments"), blank=True)
    
    class Meta:
        verbose_name = _("Approval History")
        verbose_name_plural = _("Approval Histories")
        ordering = ['-action_date']
    
    def __str__(self):
        return f"{self.approval_request.document_number} - Level {self.level} - {self.get_action_display()}"


# ==================== NOTIFICATION / ALERT ====================

class NotificationType(TimeStampedModel):
    """Notification Type Configuration"""
    TRIGGER_CHOICES = [
        ('low_stock', _('Low Stock Alert')),
        ('payment_due', _('Payment Due')),
        ('payment_overdue', _('Payment Overdue')),
        ('order_status', _('Order Status Change')),
        ('approval_pending', _('Approval Pending')),
        ('approval_completed', _('Approval Completed')),
        ('document_created', _('Document Created')),
        ('price_change', _('Price Change')),
        ('expiry_alert', _('Expiry Alert')),
        ('custom', _('Custom')),
    ]
    
    CHANNEL_CHOICES = [
        ('system', _('System Notification')),
        ('email', _('Email')),
        ('sms', _('SMS')),
        ('both', _('Email & SMS')),
    ]
    
    name = models.CharField(_("Notification Name"), max_length=100, unique=True)
    code = models.CharField(_("Code"), max_length=30, unique=True)
    trigger = models.CharField(_("Trigger"), max_length=30, choices=TRIGGER_CHOICES)
    channel = models.CharField(_("Channel"), max_length=20, choices=CHANNEL_CHOICES, default='system')
    
    subject_template = models.CharField(_("Subject Template"), max_length=200, help_text=_("Use {variable} for dynamic content"))
    message_template = models.TextField(_("Message Template"), help_text=_("Use {variable} for dynamic content"))
    
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Notification Type")
        verbose_name_plural = _("Notification Types")
        ordering = ['trigger', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class NotificationSetting(TimeStampedModel):
    """User Notification Settings"""
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='notification_settings', verbose_name=_("User"))
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE, related_name='user_settings', verbose_name=_("Notification Type"))
    
    is_enabled = models.BooleanField(_("Enabled"), default=True)
    email_enabled = models.BooleanField(_("Email Enabled"), default=True)
    sms_enabled = models.BooleanField(_("SMS Enabled"), default=False)
    
    class Meta:
        verbose_name = _("Notification Setting")
        verbose_name_plural = _("Notification Settings")
        unique_together = ['user', 'notification_type']
        ordering = ['user', 'notification_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.notification_type.name}"


class Notification(TimeStampedModel):
    """Notification - Individual notifications sent to users"""
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('normal', _('Normal')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]
    
    STATUS_CHOICES = [
        ('unread', _('Unread')),
        ('read', _('Read')),
        ('archived', _('Archived')),
    ]
    
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='notifications', verbose_name=_("User"))
    notification_type = models.ForeignKey(NotificationType, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications', verbose_name=_("Notification Type"))
    
    title = models.CharField(_("Title"), max_length=200)
    message = models.TextField(_("Message"))
    
    priority = models.CharField(_("Priority"), max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(_("Status"), max_length=10, choices=STATUS_CHOICES, default='unread')
    
    # Link to related document
    link_url = models.CharField(_("Link URL"), max_length=500, blank=True)
    document_type = models.CharField(_("Document Type"), max_length=50, blank=True)
    document_id = models.PositiveIntegerField(_("Document ID"), null=True, blank=True)
    
    # Delivery status
    email_sent = models.BooleanField(_("Email Sent"), default=False)
    sms_sent = models.BooleanField(_("SMS Sent"), default=False)
    
    read_at = models.DateTimeField(_("Read At"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if self.status == 'unread':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])


class AlertRule(TimeStampedModel):
    """Alert Rules - Automated alert triggers"""
    CONDITION_TYPE_CHOICES = [
        ('stock_below', _('Stock Below Threshold')),
        ('days_before_due', _('Days Before Due Date')),
        ('days_overdue', _('Days Overdue')),
        ('amount_above', _('Amount Above Threshold')),
        ('amount_below', _('Amount Below Threshold')),
    ]
    
    name = models.CharField(_("Rule Name"), max_length=100)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE, related_name='alert_rules', verbose_name=_("Notification Type"))
    
    condition_type = models.CharField(_("Condition Type"), max_length=30, choices=CONDITION_TYPE_CHOICES)
    threshold_value = models.DecimalField(_("Threshold Value"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Optional filters
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='alert_rules', verbose_name=_("Product"))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='alert_rules', verbose_name=_("Category"))
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name='alert_rules', verbose_name=_("Customer"))
    
    # Recipients
    notify_users = models.ManyToManyField('auth.User', blank=True, related_name='alert_rules', verbose_name=_("Notify Users"))
    
    is_active = models.BooleanField(_("Active"), default=True)
    last_triggered = models.DateTimeField(_("Last Triggered"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Alert Rule")
        verbose_name_plural = _("Alert Rules")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_condition_type_display()})"


# ==================== PAYMENT METHOD (MASTER DATA) ====================

class PaymentMethod(TimeStampedModel):
    """Payment Method - Master data for payment options"""
    PAYMENT_TYPE_CHOICES = [
        ('cash', _('Cash')),
        ('card', _('Card')),
        ('mobile', _('Mobile Payment')),
        ('bank', _('Bank Transfer')),
        ('credit', _('Credit')),
    ]
    
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("Code"), max_length=20, unique=True)
    payment_type = models.CharField(_("Payment Type"), max_length=20, choices=PAYMENT_TYPE_CHOICES)
    
    # For mobile/bank payments
    account_number = models.CharField(_("Account Number"), max_length=50, blank=True)
    account_name = models.CharField(_("Account Name"), max_length=100, blank=True)
    
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Payment Method")
        verbose_name_plural = _("Payment Methods")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_payment_type_display()})"


# ==================== USER PROFILE (FOR POS) ====================

class UserProfile(TimeStampedModel):
    """User Profile - Links user to branch/warehouse and POS settings"""
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile', verbose_name=_("User"))

    # Branch/Location settings
    branch = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='branch_users', verbose_name=_("Branch/Warehouse"), help_text=_("User's assigned branch/warehouse"))

    # Default settings for this user's operations
    default_customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_users', verbose_name=_("Default Customer"), help_text=_("Shop/Walk-in customer for this user"))

    # POS Settings
    allow_discount = models.BooleanField(_("Allow Discount"), default=True)
    max_discount_percent = models.DecimalField(_("Max Discount %"), max_digits=5, decimal_places=2, default=Decimal('10.00'))

    # Access Control
    can_access_all_branches = models.BooleanField(_("Can Access All Branches"), default=False, help_text=_("If True, user can see data from all branches"))

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")
    
    def __str__(self):
        branch_name = self.branch.name if self.branch else "No Branch"
        return f"{self.user.username} - {branch_name}"
    
    @property
    def default_warehouse(self):
        """Backward compatibility property"""
        return self.branch
    
    def get_accessible_branches(self):
        """Get list of branches this user can access"""
        if self.can_access_all_branches:
            return Warehouse.objects.filter(is_active=True)
        elif self.branch:
            return Warehouse.objects.filter(id=self.branch.id, is_active=True)
        else:
            return Warehouse.objects.none()

    def __str__(self):
        branch_name = self.branch.name if self.branch else "No Branch"
        return f"{self.user.username} - {branch_name}"

    @property
    def default_warehouse(self):
        """Backward compatibility property"""
        return self.branch

    def get_accessible_branches(self):
        """Get list of branches this user can access"""
        if self.can_access_all_branches:
            return Warehouse.objects.filter(is_active=True)
        elif self.branch:
            return Warehouse.objects.filter(id=self.branch.id, is_active=True)
        else:
            return Warehouse.objects.none()



# ==================== QUICK SALE (SIMPLIFIED POS) ====================

# ==================== SHIPPING AREA ====================

class ShippingArea(TimeStampedModel):
    """Shipping Area - Define shipping charges by area"""
    area_name = models.CharField(_("Area Name"), max_length=200, unique=True)
    shipping_charge = models.DecimalField(_("Shipping Charge"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Shipping Area")
        verbose_name_plural = _("Shipping Areas")
        ordering = ['area_name']
    
    def __str__(self):
        return f"{self.area_name} - ৳{self.shipping_charge}"


# ==================== QUICK SALE (POS) ====================

class QuickSale(TimeStampedModel):
    """Quick Sale - Simplified POS for retail sales
    
    This is a simplified version of POS that doesn't require sessions.
    Just scan products, enter quantity, and complete the sale.
    """
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),  # Added for return support
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', _('Cash')),
        ('card', _('Card')),
        ('mobile', _('Mobile')),
        ('mixed', _('Mixed')),
    ]
    
    # Auto-generated
    sale_number = models.CharField(_("Sale #"), max_length=50, unique=True, editable=False)
    sale_date = models.DateField(_("Sale Date"), default=timezone.now)
    
    # POS Session (optional - for advanced POS)
    session = models.ForeignKey(
        'POSSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quick_sales',
        verbose_name=_("POS Session"),
        help_text=_("Optional - link to POS session for cash management")
    )
    
    # User who made the sale (auto-filled)
    user = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='quick_sales', verbose_name=_("Cashier"))
    
    # Customer info (optional - for walk-in just leave blank)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True, related_name='quick_sales', verbose_name=_("Customer"), help_text=_("Leave blank for walk-in"))
    customer_name = models.CharField(_("Customer Name"), max_length=200, blank=True, help_text=_("Optional - for receipt"))
    customer_phone = models.CharField(_("Phone"), max_length=20, blank=True)
    
    # Warehouse/Branch (auto-filled from user profile)
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, related_name='quick_sales', verbose_name=_("Branch/Warehouse"))
    
    # Amounts (auto-calculated)
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(_("Discount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Tax
    tax_percentage = models.DecimalField(_("Tax %"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Shipping
    shipping_area = models.ForeignKey(
        'ShippingArea',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quick_sales',
        verbose_name=_("Shipping Area")
    )
    shipping_charge = models.DecimalField(_("Shipping Charge"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    total_amount = models.DecimalField(_("Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Payment
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='quick_sales',
        verbose_name=_("Payment Method"),
        help_text=_("Primary payment method for this sale")
    )
    amount_received = models.DecimalField(_("Amount Received"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    change_amount = models.DecimalField(_("Change"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(_("Due Amount"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Quick Sale")
        verbose_name_plural = _("Quick Sales")
        ordering = ['-created_at']
    
    def __str__(self):
        return self.sale_number
    
    def save(self, *args, **kwargs):
        # Track old status before save
        old_status = None
        if self.pk:
            try:
                old_status = QuickSale.objects.get(pk=self.pk).status
            except QuickSale.DoesNotExist:
                pass
        
        # Generate sale number
        if not self.sale_number:
            today = timezone.now().strftime('%Y%m%d')
            last_sale = QuickSale.objects.filter(
                sale_number__startswith=f"QS-{today}"
            ).order_by('-id').first()
            
            if last_sale:
                last_num = int(last_sale.sale_number.split('-')[-1])
                self.sale_number = f"QS-{today}-{last_num + 1:04d}"
            else:
                self.sale_number = f"QS-{today}-0001"
        
        # Auto-fill branch from user profile if not set
        if not self.branch_id and self.user_id:
            try:
                profile = self.user.profile
                if profile.branch:
                    self.branch = profile.branch
            except UserProfile.DoesNotExist:
                pass
        
        # Auto-fill customer from user profile if not set
        if not self.customer_id and self.user_id:
            try:
                profile = self.user.profile
                if profile.default_customer:
                    self.customer = profile.default_customer
            except UserProfile.DoesNotExist:
                pass
        
        # Check if this is a new record
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # ==================== STOCK MANAGEMENT ====================
        # Import utility functions
        from erp.utils.pos_utils import update_pos_stock, reverse_pos_stock, process_pos_refund
        
        # NEW SALE: Created directly with status='completed'
        if is_new and self.status == 'completed':
            update_pos_stock(self)
        
        # EXISTING SALE: Status changed to completed
        elif not is_new and self.status == 'completed' and old_status != 'completed':
            update_pos_stock(self)
        
        # Sale refunded (completed → refunded)
        elif self.status == 'refunded' and old_status == 'completed':
            process_pos_refund(self)
        
        # Sale cancelled or reverted to draft (completed → draft/cancelled)
        elif old_status == 'completed' and self.status in ['draft', 'cancelled']:
            reverse_pos_stock(self)
        
        # Refund cancelled (refunded → any other status)
        elif old_status == 'refunded' and self.status != 'refunded':
            # Reverse the refund transactions
            from erp.models import StockTransaction
            reference = f"POS:{self.sale_number}:REFUND"
            StockTransaction.objects.filter(reference=reference).delete()
    
    def calculate_totals(self):
        """Calculate totals from items including tax and shipping"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        
        # Calculate tax amount from percentage
        if self.tax_percentage > 0:
            self.tax_amount = (self.subtotal * self.tax_percentage) / Decimal('100')
        else:
            self.tax_amount = Decimal('0.00')
        
        # Auto-fill shipping charge from shipping area if selected
        if self.shipping_area and not self.shipping_charge:
            self.shipping_charge = self.shipping_area.shipping_charge
        
        # Total = Subtotal - Discount + Tax + Shipping
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount + self.shipping_charge
        
        # Calculate due amount
        self.due_amount = self.total_amount - self.amount_received
        if self.due_amount < 0:
            self.due_amount = Decimal('0.00')
        
        self.save(update_fields=['subtotal', 'tax_amount', 'shipping_charge', 'total_amount', 'due_amount'])
    
    def complete_sale(self):
        """Complete the sale and update stock"""
        try:
            if self.status == 'completed':
                return False, "Sale is already completed"
            
            if not self.items.exists():
                return False, "Cannot complete sale without items"
            
            # Deduct stock for each item
            for item in self.items.all():
                product = item.product
                
                # Check if variant is used
                if item.variant:
                    # Deduct variant stock
                    item.variant.update_warehouse_stock(
                        self.branch,
                        -item.quantity
                    )
                # Check if product has a default BOM
                elif product.default_bom:
                    # Deduct BOM components instead
                    for component in product.default_bom.components.all():
                        component_product = component.product
                        quantity_to_deduct = item.quantity * component.quantity
                        component_product.update_warehouse_stock(
                            self.branch,
                            -quantity_to_deduct
                        )
                else:
                    # Deduct the product itself
                    product.update_warehouse_stock(
                        self.branch,
                        -item.quantity
                    )
            
            # Mark as completed
            self.status = 'completed'
            self.save(update_fields=['status'])
            
            return True, f"Sale {self.sale_number} completed successfully"
        
        except Exception as e:
            return False, f"Error completing sale: {str(e)}"
    
    @property
    def balance_due(self):
        """বাকি কত টাকা"""
        return self.due_amount


class QuickSaleItem(TimeStampedModel):
    """Quick Sale Item - Line items for quick sale"""
    quick_sale = models.ForeignKey(QuickSale, on_delete=models.CASCADE, related_name='items', verbose_name=_("Quick Sale"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    # Variant — Size/Color (optional)
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Variant (Size/Color)"),
        help_text=_("Select variant if product has size/color options")
    )
    
    quantity = models.DecimalField(_("Qty"), max_digits=10, decimal_places=2, default=Decimal('1.00'), validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    
    # Item-level discount (optional)
    discount_amount = models.DecimalField(
        _("Discount"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Item-specific discount")
    )
    
    line_total = models.DecimalField(_("Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = _("Quick Sale Item")
        verbose_name_plural = _("Quick Sale Items")
    
    def __str__(self):
        variant_str = f" [{self.variant}]" if self.variant else ""
        return f"{self.product.name}{variant_str} × {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Auto-set price: variant price > product price
        if not self.unit_price:
            if self.variant and self.variant.effective_selling_price:
                self.unit_price = self.variant.effective_selling_price
            else:
                self.unit_price = self.product.selling_price
        
        # Calculate line total: (qty × price) - discount
        self.line_total = (self.quantity * self.unit_price) - self.discount_amount
        if self.line_total < 0:
            self.line_total = Decimal('0.00')
        
        super().save(*args, **kwargs)
        
        # Update sale totals
        self.quick_sale.calculate_totals()
    
    def delete(self, *args, **kwargs):
        sale = self.quick_sale
        super().delete(*args, **kwargs)
        # Item delete হলেও total update হবে
        sale.calculate_totals()



# ==================== QUALITY CONTROL & SERVICE MANAGEMENT ====================

class QualityCheckType(TimeStampedModel):
    """Quality Check Type Master"""
    name = models.CharField(_("Check Type"), max_length=100, unique=True, db_index=True)
    code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Quality Check Type")
        verbose_name_plural = _("Quality Check Types")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class QualityCheck(TimeStampedModel):
    """Quality Check/Inspection Record"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('in_progress', _('In Progress')),
        ('passed', _('Passed')),
        ('failed', _('Failed')),
        ('on_hold', _('On Hold')),
    ]
    
    check_number = models.CharField(_("Check#"), max_length=50, unique=True, editable=False, db_index=True)
    check_date = models.DateField(_("Check Date"), default=timezone.now, db_index=True)
    check_type = models.ForeignKey(QualityCheckType, on_delete=models.PROTECT, db_index=True)
    
    # Reference
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    production_receipt = models.ForeignKey(ProductionReceipt, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    
    # Check Details
    inspector = models.CharField(_("Inspector"), max_length=100, db_index=True)
    sample_size = models.IntegerField(_("Sample Size"), default=0)
    passed_quantity = models.IntegerField(_("Passed Qty"), default=0)
    failed_quantity = models.IntegerField(_("Failed Qty"), default=0)
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    result = models.TextField(_("Result/Findings"), blank=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='quality_checks', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this qualitycheck"))

    class Meta:
        verbose_name = _("Quality Check")
        verbose_name_plural = _("Quality Checks")
        ordering = ['-check_date']
        indexes = [
            models.Index(fields=['check_type', 'status']),
            models.Index(fields=['inspector', 'check_date']),
        ]
    
    def __str__(self):
        return f"{self.check_number} - {self.check_type.name}"
    
    def save(self, *args, **kwargs):
        if not self.check_number:
            last_check = QualityCheck.objects.order_by('-id').first()
            if last_check:
                last_num = int(last_check.check_number.split('-')[-1])
                self.check_number = f"QC-{last_num + 1:06d}"
            else:
                self.check_number = "QC-000001"
        super().save(*args, **kwargs)


class DefectType(TimeStampedModel):
    """Defect Type Master"""
    SEVERITY_CHOICES = [
        ('minor', _('Minor')),
        ('major', _('Major')),
        ('critical', _('Critical')),
    ]
    
    name = models.CharField(_("Defect Name"), max_length=100, unique=True, db_index=True)
    code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    severity = models.CharField(_("Severity"), max_length=20, choices=SEVERITY_CHOICES, default='minor', db_index=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Defect Type")
        verbose_name_plural = _("Defect Types")
        ordering = ['severity', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"


class QualityDefect(TimeStampedModel):
    """Quality Defects Found"""
    quality_check = models.ForeignKey(QualityCheck, on_delete=models.CASCADE, related_name='defects', db_index=True)
    defect_type = models.ForeignKey(DefectType, on_delete=models.PROTECT, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True, db_index=True)
    quantity = models.IntegerField(_("Defect Qty"), default=1)
    location = models.CharField(_("Location"), max_length=200, blank=True)
    description = models.TextField(_("Description"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='quality_defects', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this qualitydefect"))

    class Meta:
        verbose_name = _("Quality Defect")
        verbose_name_plural = _("Quality Defects")
        ordering = ['quality_check', 'defect_type']
    
    def __str__(self):
        return f"{self.quality_check.check_number} - {self.defect_type.name}"


class ServiceType(TimeStampedModel):
    """Service Type Master"""
    name = models.CharField(_("Service Type"), max_length=100, unique=True, db_index=True)
    code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Service Type")
        verbose_name_plural = _("Service Types")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ServiceRequest(TimeStampedModel):
    """Customer Service Request/Ticket"""
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]
    
    STATUS_CHOICES = [
        ('open', _('Open')),
        ('assigned', _('Assigned')),
        ('in_progress', _('In Progress')),
        ('resolved', _('Resolved')),
        ('closed', _('Closed')),
        ('cancelled', _('Cancelled')),
    ]
    
    ticket_number = models.CharField(_("Ticket#"), max_length=50, unique=True, editable=False, db_index=True)
    request_date = models.DateTimeField(_("Request Date"), default=timezone.now, db_index=True)
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT, db_index=True)
    
    # Customer Info
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, db_index=True)
    contact_person = models.CharField(_("Contact Person"), max_length=100)
    contact_phone = models.CharField(_("Phone"), max_length=20)
    contact_email = models.EmailField(_("Email"), blank=True)
    
    # Request Details
    subject = models.CharField(_("Subject"), max_length=200, db_index=True)
    description = models.TextField(_("Description"))
    priority = models.CharField(_("Priority"), max_length=20, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='open', db_index=True)
    
    # Assignment
    assigned_to = models.CharField(_("Assigned To"), max_length=100, blank=True, db_index=True)
    assigned_date = models.DateTimeField(_("Assigned Date"), null=True, blank=True, db_index=True)
    
    # Resolution
    resolution = models.TextField(_("Resolution"), blank=True)
    resolved_date = models.DateTimeField(_("Resolved Date"), null=True, blank=True, db_index=True)
    closed_date = models.DateTimeField(_("Closed Date"), null=True, blank=True, db_index=True)
    
    # Reference
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='service_requests', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this servicerequest"))

    class Meta:
        verbose_name = _("Service Request")
        verbose_name_plural = _("Service Requests")
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['priority', 'status']),
        ]
    
    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            last_ticket = ServiceRequest.objects.order_by('-id').first()
            if last_ticket:
                last_num = int(last_ticket.ticket_number.split('-')[-1])
                self.ticket_number = f"SR-{last_num + 1:06d}"
            else:
                self.ticket_number = "SR-000001"
        super().save(*args, **kwargs)


class ComplaintType(TimeStampedModel):
    """Complaint Type Master"""
    name = models.CharField(_("Complaint Type"), max_length=100, unique=True, db_index=True)
    code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Complaint Type")
        verbose_name_plural = _("Complaint Types")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Complaint(TimeStampedModel):
    """Customer Complaint"""
    SEVERITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]
    
    STATUS_CHOICES = [
        ('open', _('Open')),
        ('investigating', _('Investigating')),
        ('resolved', _('Resolved')),
        ('closed', _('Closed')),
        ('rejected', _('Rejected')),
    ]
    
    complaint_number = models.CharField(_("Complaint#"), max_length=50, unique=True, editable=False, db_index=True)
    complaint_date = models.DateTimeField(_("Complaint Date"), default=timezone.now, db_index=True)
    complaint_type = models.ForeignKey(ComplaintType, on_delete=models.PROTECT, db_index=True)
    
    # Customer Info
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, db_index=True)
    contact_person = models.CharField(_("Contact Person"), max_length=100)
    contact_phone = models.CharField(_("Phone"), max_length=20)
    
    # Complaint Details
    subject = models.CharField(_("Subject"), max_length=200, db_index=True)
    description = models.TextField(_("Description"))
    severity = models.CharField(_("Severity"), max_length=20, choices=SEVERITY_CHOICES, default='medium', db_index=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='open', db_index=True)
    
    # Reference
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    
    # Investigation
    investigated_by = models.CharField(_("Investigated By"), max_length=100, blank=True, db_index=True)
    investigation_notes = models.TextField(_("Investigation Notes"), blank=True)
    root_cause = models.TextField(_("Root Cause"), blank=True)
    
    # Resolution
    corrective_action = models.TextField(_("Corrective Action"), blank=True)
    preventive_action = models.TextField(_("Preventive Action"), blank=True)
    resolution_date = models.DateTimeField(_("Resolved Date"), null=True, blank=True, db_index=True)
    closed_date = models.DateTimeField(_("Closed Date"), null=True, blank=True, db_index=True)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='complaints', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this complaint"))

    class Meta:
        verbose_name = _("Complaint")
        verbose_name_plural = _("Complaints")
        ordering = ['-complaint_date']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['complaint_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.complaint_number} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.complaint_number:
            last_complaint = Complaint.objects.order_by('-id').first()
            if last_complaint:
                last_num = int(last_complaint.complaint_number.split('-')[-1])
                self.complaint_number = f"CMP-{last_num + 1:06d}"
            else:
                self.complaint_number = "CMP-000001"
        super().save(*args, **kwargs)


# ==================== FIXED ASSETS MANAGEMENT ====================

class AssetCategory(TimeStampedModel):
    """Asset Category Master"""
    DEPRECIATION_METHOD_CHOICES = [
        ('straight_line', _('Straight Line')),
        ('reducing_balance', _('Reducing Balance')),
        ('double_declining', _('Double Declining Balance')),
        ('sum_of_years', _('Sum of Years Digits')),
    ]
    
    name = models.CharField(_("Category Name"), max_length=100, unique=True, db_index=True)
    code = models.CharField(_("Category Code"), max_length=20, unique=True, db_index=True)
    parent_category = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_categories', verbose_name=_("Parent Category"))
    
    # Accounting Integration
    asset_account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, related_name='asset_categories', verbose_name=_("Asset Account"))
    depreciation_account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, related_name='depreciation_categories', verbose_name=_("Depreciation Account"))
    accumulated_depreciation_account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, related_name='accumulated_depreciation_categories', verbose_name=_("Accumulated Depreciation Account"))
    
    # Default Depreciation Settings
    default_depreciation_method = models.CharField(_("Depreciation Method"), max_length=30, choices=DEPRECIATION_METHOD_CHOICES, default='straight_line')
    default_useful_life_years = models.IntegerField(_("Useful Life (Years)"), default=5, validators=[MinValueValidator(1)])
    default_salvage_value_percentage = models.DecimalField(_("Salvage Value (%)"), max_digits=5, decimal_places=2, default=Decimal('10.00'), validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))])
    
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = _("Asset Category")
        verbose_name_plural = _("Asset Categories")
        ordering = ['code', 'name']
        indexes = [
            models.Index(fields=['parent_category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class FixedAsset(TimeStampedModel):
    """Fixed Asset Register"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('under_maintenance', _('Under Maintenance')),
        ('disposed', _('Disposed')),
        ('sold', _('Sold')),
        ('scrapped', _('Scrapped')),
    ]
    
    asset_number = models.CharField(_("Asset Number"), max_length=50, unique=True, editable=False, db_index=True)
    asset_name = models.CharField(_("Asset Name"), max_length=200, db_index=True)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name='assets', db_index=True)
    
    # Purchase Details
    purchase_date = models.DateField(_("Purchase Date"), default=timezone.now, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    purchase_invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='fixed_assets')
    purchase_cost = models.DecimalField(_("Purchase Cost"), max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Depreciation Settings
    depreciation_method = models.CharField(_("Depreciation Method"), max_length=30, choices=AssetCategory.DEPRECIATION_METHOD_CHOICES)
    useful_life_years = models.IntegerField(_("Useful Life (Years)"), validators=[MinValueValidator(1)])
    salvage_value = models.DecimalField(_("Salvage Value"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    depreciation_start_date = models.DateField(_("Depreciation Start Date"), db_index=True)
    
    # Current Values
    accumulated_depreciation = models.DecimalField(_("Accumulated Depreciation"), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    book_value = models.DecimalField(_("Book Value"), max_digits=15, decimal_places=2, editable=False)
    
    # Location & Assignment
    location = models.CharField(_("Location"), max_length=200, blank=True, db_index=True)
    department = models.CharField(_("Department"), max_length=100, blank=True, db_index=True)
    assigned_to = models.CharField(_("Assigned To"), max_length=100, blank=True)
    
    # Status
    status = models.CharField(_("Status"), max_length=30, choices=STATUS_CHOICES, default='draft', db_index=True)
    
    # Additional Info
    serial_number = models.CharField(_("Serial Number"), max_length=100, blank=True, db_index=True)
    model_number = models.CharField(_("Model Number"), max_length=100, blank=True)
    manufacturer = models.CharField(_("Manufacturer"), max_length=100, blank=True)
    warranty_expiry_date = models.DateField(_("Warranty Expiry"), null=True, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='fixed_assets', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this fixedasset"))

    class Meta:
        verbose_name = _("Fixed Asset")
        verbose_name_plural = _("Fixed Assets")
        ordering = ['-purchase_date', 'asset_number']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['location', 'status']),
            models.Index(fields=['purchase_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.asset_number} - {self.asset_name}"
    
    def save(self, *args, **kwargs):
        if not self.asset_number:
            last_asset = FixedAsset.objects.order_by('-id').first()
            if last_asset:
                last_num = int(last_asset.asset_number.split('-')[-1])
                self.asset_number = f"FA-{last_num + 1:06d}"
            else:
                self.asset_number = "FA-000001"
        
        # Calculate book value
        self.book_value = self.purchase_cost - self.accumulated_depreciation
        
        super().save(*args, **kwargs)
    
    @property
    def depreciable_amount(self):
        """Amount to be depreciated"""
        return self.purchase_cost - self.salvage_value
    
    @property
    def annual_depreciation(self):
        """Annual depreciation amount"""
        if self.depreciation_method == 'straight_line':
            return self.depreciable_amount / self.useful_life_years
        return Decimal('0.00')


class AssetDepreciation(TimeStampedModel):
    """Asset Depreciation Schedule & Posting"""
    asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name='depreciations', db_index=True)
    depreciation_date = models.DateField(_("Depreciation Date"), db_index=True)
    period_start = models.DateField(_("Period Start"))
    period_end = models.DateField(_("Period End"))
    
    depreciation_amount = models.DecimalField(_("Depreciation Amount"), max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    accumulated_depreciation = models.DecimalField(_("Accumulated Depreciation"), max_digits=15, decimal_places=2)
    book_value = models.DecimalField(_("Book Value"), max_digits=15, decimal_places=2)
    
    # Accounting Integration
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True, related_name='asset_depreciations')
    is_posted = models.BooleanField(_("Posted"), default=False, db_index=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='asset_depreciations', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this assetdepreciation"))

    class Meta:
        verbose_name = _("Asset Depreciation")
        verbose_name_plural = _("Asset Depreciations")
        ordering = ['-depreciation_date', 'asset']
        unique_together = ['asset', 'period_start', 'period_end']
        indexes = [
            models.Index(fields=['asset', 'is_posted']),
            models.Index(fields=['depreciation_date', 'is_posted']),
        ]
    
    def __str__(self):
        return f"{self.asset.asset_number} - {self.depreciation_date}"


class AssetTransfer(TimeStampedModel):
    """Asset Transfer between Locations/Departments"""
    transfer_number = models.CharField(_("Transfer Number"), max_length=50, unique=True, editable=False, db_index=True)
    transfer_date = models.DateField(_("Transfer Date"), default=timezone.now, db_index=True)
    asset = models.ForeignKey(FixedAsset, on_delete=models.PROTECT, related_name='transfers', db_index=True)
    
    # From
    from_location = models.CharField(_("From Location"), max_length=200)
    from_department = models.CharField(_("From Department"), max_length=100, blank=True)
    from_assigned_to = models.CharField(_("From Assigned To"), max_length=100, blank=True)
    
    # To
    to_location = models.CharField(_("To Location"), max_length=200)
    to_department = models.CharField(_("To Department"), max_length=100, blank=True)
    to_assigned_to = models.CharField(_("To Assigned To"), max_length=100, blank=True)
    
    transfer_reason = models.TextField(_("Transfer Reason"))
    approved_by = models.CharField(_("Approved By"), max_length=100, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='asset_transfers', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this assettransfer"))

    class Meta:
        verbose_name = _("Asset Transfer")
        verbose_name_plural = _("Asset Transfers")
        ordering = ['-transfer_date']
        indexes = [
            models.Index(fields=['asset', 'transfer_date']),
        ]
    
    def __str__(self):
        return f"{self.transfer_number} - {self.asset.asset_name}"
    
    def save(self, *args, **kwargs):
        if not self.transfer_number:
            last_transfer = AssetTransfer.objects.order_by('-id').first()
            if last_transfer:
                last_num = int(last_transfer.transfer_number.split('-')[-1])
                self.transfer_number = f"AT-{last_num + 1:06d}"
            else:
                self.transfer_number = "AT-000001"
        super().save(*args, **kwargs)


class AssetDisposal(TimeStampedModel):
    """Asset Disposal/Sale/Scrap"""
    DISPOSAL_TYPE_CHOICES = [
        ('sale', _('Sale')),
        ('scrap', _('Scrap')),
        ('donation', _('Donation')),
        ('trade_in', _('Trade-In')),
    ]
    
    disposal_number = models.CharField(_("Disposal Number"), max_length=50, unique=True, editable=False, db_index=True)
    disposal_date = models.DateField(_("Disposal Date"), default=timezone.now, db_index=True)
    asset = models.ForeignKey(FixedAsset, on_delete=models.PROTECT, related_name='disposals', db_index=True)
    
    disposal_type = models.CharField(_("Disposal Type"), max_length=20, choices=DISPOSAL_TYPE_CHOICES, db_index=True)
    disposal_value = models.DecimalField(_("Disposal Value"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    book_value_at_disposal = models.DecimalField(_("Book Value at Disposal"), max_digits=15, decimal_places=2)
    gain_loss = models.DecimalField(_("Gain/Loss"), max_digits=15, decimal_places=2, editable=False)
    
    # Buyer/Recipient Info (for sale/donation)
    buyer_name = models.CharField(_("Buyer/Recipient Name"), max_length=200, blank=True)
    buyer_contact = models.CharField(_("Contact"), max_length=100, blank=True)
    
    # Accounting Integration
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True, related_name='asset_disposals')
    is_posted = models.BooleanField(_("Posted"), default=False, db_index=True)
    
    disposal_reason = models.TextField(_("Disposal Reason"))
    approved_by = models.CharField(_("Approved By"), max_length=100, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='asset_disposals', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this assetdisposal"))

    class Meta:
        verbose_name = _("Asset Disposal")
        verbose_name_plural = _("Asset Disposals")
        ordering = ['-disposal_date']
        indexes = [
            models.Index(fields=['asset', 'disposal_date']),
            models.Index(fields=['disposal_type', 'is_posted']),
        ]
    
    def __str__(self):
        return f"{self.disposal_number} - {self.asset.asset_name}"
    
    def save(self, *args, **kwargs):
        if not self.disposal_number:
            last_disposal = AssetDisposal.objects.order_by('-id').first()
            if last_disposal:
                last_num = int(last_disposal.disposal_number.split('-')[-1])
                self.disposal_number = f"AD-{last_num + 1:06d}"
            else:
                self.disposal_number = "AD-000001"
        
        # Calculate gain/loss
        self.gain_loss = self.disposal_value - self.book_value_at_disposal
        
        super().save(*args, **kwargs)


class AssetMaintenance(TimeStampedModel):
    """Asset Maintenance Log"""
    MAINTENANCE_TYPE_CHOICES = [
        ('preventive', _('Preventive')),
        ('corrective', _('Corrective')),
        ('breakdown', _('Breakdown')),
        ('inspection', _('Inspection')),
    ]
    
    maintenance_number = models.CharField(_("Maintenance Number"), max_length=50, unique=True, editable=False, db_index=True)
    maintenance_date = models.DateField(_("Maintenance Date"), default=timezone.now, db_index=True)
    asset = models.ForeignKey(FixedAsset, on_delete=models.PROTECT, related_name='maintenances', db_index=True)
    
    maintenance_type = models.CharField(_("Maintenance Type"), max_length=20, choices=MAINTENANCE_TYPE_CHOICES, db_index=True)
    description = models.TextField(_("Description"))
    
    # Service Provider
    service_provider = models.CharField(_("Service Provider"), max_length=200, blank=True)
    technician_name = models.CharField(_("Technician Name"), max_length=100, blank=True)
    
    # Cost
    labor_cost = models.DecimalField(_("Labor Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    parts_cost = models.DecimalField(_("Parts Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    other_cost = models.DecimalField(_("Other Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(_("Total Cost"), max_digits=10, decimal_places=2, editable=False)
    
    # Downtime
    downtime_hours = models.DecimalField(_("Downtime (Hours)"), max_digits=6, decimal_places=2, default=Decimal('0.00'))
    
    next_maintenance_date = models.DateField(_("Next Maintenance Date"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='asset_maintenances', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this assetmaintenance"))

    class Meta:
        verbose_name = _("Asset Maintenance")
        verbose_name_plural = _("Asset Maintenances")
        ordering = ['-maintenance_date']
        indexes = [
            models.Index(fields=['asset', 'maintenance_date']),
            models.Index(fields=['maintenance_type', 'maintenance_date']),
        ]
    
    def __str__(self):
        return f"{self.maintenance_number} - {self.asset.asset_name}"
    
    def save(self, *args, **kwargs):
        if not self.maintenance_number:
            last_maintenance = AssetMaintenance.objects.order_by('-id').first()
            if last_maintenance:
                last_num = int(last_maintenance.maintenance_number.split('-')[-1])
                self.maintenance_number = f"AM-{last_num + 1:06d}"
            else:
                self.maintenance_number = "AM-000001"
        
        # Calculate total cost
        self.total_cost = self.labor_cost + self.parts_cost + self.other_cost
        
        super().save(*args, **kwargs)


# ==================== BANK RECONCILIATION ====================

class BankStatement(TimeStampedModel):
    """Bank Statement Import"""
    statement_number = models.CharField(_("Statement Number"), max_length=50, unique=True, editable=False, db_index=True)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name='statements', db_index=True)
    statement_date = models.DateField(_("Statement Date"), db_index=True)
    period_start = models.DateField(_("Period Start"))
    period_end = models.DateField(_("Period End"))
    
    opening_balance = models.DecimalField(_("Opening Balance"), max_digits=15, decimal_places=2)
    closing_balance = models.DecimalField(_("Closing Balance"), max_digits=15, decimal_places=2)
    
    # Import Info
    import_date = models.DateTimeField(_("Import Date"), auto_now_add=True)
    imported_by = models.CharField(_("Imported By"), max_length=100, blank=True)
    file_name = models.CharField(_("File Name"), max_length=255, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='bank_statements', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this bankstatement"))

    class Meta:
        verbose_name = _("Bank Statement")
        verbose_name_plural = _("Bank Statements")
        ordering = ['-statement_date', 'bank_account']
        unique_together = ['bank_account', 'period_start', 'period_end']
        indexes = [
            models.Index(fields=['bank_account', 'statement_date']),
        ]
    
    def __str__(self):
        return f"{self.statement_number} - {self.bank_account.account_name} ({self.statement_date})"
    
    def save(self, *args, **kwargs):
        if not self.statement_number:
            last_statement = BankStatement.objects.order_by('-id').first()
            if last_statement:
                last_num = int(last_statement.statement_number.split('-')[-1])
                self.statement_number = f"BS-{last_num + 1:06d}"
            else:
                self.statement_number = "BS-000001"
        super().save(*args, **kwargs)


class BankReconciliation(TimeStampedModel):
    """Bank Reconciliation"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('completed', _('Completed')),
        ('approved', _('Approved')),
    ]
    
    reconciliation_number = models.CharField(_("Reconciliation Number"), max_length=50, unique=True, editable=False, db_index=True)
    bank_statement = models.ForeignKey(BankStatement, on_delete=models.PROTECT, related_name='reconciliations', db_index=True)
    reconciliation_date = models.DateField(_("Reconciliation Date"), default=timezone.now, db_index=True)
    
    # Balances
    bank_statement_balance = models.DecimalField(_("Bank Statement Balance"), max_digits=15, decimal_places=2)
    book_balance = models.DecimalField(_("Book Balance"), max_digits=15, decimal_places=2)
    difference = models.DecimalField(_("Difference"), max_digits=15, decimal_places=2, editable=False)
    
    # Reconciliation Items
    outstanding_deposits = models.DecimalField(_("Outstanding Deposits"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    outstanding_cheques = models.DecimalField(_("Outstanding Cheques"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    bank_charges = models.DecimalField(_("Bank Charges"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    bank_interest = models.DecimalField(_("Bank Interest"), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    reconciled_by = models.CharField(_("Reconciled By"), max_length=100, blank=True)
    approved_by = models.CharField(_("Approved By"), max_length=100, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, 
                              related_name='bank_reconciliations', verbose_name=_("Branch"), 
                              help_text=_("Branch/Warehouse for this bankreconciliation"))

    class Meta:
        verbose_name = _("Bank Reconciliation")
        verbose_name_plural = _("Bank Reconciliations")
        ordering = ['-reconciliation_date']
        indexes = [
            models.Index(fields=['bank_statement', 'status']),
        ]
    
    def __str__(self):
        return f"{self.reconciliation_number} - {self.bank_statement.bank_account.account_name}"
    
    def save(self, *args, **kwargs):
        if not self.reconciliation_number:
            last_recon = BankReconciliation.objects.order_by('-id').first()
            if last_recon:
                last_num = int(last_recon.reconciliation_number.split('-')[-1])
                self.reconciliation_number = f"BR-{last_num + 1:06d}"
            else:
                self.reconciliation_number = "BR-000001"
        
        # Calculate difference
        adjusted_book_balance = self.book_balance + self.outstanding_deposits - self.outstanding_cheques + self.bank_interest - self.bank_charges
        self.difference = self.bank_statement_balance - adjusted_book_balance
        
        super().save(*args, **kwargs)


class UnreconciledTransaction(TimeStampedModel):
    """Unreconciled Transactions"""
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', _('Deposit')),
        ('cheque', _('Cheque')),
        ('bank_charge', _('Bank Charge')),
        ('bank_interest', _('Bank Interest')),
        ('other', _('Other')),
    ]
    
    bank_reconciliation = models.ForeignKey(BankReconciliation, on_delete=models.CASCADE, related_name='unreconciled_items', db_index=True)
    transaction_date = models.DateField(_("Transaction Date"), db_index=True)
    transaction_type = models.CharField(_("Transaction Type"), max_length=20, choices=TRANSACTION_TYPE_CHOICES, db_index=True)
    
    reference_number = models.CharField(_("Reference Number"), max_length=100, blank=True)
    description = models.CharField(_("Description"), max_length=200)
    amount = models.DecimalField(_("Amount"), max_digits=15, decimal_places=2)
    
    # Link to system transactions
    incoming_payment = models.ForeignKey(IncomingPayment, on_delete=models.SET_NULL, null=True, blank=True)
    outgoing_payment = models.ForeignKey(OutgoingPayment, on_delete=models.SET_NULL, null=True, blank=True)
    
    is_reconciled = models.BooleanField(_("Reconciled"), default=False, db_index=True)
    reconciled_date = models.DateField(_("Reconciled Date"), null=True, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Unreconciled Transaction")
        verbose_name_plural = _("Unreconciled Transactions")
        ordering = ['transaction_date', 'transaction_type']
        indexes = [
            models.Index(fields=['bank_reconciliation', 'is_reconciled']),
            models.Index(fields=['transaction_type', 'is_reconciled']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.transaction_date})"
# ==================== SIMPLE EXPENSE SYSTEM ====================

class ExpenseCategory(TimeStampedModel):
    """Expense Categories for Simple Expense Entry"""
    name = models.CharField(_("Category Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    default_account = models.ForeignKey(
        ChartOfAccounts,
        on_delete=models.PROTECT,
        related_name='expense_categories',
        verbose_name=_("Default Account"),
        help_text=_("Default expense account for this category")
    )
    is_active = models.BooleanField(_("Active"), default=True)

    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True,
                              related_name='expense_categories', verbose_name=_("Branch"),
                              help_text=_("Branch/Warehouse for this expense category"))

    class Meta:
        verbose_name = _("Expense Category")
        verbose_name_plural = _("Expense Categories")
        ordering = ['name']
        unique_together = ['name', 'branch']

    def __str__(self):
        return self.name


class SimpleExpense(TimeStampedModel):
    """Simple Expense Entry for Regular Users"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('posted', _('Posted')),
        ('cancelled', _('Cancelled')),
    ]

    expense_number = models.CharField(_("Expense Number"), max_length=50, unique=True, editable=False)
    expense_date = models.DateField(_("Expense Date"), default=timezone.now)

    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name='expenses',
        verbose_name=_("Expense Category")
    )

    amount = models.DecimalField(_("Amount"), max_digits=15, decimal_places=2)
    description = models.CharField(_("Description"), max_length=200)
    notes = models.TextField(_("Notes"), blank=True)

    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')

    # Auto-created journal entry
    journal_entry = models.OneToOneField(
        JournalEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='simple_expense',
        verbose_name=_("Journal Entry"),
        editable=False
    )

    # User who created the expense
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='created_expenses',
        verbose_name=_("Created By"),
        editable=False
    )

    # Branch/Warehouse
    branch = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True,
                              related_name='simple_expenses', verbose_name=_("Branch"),
                              help_text=_("Branch/Warehouse for this expense"))

    class Meta:
        verbose_name = _("Simple Expense")
        verbose_name_plural = _("Simple Expenses")
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.expense_number} - {self.category.name} - {self.amount}"

    def save(self, *args, **kwargs):
        # Generate expense number
        if not self.expense_number:
            last_expense = SimpleExpense.objects.order_by('-id').first()
            if last_expense:
                last_num = int(last_expense.expense_number.split('-')[-1])
                self.expense_number = f"EXP-{last_num + 1:06d}"
            else:
                self.expense_number = "EXP-000001"

        super().save(*args, **kwargs)

        # Auto-create journal entry when posted
        if self.status == 'posted' and not self.journal_entry:
            self.create_journal_entry()

    def create_journal_entry(self):
        """Create journal entry for the expense"""
        from decimal import Decimal

        # Get default cash account (assuming account code 1001 for cash)
        try:
            cash_account = ChartOfAccounts.objects.filter(
                account_code__in=['1001', '1000', 'CASH']
            ).first()

            if not cash_account:
                # Create a default cash account if it doesn't exist
                cash_account_type = AccountType.objects.filter(name__icontains='asset').first()
                if cash_account_type:
                    cash_account = ChartOfAccounts.objects.create(
                        account_code='1001',
                        account_name='Cash',
                        account_type=cash_account_type,
                        is_active=True
                    )
        except:
            return  # Skip journal entry creation if no cash account

        if not cash_account:
            return

        # Create journal entry
        journal_entry = JournalEntry.objects.create(
            entry_date=self.expense_date,
            reference=f"Simple Expense: {self.expense_number}",
            status='posted',
            notes=f"Auto-generated from Simple Expense: {self.description}",
            branch=self.branch
        )

        # Create journal entry lines
        # Debit: Expense Account
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=self.category.default_account,
            description=self.description,
            debit=self.amount,
            credit=Decimal('0.00')
        )

        # Credit: Cash Account
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=cash_account,
            description=f"Cash payment for {self.description}",
            debit=Decimal('0.00'),
            credit=self.amount
        )

        # Update totals and link
        journal_entry.calculate_totals()
        self.journal_entry = journal_entry
        self.save(update_fields=['journal_entry'])

    def cancel_expense(self):
        """Cancel the expense and reverse journal entry"""
        if self.status == 'posted' and self.journal_entry:
            self.journal_entry.status = 'cancelled'
            self.journal_entry.save()

        self.status = 'cancelled'
        self.save(update_fields=['status'])



# ============================================================
# ADVANCED POS MODELS - Session, Payment, Return Management
# ============================================================

class POSSession(TimeStampedModel):
    """POS Session - Cashier session management with opening/closing cash
    
    একজন Cashier যখন কাজ শুরু করে, সে একটা Session খোলে।
    Session-এ opening cash দেয় (drawer-এ কত টাকা আছে)।
    সারাদিন সব sale এই session-এর সাথে linked থাকে।
    দিন শেষে session close করে closing cash দেয়।
    """
    STATUS_CHOICES = [
        ('open',   _('Open')),
        ('closed', _('Closed')),
    ]
    
    # Auto-generated session number: SES-20250309-001
    session_number = models.CharField(
        _("Session Number"),
        max_length=50,
        unique=True,
        editable=False,
        db_index=True
    )
    
    # কোন cashier এই session খুলেছে
    cashier = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='pos_sessions',
        verbose_name=_("Cashier")
    )
    
    # কোন branch/warehouse-এ এই session
    branch = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='pos_sessions',
        verbose_name=_("Branch")
    )
    
    # Session শুরুতে drawer-এ কত টাকা রাখা হয়েছে
    opening_cash = models.DecimalField(
        _("Opening Cash"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Session শেষে drawer গণনা করে কত পাওয়া গেছে
    closing_cash = models.DecimalField(
        _("Closing Cash"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # System হিসাব করে কত থাকার কথা
    expected_cash = models.DecimalField(
        _("Expected Cash"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )
    
    # closing_cash - expected_cash
    cash_difference = models.DecimalField(
        _("Cash Difference"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )
    
    opened_at = models.DateTimeField(_("Opened At"), auto_now_add=True)
    closed_at = models.DateTimeField(_("Closed At"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=10,
        choices=STATUS_CHOICES,
        default='open',
        db_index=True
    )
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("POS Session")
        verbose_name_plural = _("POS Sessions")
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['cashier', 'status']),
            models.Index(fields=['branch', 'status']),
        ]
    
    def __str__(self):
        return f"{self.session_number} - {self.cashier.username} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-generate session number
        if not self.session_number:
            today = timezone.now().strftime('%Y%m%d')
            last = POSSession.objects.filter(
                session_number__startswith=f"SES-{today}"
            ).order_by('-id').first()
            
            if last:
                last_num = int(last.session_number.split('-')[-1])
                self.session_number = f"SES-{today}-{last_num + 1:03d}"
            else:
                self.session_number = f"SES-{today}-001"
        
        super().save(*args, **kwargs)
    
    def close_session(self, closing_cash):
        """Session বন্ধ করুন"""
        from django.db.models import Sum
        
        # সব cash sale এর মোট (শুধু cash payment method)
        total_cash_sales = self.quick_sales.filter(
            status='completed',
            payment_method__payment_type='cash'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        self.closing_cash = Decimal(str(closing_cash))
        self.expected_cash = self.opening_cash + total_cash_sales
        self.cash_difference = self.closing_cash - self.expected_cash
        self.closed_at = timezone.now()
        self.status = 'closed'
        self.save()
    
    @property
    def total_sales(self):
        """এই session-এর মোট বিক্রয়"""
        from django.db.models import Sum
        return self.quick_sales.filter(
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    @property
    def total_transactions(self):
        """এই session-এর মোট transaction সংখ্যা"""
        return self.quick_sales.filter(status='completed').count()
    @property
    def total_cash_sales(self):
        """এই session-এর মোট cash payment"""
        from django.db.models import Sum
        return self.quick_sales.filter(
            status='completed',
            payment_method__payment_type='cash'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    @property
    def current_expected_cash(self):
        """বর্তমানে কত cash থাকার কথা (for open sessions)"""
        return self.opening_cash + self.total_cash_sales



class POSReturn(TimeStampedModel):
    """POS Return - Return management
    
    Customer পণ্য ফেরত দিলে এখানে record হয়।
    """
    STATUS_CHOICES = [
        ('completed',  _('Completed')),
        ('cancelled',  _('Cancelled')),
    ]
    
    REFUND_METHOD_CHOICES = [
        ('cash',         _('Cash')),
        ('card',         _('Card')),
        ('store_credit', _('Store Credit')),
    ]
    
    # Auto-generated: RET-20250309-001
    return_number = models.CharField(
        _("Return Number"),
        max_length=50,
        unique=True,
        editable=False,
        db_index=True
    )
    
    # কোন original sale থেকে return
    original_sale = models.ForeignKey(
        QuickSale,
        on_delete=models.PROTECT,
        related_name='returns',
        verbose_name=_("Original Sale")
    )
    
    # কোন cashier return process করেছে
    cashier = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='pos_returns',
        verbose_name=_("Cashier")
    )
    
    # কোন branch-এ return হয়েছে
    branch = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='pos_returns',
        verbose_name=_("Branch")
    )
    
    return_datetime = models.DateTimeField(
        _("Return Date & Time"),
        default=timezone.now
    )
    
    reason = models.TextField(_("Return Reason"), blank=True)
    
    # মোট refund amount
    total_refund = models.DecimalField(
        _("Total Refund"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )
    
    refund_method = models.CharField(
        _("Refund Method"),
        max_length=20,
        choices=REFUND_METHOD_CHOICES,
        default='cash'
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        db_index=True
    )
    
    class Meta:
        verbose_name = _("POS Return")
        verbose_name_plural = _("POS Returns")
        ordering = ['-return_datetime']
    
    def __str__(self):
        return f"{self.return_number} ← {self.original_sale.sale_number}"
    
    def save(self, *args, **kwargs):
        if not self.return_number:
            today = timezone.now().strftime('%Y%m%d')
            last = POSReturn.objects.filter(
                return_number__startswith=f"RET-{today}"
            ).order_by('-id').first()
            
            if last:
                last_num = int(last.return_number.split('-')[-1])
                self.return_number = f"RET-{today}-{last_num + 1:03d}"
            else:
                self.return_number = f"RET-{today}-001"
        
        super().save(*args, **kwargs)
    
    def calculate_refund(self):
        """Items থেকে total_refund calculate করুন"""
        self.total_refund = sum(item.refund_amount for item in self.items.all())
        self.save(update_fields=['total_refund'])
    
    def process_return(self):
        """Return complete করুন - stock ফেরত যাবে"""
        for item in self.items.all():
            if item.restock:
                warehouse = self.branch
                if item.variant:
                    item.variant.update_warehouse_stock(warehouse, item.quantity)
                else:
                    item.product.update_warehouse_stock(warehouse, item.quantity)
        
        # Full return হলে original sale refunded mark করুন
        self.original_sale.status = 'refunded'
        self.original_sale.save(update_fields=['status'])


class POSReturnItem(TimeStampedModel):
    """POS Return Item - Return line items"""
    pos_return = models.ForeignKey(
        POSReturn,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("POS Return")
    )
    
    # কোন original item থেকে return
    original_item = models.ForeignKey(
        QuickSaleItem,
        on_delete=models.PROTECT,
        verbose_name=_("Original Sale Item")
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name=_("Product")
    )
    
    # Variant যদি থাকে
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Variant")
    )
    
    # কতটুকু ফেরত দিচ্ছে
    quantity = models.DecimalField(
        _("Return Quantity"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Refund amount
    refund_amount = models.DecimalField(
        _("Refund Amount"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Stock-এ ফেরত নেবে কি না
    restock = models.BooleanField(
        _("Add Back to Stock"),
        default=True,
        help_text=_("False করলে stock-এ ফেরত যাবে না (damaged item)")
    )
    
    class Meta:
        verbose_name = _("POS Return Item")
        verbose_name_plural = _("POS Return Items")
    
    def __str__(self):
        return f"{self.product.name} × {self.quantity} (Return)"
    
    def save(self, *args, **kwargs):
        # Auto-fill product/variant from original_item
        if self.original_item_id and not self.product_id:
            self.product = self.original_item.product
            if hasattr(self.original_item, 'variant'):
                self.variant = self.original_item.variant
        
        # Auto-calculate refund amount
        if not self.refund_amount:
            self.refund_amount = self.quantity * self.original_item.unit_price
        
        super().save(*args, **kwargs)
        self.pos_return.calculate_refund()
