"""
Complete Optimized Bangladesh Garments ERP
With Database Optimization, Indexes, Validation, Caching
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.functional import cached_property
from django.contrib.auth.models import User
from decimal import Decimal


class TimeStampedModel(models.Model):
    """Optimized base model with indexes"""
    created_at = models.DateTimeField(_("Created"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True)
    
    class Meta:
        abstract = True
        get_latest_by = 'created_at'


# ==================== FOUNDATION ====================

class Company(TimeStampedModel):
    """Company with validation"""
    name = models.CharField(_("Company"), max_length=200, db_index=True)
    trade_license = models.CharField(_("License"), max_length=100, blank=True, db_index=True)
    bin_number = models.CharField(_("BIN"), max_length=50, blank=True, unique=True)
    tin_number = models.CharField(_("TIN"), max_length=50, blank=True, unique=True)
    address = models.TextField(_("Address"))
    city = models.CharField(_("City"), max_length=100, default="Dhaka", db_index=True)
    phone = models.CharField(_("Phone"), max_length=20)
    email = models.EmailField(_("Email"))
    factory_type = models.CharField(_("Type"), max_length=50, choices=[
        ('woven', 'Woven'), ('knit', 'Knit'), ('sweater', 'Sweater'), ('composite', 'Composite')
    ], default='knit', db_index=True)
    total_workers = models.IntegerField(_("Workers"), default=0, validators=[MinValueValidator(0)])
    monthly_capacity = models.IntegerField(_("Capacity"), default=0, validators=[MinValueValidator(0)])
    logo = models.ImageField(_("Logo"), upload_to='garments/company/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'city']),
            models.Index(fields=['factory_type', 'city']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if self.monthly_capacity < 0:
            raise ValidationError({'monthly_capacity': 'Cannot be negative'})


class Factory(TimeStampedModel):
    """Factory with capacity validation"""
    factory_name = models.CharField(_("Factory"), max_length=200, db_index=True)
    factory_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='factories', db_index=True)
    address = models.TextField(_("Address"))
    city = models.CharField(_("City"), max_length=100, db_index=True)
    manager = models.CharField(_("Manager"), max_length=100, blank=True, db_index=True)
    number_of_lines = models.IntegerField(_("Lines"), default=0, validators=[MinValueValidator(0)])
    daily_capacity = models.IntegerField(_("Capacity"), default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Factory"
        verbose_name_plural = "Factories"
        ordering = ['factory_name']
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['city', 'is_active']),
        ]
    
    def __str__(self):
        return self.factory_name


class Size(TimeStampedModel):
    """Size with ordering"""
    name = models.CharField(_("Size"), max_length=50, unique=True, db_index=True)
    code = models.CharField(_("Code"), max_length=20, unique=True, db_index=True)
    sort_order = models.IntegerField(_("Order"), default=0, db_index=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Size"
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['sort_order', 'is_active']),
        ]
    
    def __str__(self):
        return self.name


class Color(TimeStampedModel):
    """Color with hex validation"""
    name = models.CharField(_("Color"), max_length=50, unique=True, db_index=True)
    code = models.CharField(_("Code"), max_length=20, unique=True, db_index=True)
    hex_code = models.CharField(_("Hex"), max_length=7, blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Color"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if self.hex_code and not self.hex_code.startswith('#'):
            raise ValidationError({'hex_code': 'Must start with #'})


class Season(TimeStampedModel):
    """Season with date validation"""
    name = models.CharField(_("Season"), max_length=100, db_index=True)
    code = models.CharField(_("Code"), max_length=20, unique=True, db_index=True)
    year = models.IntegerField(_("Year"), db_index=True)
    start_date = models.DateField(_("Start"), db_index=True)
    end_date = models.DateField(_("End"), db_index=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Season"
        ordering = ['-year', 'start_date']
        unique_together = ['name', 'year']
        indexes = [
            models.Index(fields=['year', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} {self.year}"
    
    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError('Start date must be before end date')


class GarmentType(TimeStampedModel):
    name = models.CharField(_("Type"), max_length=100, unique=True, db_index=True)
    code = models.CharField(_("Code"), max_length=20, unique=True, db_index=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Garment Type"
        ordering = ['name']
    
    def __str__(self):
        return self.name


# ==================== BUYER & SUPPLIER ====================

class Buyer(TimeStampedModel):
    """Buyer with optimized queries"""
    buyer_name = models.CharField(_("Buyer"), max_length=200, db_index=True)
    buyer_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    buyer_type = models.CharField(_("Type"), max_length=50, choices=[
        ('direct', 'Direct'), ('agent', 'Agent'), ('retailer', 'Retailer')
    ], default='direct', db_index=True)
    country = models.CharField(_("Country"), max_length=100, db_index=True)
    address = models.TextField(_("Address"), blank=True)
    email = models.EmailField(_("Email"), blank=True, db_index=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    payment_terms = models.IntegerField(_("Terms"), default=30, validators=[MinValueValidator(0)])
    lc_required = models.BooleanField(_("LC"), default=False, db_index=True)
    compliance_required = models.BooleanField(_("Compliance"), default=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Buyer"
        ordering = ['buyer_name']
        indexes = [
            models.Index(fields=['buyer_name', 'is_active']),
            models.Index(fields=['country', 'is_active']),
            models.Index(fields=['buyer_type', 'is_active']),
        ]
    
    def __str__(self):
        return self.buyer_name


class BuyerBrand(TimeStampedModel):
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='brands', db_index=True)
    brand_name = models.CharField(_("Brand"), max_length=200, db_index=True)
    brand_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    logo = models.ImageField(_("Logo"), upload_to='garments/brands/', blank=True, null=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Buyer Brand"
        ordering = ['brand_name']
        indexes = [
            models.Index(fields=['buyer', 'is_active']),
        ]
    
    def __str__(self):
        return self.brand_name


class Merchandiser(TimeStampedModel):
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='merchandisers', db_index=True)
    name = models.CharField(_("Name"), max_length=200, db_index=True)
    email = models.EmailField(_("Email"), db_index=True)
    phone = models.CharField(_("Phone"), max_length=20)
    designation = models.CharField(_("Designation"), max_length=100, blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Merchandiser"
        ordering = ['name']
        indexes = [
            models.Index(fields=['buyer', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.buyer.buyer_name})"


class Supplier(TimeStampedModel):
    supplier_name = models.CharField(_("Supplier"), max_length=200, db_index=True)
    supplier_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    supplier_type = models.CharField(_("Type"), max_length=50, choices=[
        ('fabric', 'Fabric'), ('trim', 'Trim'), ('accessory', 'Accessory'), ('both', 'Both')
    ], db_index=True)
    country = models.CharField(_("Country"), max_length=100, default="Bangladesh", db_index=True)
    address = models.TextField(_("Address"), blank=True)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    payment_terms = models.IntegerField(_("Terms"), default=30, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Supplier"
        ordering = ['supplier_name']
        indexes = [
            models.Index(fields=['supplier_type', 'is_active']),
            models.Index(fields=['country', 'is_active']),
        ]
    
    def __str__(self):
        return self.supplier_name


# ==================== MATERIALS ====================

class FabricType(TimeStampedModel):
    name = models.CharField(_("Type"), max_length=100, unique=True, db_index=True)
    code = models.CharField(_("Code"), max_length=20, unique=True, db_index=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Fabric Type"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Fabric(TimeStampedModel):
    fabric_name = models.CharField(_("Fabric"), max_length=200, db_index=True)
    fabric_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    fabric_type = models.ForeignKey(FabricType, on_delete=models.SET_NULL, null=True, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    composition = models.CharField(_("Composition"), max_length=200, db_index=True)
    gsm = models.DecimalField(_("GSM"), max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.01'))])
    width = models.DecimalField(_("Width"), max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.01'))])
    shrinkage_length = models.DecimalField(_("Shrink L%"), max_digits=5, decimal_places=2, default=Decimal('3.00'), validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))])
    shrinkage_width = models.DecimalField(_("Shrink W%"), max_digits=5, decimal_places=2, default=Decimal('3.00'), validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))])
    wastage = models.DecimalField(_("Wastage%"), max_digits=5, decimal_places=2, default=Decimal('5.00'), validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))])
    price_per_kg = models.DecimalField(_("Price/KG"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Fabric"
        ordering = ['fabric_name']
        indexes = [
            models.Index(fields=['fabric_type', 'is_active']),
            models.Index(fields=['supplier', 'is_active']),
        ]
    
    def __str__(self):
        return self.fabric_name


class TrimType(TimeStampedModel):
    name = models.CharField(_("Type"), max_length=100, unique=True, db_index=True)
    code = models.CharField(_("Code"), max_length=20, unique=True, db_index=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Trim Type"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Trim(TimeStampedModel):
    trim_name = models.CharField(_("Trim"), max_length=200, db_index=True)
    trim_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    trim_type = models.ForeignKey(TrimType, on_delete=models.SET_NULL, null=True, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    unit = models.CharField(_("Unit"), max_length=20, default="PCS")
    unit_price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Trim"
        ordering = ['trim_name']
        indexes = [
            models.Index(fields=['trim_type', 'is_active']),
            models.Index(fields=['supplier', 'is_active']),
        ]
    
    def __str__(self):
        return self.trim_name


# Continue in next part due to size...


# ==================== STYLE (Optimized) ====================

class Style(TimeStampedModel):
    """Style with caching and validation"""
    style_number = models.CharField(_("Style#"), max_length=100, unique=True, db_index=True)
    style_name = models.CharField(_("Name"), max_length=200, db_index=True)
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT, related_name='styles', db_index=True)
    brand = models.ForeignKey(BuyerBrand, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    garment_type = models.ForeignKey(GarmentType, on_delete=models.SET_NULL, null=True, db_index=True)
    description = models.TextField(_("Description"), blank=True)
    technical_sketch = models.ImageField(_("Sketch"), upload_to='garments/styles/', blank=True, null=True)
    size_range = models.ManyToManyField(Size, related_name='styles')
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('development', 'Development'), ('sampling', 'Sampling'), 
        ('approved', 'Approved'), ('production', 'Production'), ('discontinued', 'Discontinued')
    ], default='development', db_index=True)
    development_date = models.DateField(_("Dev Date"), default=timezone.now, db_index=True)
    approval_date = models.DateField(_("Approval"), null=True, blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Style"
        ordering = ['-development_date']
        indexes = [
            models.Index(fields=['buyer', 'status', 'is_active']),
            models.Index(fields=['season', 'is_active']),
            models.Index(fields=['garment_type', 'is_active']),
            models.Index(fields=['-development_date']),
        ]
    
    def __str__(self):
        return f"{self.style_number} - {self.style_name}"
    
    @cached_property
    def total_fabric_cost(self):
        """Cached fabric cost calculation"""
        return sum(sf.fabric.price_per_kg * sf.consumption_per_piece for sf in self.fabrics.select_related('fabric'))
    
    @cached_property
    def total_trim_cost(self):
        """Cached trim cost calculation"""
        return sum(st.trim.unit_price * st.quantity_per_piece for st in self.trims.select_related('trim'))


class StyleImage(TimeStampedModel):
    style = models.ForeignKey(Style, on_delete=models.CASCADE, related_name='images', db_index=True)
    image = models.ImageField(_("Image"), upload_to='garments/styles/images/')
    image_type = models.CharField(_("Type"), max_length=50, choices=[
        ('front', 'Front'), ('back', 'Back'), ('side', 'Side'), ('detail', 'Detail')
    ], default='front', db_index=True)
    is_primary = models.BooleanField(_("Primary"), default=False, db_index=True)
    sort_order = models.IntegerField(_("Order"), default=0, db_index=True)
    
    class Meta:
        verbose_name = "Style Image"
        ordering = ['style', 'sort_order']
        indexes = [
            models.Index(fields=['style', 'is_primary']),
        ]
    
    def __str__(self):
        return f"{self.style.style_number} - {self.image_type}"


class StyleFabric(TimeStampedModel):
    style = models.ForeignKey(Style, on_delete=models.CASCADE, related_name='fabrics', db_index=True)
    fabric = models.ForeignKey(Fabric, on_delete=models.PROTECT, db_index=True)
    consumption_per_piece = models.DecimalField(_("Consumption"), max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal('0.0001'))])
    unit = models.CharField(_("Unit"), max_length=20, choices=[('meter', 'Meter'), ('yard', 'Yard'), ('kg', 'KG')], default='meter')
    placement = models.CharField(_("Placement"), max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Style Fabric"
        ordering = ['style', 'fabric']
        indexes = [
            models.Index(fields=['style', 'fabric']),
        ]
    
    def __str__(self):
        return f"{self.style.style_number} - {self.fabric.fabric_name}"


class StyleTrim(TimeStampedModel):
    style = models.ForeignKey(Style, on_delete=models.CASCADE, related_name='trims', db_index=True)
    trim = models.ForeignKey(Trim, on_delete=models.PROTECT, db_index=True)
    quantity_per_piece = models.DecimalField(_("Qty"), max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal('0.0001'))])
    placement = models.CharField(_("Placement"), max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Style Trim"
        ordering = ['style', 'trim']
        indexes = [
            models.Index(fields=['style', 'trim']),
        ]
    
    def __str__(self):
        return f"{self.style.style_number} - {self.trim.trim_name}"


class StyleCosting(TimeStampedModel):
    """Costing with auto-calculation"""
    style = models.ForeignKey(Style, on_delete=models.CASCADE, related_name='costings', db_index=True)
    version = models.IntegerField(_("Version"), default=1, validators=[MinValueValidator(1)])
    costing_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    fabric_cost = models.DecimalField(_("Fabric"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    trim_cost = models.DecimalField(_("Trim"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    cm_cost = models.DecimalField(_("CM"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    other_cost = models.DecimalField(_("Other"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    total_cost = models.DecimalField(_("Total"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fob_price = models.DecimalField(_("FOB"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    margin_percent = models.DecimalField(_("Margin%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    is_approved = models.BooleanField(_("Approved"), default=False, db_index=True)
    
    class Meta:
        verbose_name = "Style Costing"
        ordering = ['style', '-version']
        unique_together = ['style', 'version']
        indexes = [
            models.Index(fields=['style', 'is_approved']),
            models.Index(fields=['-costing_date']),
        ]
    
    def __str__(self):
        return f"{self.style.style_number} V{self.version}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate totals
        self.total_cost = self.fabric_cost + self.trim_cost + self.cm_cost + self.other_cost
        if self.fob_price > 0:
            self.margin_percent = ((self.fob_price - self.total_cost) / self.fob_price) * 100
        super().save(*args, **kwargs)


# ==================== BUYER ORDER (Optimized) ====================

class BuyerOrder(TimeStampedModel):
    """Order with validation and caching"""
    order_number = models.CharField(_("Order#"), max_length=100, unique=True, db_index=True)
    buyer_po = models.CharField(_("Buyer PO"), max_length=100, db_index=True)
    buyer_po_date = models.DateField(_("PO Date"), db_index=True)
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT, related_name='orders', db_index=True)
    style = models.ForeignKey(Style, on_delete=models.PROTECT, related_name='orders', db_index=True)
    merchandiser = models.ForeignKey(Merchandiser, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    total_quantity = models.IntegerField(_("Qty"), default=0, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    total_value = models.DecimalField(_("Value"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shipment_mode = models.CharField(_("Shipment"), max_length=50, choices=[
        ('sea', 'Sea'), ('air', 'Air'), ('courier', 'Courier')
    ], default='sea', db_index=True)
    ex_factory_date = models.DateField(_("Ex-Factory"), db_index=True)
    shipment_date = models.DateField(_("Shipment"), db_index=True)
    payment_terms = models.CharField(_("Payment"), max_length=200)
    lc_number = models.CharField(_("LC#"), max_length=100, blank=True, db_index=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('pending', 'Pending'), ('confirmed', 'Confirmed'), ('production', 'Production'),
        ('shipped', 'Shipped'), ('completed', 'Completed'), ('cancelled', 'Cancelled')
    ], default='pending', db_index=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Buyer Order"
        ordering = ['-buyer_po_date']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['style', 'status']),
            models.Index(fields=['-buyer_po_date']),
            models.Index(fields=['ex_factory_date', 'status']),
            models.Index(fields=['shipment_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.buyer_po}"
    
    def save(self, *args, **kwargs):
        self.total_value = self.total_quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def clean(self):
        if self.ex_factory_date and self.shipment_date and self.ex_factory_date > self.shipment_date:
            raise ValidationError('Ex-factory date must be before shipment date')


class OrderBreakdown(TimeStampedModel):
    """Breakdown with auto-calculation"""
    order = models.ForeignKey(BuyerOrder, on_delete=models.CASCADE, related_name='breakdowns', db_index=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, db_index=True)
    size = models.ForeignKey(Size, on_delete=models.PROTECT, db_index=True)
    quantity = models.IntegerField(_("Qty"), validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    cutting_qty = models.IntegerField(_("Cut"), default=0, validators=[MinValueValidator(0)])
    sewing_qty = models.IntegerField(_("Sew"), default=0, validators=[MinValueValidator(0)])
    finishing_qty = models.IntegerField(_("Finish"), default=0, validators=[MinValueValidator(0)])
    shipped_qty = models.IntegerField(_("Ship"), default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        verbose_name = "Order Breakdown"
        ordering = ['order', 'color__name', 'size__sort_order']
        unique_together = ['order', 'color', 'size']
        indexes = [
            models.Index(fields=['order', 'color', 'size']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.color.name} {self.size.name}"
    
    @cached_property
    def line_total(self):
        return self.quantity * self.unit_price
    
    @cached_property
    def balance_to_cut(self):
        return max(0, self.quantity - self.cutting_qty)
    
    @cached_property
    def balance_to_ship(self):
        return max(0, self.quantity - self.shipped_qty)


# ==================== PRODUCTION (Optimized) ====================

class SewingLine(TimeStampedModel):
    line_number = models.CharField(_("Line#"), max_length=50, unique=True, db_index=True)
    line_name = models.CharField(_("Name"), max_length=100, db_index=True)
    factory = models.ForeignKey(Factory, on_delete=models.PROTECT, related_name='lines', db_index=True)
    operators = models.IntegerField(_("Operators"), default=0, validators=[MinValueValidator(0)])
    helpers = models.IntegerField(_("Helpers"), default=0, validators=[MinValueValidator(0)])
    machines = models.IntegerField(_("Machines"), default=0, validators=[MinValueValidator(0)])
    daily_capacity = models.IntegerField(_("Capacity"), default=0, validators=[MinValueValidator(0)])
    line_chief = models.CharField(_("Chief"), max_length=100, blank=True, db_index=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Sewing Line"
        ordering = ['line_number']
        indexes = [
            models.Index(fields=['factory', 'is_active']),
        ]
    
    def __str__(self):
        return self.line_number


class CuttingOrder(TimeStampedModel):
    cutting_number = models.CharField(_("Cutting#"), max_length=100, unique=True, db_index=True)
    cutting_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.PROTECT, related_name='cuttings', db_index=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, db_index=True)
    total_quantity = models.IntegerField(_("Qty"), validators=[MinValueValidator(1)])
    fabric_lot = models.CharField(_("Lot"), max_length=100, blank=True, db_index=True)
    number_of_lays = models.IntegerField(_("Lays"), default=1, validators=[MinValueValidator(1)])
    ply_per_lay = models.IntegerField(_("Ply"), default=1, validators=[MinValueValidator(1)])
    marker_length = models.DecimalField(_("Marker"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('planned', 'Planned'), ('in_progress', 'In Progress'), ('completed', 'Completed')
    ], default='planned', db_index=True)
    cutter_name = models.CharField(_("Cutter"), max_length=100, blank=True, db_index=True)
    
    class Meta:
        verbose_name = "Cutting Order"
        ordering = ['-cutting_date']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['-cutting_date']),
        ]
    
    def __str__(self):
        return self.cutting_number


class CuttingSizeBreakdown(TimeStampedModel):
    cutting = models.ForeignKey(CuttingOrder, on_delete=models.CASCADE, related_name='sizes', db_index=True)
    size = models.ForeignKey(Size, on_delete=models.PROTECT, db_index=True)
    quantity = models.IntegerField(_("Qty"), validators=[MinValueValidator(1)])
    
    class Meta:
        verbose_name = "Cutting Size"
        ordering = ['cutting', 'size__sort_order']
        unique_together = ['cutting', 'size']
        indexes = [
            models.Index(fields=['cutting', 'size']),
        ]
    
    def __str__(self):
        return f"{self.cutting.cutting_number} - {self.size.name}"


class Bundle(TimeStampedModel):
    bundle_number = models.CharField(_("Bundle#"), max_length=100, unique=True, db_index=True)
    cutting = models.ForeignKey(CuttingOrder, on_delete=models.PROTECT, related_name='bundles', db_index=True)
    size = models.ForeignKey(Size, on_delete=models.PROTECT, db_index=True)
    quantity = models.IntegerField(_("Qty"), validators=[MinValueValidator(1)])
    barcode = models.CharField(_("Barcode"), max_length=100, unique=True, blank=True, db_index=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('cut', 'Cut'), ('in_sewing', 'Sewing'), ('completed', 'Completed')
    ], default='cut', db_index=True)
    sewing_line = models.ForeignKey(SewingLine, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    cut_date = models.DateField(_("Cut Date"), default=timezone.now, db_index=True)
    
    class Meta:
        verbose_name = "Bundle"
        ordering = ['bundle_number']
        indexes = [
            models.Index(fields=['cutting', 'status']),
            models.Index(fields=['sewing_line', 'status']),
        ]
    
    def __str__(self):
        return self.bundle_number
    
    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = f"BDL-{self.bundle_number}"
        super().save(*args, **kwargs)


# ==================== QUALITY (Optimized) ====================

class DefectType(TimeStampedModel):
    defect_name = models.CharField(_("Defect"), max_length=100, unique=True, db_index=True)
    defect_code = models.CharField(_("Code"), max_length=20, unique=True, db_index=True)
    category = models.CharField(_("Category"), max_length=50, choices=[
        ('fabric', 'Fabric'), ('cutting', 'Cutting'), ('sewing', 'Sewing'), ('finishing', 'Finishing')
    ], db_index=True)
    severity = models.CharField(_("Severity"), max_length=20, choices=[
        ('critical', 'Critical'), ('major', 'Major'), ('minor', 'Minor')
    ], default='minor', db_index=True)
    points = models.IntegerField(_("Points"), default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Defect Type"
        ordering = ['category', 'defect_name']
        indexes = [
            models.Index(fields=['category', 'severity', 'is_active']),
        ]
    
    def __str__(self):
        return self.defect_name


class Inspection(TimeStampedModel):
    inspection_number = models.CharField(_("Inspection#"), max_length=100, unique=True, db_index=True)
    inspection_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.PROTECT, related_name='inspections', db_index=True)
    inspection_type = models.CharField(_("Type"), max_length=50, choices=[
        ('inline', 'Inline'), ('final', 'Final'), ('aql', 'AQL'), ('pre_shipment', 'Pre-Shipment')
    ], db_index=True)
    order_quantity = models.IntegerField(_("Order Qty"), validators=[MinValueValidator(1)])
    inspected_quantity = models.IntegerField(_("Inspected"), validators=[MinValueValidator(1)])
    passed_quantity = models.IntegerField(_("Passed"), default=0, validators=[MinValueValidator(0)])
    failed_quantity = models.IntegerField(_("Failed"), default=0, validators=[MinValueValidator(0)])
    result = models.CharField(_("Result"), max_length=20, choices=[
        ('passed', 'Passed'), ('failed', 'Failed'), ('conditional', 'Conditional')
    ], default='passed', db_index=True)
    inspector_name = models.CharField(_("Inspector"), max_length=100, db_index=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Inspection"
        ordering = ['-inspection_date']
        indexes = [
            models.Index(fields=['order', 'inspection_type']),
            models.Index(fields=['-inspection_date']),
            models.Index(fields=['result', 'inspection_type']),
        ]
    
    def __str__(self):
        return self.inspection_number


class InspectionDefect(TimeStampedModel):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='defects', db_index=True)
    defect_type = models.ForeignKey(DefectType, on_delete=models.PROTECT, db_index=True)
    quantity = models.IntegerField(_("Qty"), default=1, validators=[MinValueValidator(1)])
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    location = models.CharField(_("Location"), max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Inspection Defect"
        ordering = ['inspection', 'defect_type']
        indexes = [
            models.Index(fields=['inspection', 'defect_type']),
        ]
    
    def __str__(self):
        return f"{self.inspection.inspection_number} - {self.defect_type.defect_name}"


# ==================== PACKING (Optimized) ====================

class PackingList(TimeStampedModel):
    packing_number = models.CharField(_("Packing#"), max_length=100, unique=True, db_index=True)
    packing_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.PROTECT, related_name='packings', db_index=True)
    invoice_number = models.CharField(_("Invoice#"), max_length=100, blank=True, db_index=True)
    container_number = models.CharField(_("Container#"), max_length=100, blank=True, db_index=True)
    total_cartons = models.IntegerField(_("Cartons"), default=0, validators=[MinValueValidator(0)])
    total_quantity = models.IntegerField(_("Qty"), default=0, validators=[MinValueValidator(0)])
    gross_weight = models.DecimalField(_("Gross"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    net_weight = models.DecimalField(_("Net"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    cbm = models.DecimalField(_("CBM"), max_digits=10, decimal_places=3, default=Decimal('0.000'), validators=[MinValueValidator(Decimal('0.000'))])
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('draft', 'Draft'), ('packed', 'Packed'), ('shipped', 'Shipped')
    ], default='draft', db_index=True)
    
    class Meta:
        verbose_name = "Packing List"
        ordering = ['-packing_date']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['-packing_date']),
        ]
    
    def __str__(self):
        return self.packing_number


class Carton(TimeStampedModel):
    packing = models.ForeignKey(PackingList, on_delete=models.CASCADE, related_name='cartons', db_index=True)
    carton_number = models.IntegerField(_("Carton#"), validators=[MinValueValidator(1)])
    carton_from = models.IntegerField(_("From"), validators=[MinValueValidator(1)])
    carton_to = models.IntegerField(_("To"), validators=[MinValueValidator(1)])
    length = models.DecimalField(_("L"), max_digits=6, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.01'))])
    width = models.DecimalField(_("W"), max_digits=6, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.01'))])
    height = models.DecimalField(_("H"), max_digits=6, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.01'))])
    gross_weight = models.DecimalField(_("Gross"), max_digits=8, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    net_weight = models.DecimalField(_("Net"), max_digits=8, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    total_pieces = models.IntegerField(_("Pieces"), default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        verbose_name = "Carton"
        ordering = ['packing', 'carton_number']
        indexes = [
            models.Index(fields=['packing', 'carton_number']),
        ]
    
    def __str__(self):
        return f"{self.packing.packing_number} - Carton {self.carton_number}"
    
    @cached_property
    def cbm(self):
        return (self.length * self.width * self.height) / 1000000
    
    def clean(self):
        if self.carton_from > self.carton_to:
            raise ValidationError('Carton From must be <= Carton To')


class CartonBreakdown(TimeStampedModel):
    carton = models.ForeignKey(Carton, on_delete=models.CASCADE, related_name='breakdowns', db_index=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, db_index=True)
    size = models.ForeignKey(Size, on_delete=models.PROTECT, db_index=True)
    quantity = models.IntegerField(_("Qty"), validators=[MinValueValidator(1)])
    
    class Meta:
        verbose_name = "Carton Breakdown"
        ordering = ['carton', 'color__name', 'size__sort_order']
        indexes = [
            models.Index(fields=['carton', 'color', 'size']),
        ]
    
    def __str__(self):
        return f"Carton {self.carton.carton_number} - {self.color.name} {self.size.name}"


# ==================== PHASE 2: TNA (TIME & ACTION) ====================

class TNATemplate(TimeStampedModel):
    """TNA Template for different garment types"""
    template_name = models.CharField(_("Template"), max_length=200, unique=True, db_index=True)
    garment_type = models.ForeignKey(GarmentType, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "TNA Template"
        ordering = ['template_name']
    
    def __str__(self):
        return self.template_name


class TNATask(TimeStampedModel):
    """TNA Task Master"""
    task_name = models.CharField(_("Task"), max_length=200, db_index=True)
    task_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    department = models.CharField(_("Department"), max_length=100, choices=[
        ('merchandising', 'Merchandising'), ('sampling', 'Sampling'), ('production', 'Production'),
        ('fabric', 'Fabric'), ('trim', 'Trim'), ('quality', 'Quality'), ('commercial', 'Commercial')
    ], db_index=True)
    standard_lead_time = models.IntegerField(_("Lead Days"), default=1, validators=[MinValueValidator(1)])
    is_critical = models.BooleanField(_("Critical"), default=False, db_index=True)
    sort_order = models.IntegerField(_("Order"), default=0, db_index=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "TNA Task"
        ordering = ['sort_order', 'task_name']
        indexes = [
            models.Index(fields=['department', 'is_active']),
            models.Index(fields=['sort_order', 'is_active']),
        ]
    
    def __str__(self):
        return self.task_name


class TNATemplateTask(TimeStampedModel):
    """Tasks in TNA Template"""
    template = models.ForeignKey(TNATemplate, on_delete=models.CASCADE, related_name='tasks', db_index=True)
    task = models.ForeignKey(TNATask, on_delete=models.PROTECT, db_index=True)
    sequence = models.IntegerField(_("Sequence"), validators=[MinValueValidator(1)])
    lead_time_days = models.IntegerField(_("Days"), validators=[MinValueValidator(1)])
    dependency = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependents', db_index=True)
    
    class Meta:
        verbose_name = "Template Task"
        ordering = ['template', 'sequence']
        unique_together = ['template', 'task']
        indexes = [
            models.Index(fields=['template', 'sequence']),
        ]
    
    def __str__(self):
        return f"{self.template.template_name} - {self.task.task_name}"


class OrderTNA(TimeStampedModel):
    """TNA for specific order"""
    order = models.ForeignKey(BuyerOrder, on_delete=models.CASCADE, related_name='tna', db_index=True)
    template = models.ForeignKey(TNATemplate, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    start_date = models.DateField(_("Start"), db_index=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Order TNA"
        ordering = ['order', 'start_date']
        indexes = [
            models.Index(fields=['order', 'is_active']),
        ]
    
    def __str__(self):
        return f"TNA - {self.order.order_number}"


class OrderTNATask(TimeStampedModel):
    """Individual TNA task for order"""
    order_tna = models.ForeignKey(OrderTNA, on_delete=models.CASCADE, related_name='tasks', db_index=True)
    task = models.ForeignKey(TNATask, on_delete=models.PROTECT, db_index=True)
    plan_start_date = models.DateField(_("Plan Start"), db_index=True)
    plan_end_date = models.DateField(_("Plan End"), db_index=True)
    actual_start_date = models.DateField(_("Actual Start"), null=True, blank=True, db_index=True)
    actual_end_date = models.DateField(_("Actual End"), null=True, blank=True, db_index=True)
    responsible_person = models.CharField(_("Responsible"), max_length=100, blank=True, db_index=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), 
        ('delayed', 'Delayed'), ('cancelled', 'Cancelled')
    ], default='pending', db_index=True)
    delay_days = models.IntegerField(_("Delay"), default=0)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Order TNA Task"
        ordering = ['order_tna', 'plan_start_date']
        unique_together = ['order_tna', 'task']
        indexes = [
            models.Index(fields=['order_tna', 'status']),
            models.Index(fields=['plan_end_date', 'status']),
            models.Index(fields=['status', 'task']),
        ]
    
    def __str__(self):
        return f"{self.order_tna.order.order_number} - {self.task.task_name}"
    
    @cached_property
    def is_delayed(self):
        if self.status != 'completed' and self.plan_end_date < timezone.now().date():
            return True
        return False
    
    def save(self, *args, **kwargs):
        # Calculate delay
        if self.actual_end_date and self.plan_end_date:
            delay = (self.actual_end_date - self.plan_end_date).days
            self.delay_days = max(0, delay)
        super().save(*args, **kwargs)


# ==================== PHASE 3: COMPLIANCE & CERTIFICATION ====================

class ComplianceType(TimeStampedModel):
    """Compliance types (BSCI, WRAP, etc.)"""
    name = models.CharField(_("Compliance"), max_length=100, unique=True, db_index=True)
    code = models.CharField(_("Code"), max_length=20, unique=True, db_index=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Compliance Type"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class FactoryCompliance(TimeStampedModel):
    """Factory compliance certificates"""
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE, related_name='compliances', db_index=True)
    compliance_type = models.ForeignKey(ComplianceType, on_delete=models.PROTECT, db_index=True)
    certificate_number = models.CharField(_("Certificate#"), max_length=100, db_index=True)
    issue_date = models.DateField(_("Issue Date"), db_index=True)
    expiry_date = models.DateField(_("Expiry"), db_index=True)
    issuing_authority = models.CharField(_("Authority"), max_length=200)
    certificate_file = models.FileField(_("File"), upload_to='garments/compliance/', blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('active', 'Active'), ('expired', 'Expired'), ('suspended', 'Suspended')
    ], default='active', db_index=True)
    
    class Meta:
        verbose_name = "Factory Compliance"
        ordering = ['factory', '-issue_date']
        unique_together = ['factory', 'compliance_type', 'certificate_number']
        indexes = [
            models.Index(fields=['factory', 'status']),
            models.Index(fields=['expiry_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.factory.factory_name} - {self.compliance_type.name}"
    
    @cached_property
    def is_expiring_soon(self):
        """Check if expiring within 30 days"""
        if self.expiry_date:
            days_to_expiry = (self.expiry_date - timezone.now().date()).days
            return 0 < days_to_expiry <= 30
        return False


class TestType(TimeStampedModel):
    """Test types (Lab tests, wash tests, etc.)"""
    test_name = models.CharField(_("Test"), max_length=200, unique=True, db_index=True)
    test_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    category = models.CharField(_("Category"), max_length=50, choices=[
        ('fabric', 'Fabric Test'), ('garment', 'Garment Test'), ('chemical', 'Chemical Test'), ('physical', 'Physical Test')
    ], db_index=True)
    standard_cost = models.DecimalField(_("Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    standard_lead_time = models.IntegerField(_("Lead Days"), default=7, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Test Type"
        ordering = ['category', 'test_name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return self.test_name


class OrderTest(TimeStampedModel):
    """Tests for specific order"""
    order = models.ForeignKey(BuyerOrder, on_delete=models.CASCADE, related_name='tests', db_index=True)
    test_type = models.ForeignKey(TestType, on_delete=models.PROTECT, db_index=True)
    test_number = models.CharField(_("Test#"), max_length=100, unique=True, db_index=True)
    lab_name = models.CharField(_("Lab"), max_length=200, db_index=True)
    submission_date = models.DateField(_("Submitted"), db_index=True)
    expected_result_date = models.DateField(_("Expected"), db_index=True)
    actual_result_date = models.DateField(_("Actual"), null=True, blank=True, db_index=True)
    result = models.CharField(_("Result"), max_length=20, choices=[
        ('pending', 'Pending'), ('passed', 'Passed'), ('failed', 'Failed'), ('conditional', 'Conditional')
    ], default='pending', db_index=True)
    test_cost = models.DecimalField(_("Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    report_file = models.FileField(_("Report"), upload_to='garments/test_reports/', blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Order Test"
        ordering = ['order', '-submission_date']
        indexes = [
            models.Index(fields=['order', 'result']),
            models.Index(fields=['test_type', 'result']),
            models.Index(fields=['-submission_date']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.test_type.test_name}"


# ==================== PHASE 4: ADVANCED FEATURES ====================

class ProductionPlan(TimeStampedModel):
    """Production planning"""
    plan_number = models.CharField(_("Plan#"), max_length=100, unique=True, db_index=True)
    plan_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    factory = models.ForeignKey(Factory, on_delete=models.PROTECT, related_name='production_plans', db_index=True)
    sewing_line = models.ForeignKey(SewingLine, on_delete=models.PROTECT, related_name='plans', db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.PROTECT, related_name='production_plans', db_index=True)
    style = models.ForeignKey(Style, on_delete=models.PROTECT, db_index=True)
    planned_quantity = models.IntegerField(_("Plan Qty"), validators=[MinValueValidator(1)])
    start_date = models.DateField(_("Start"), db_index=True)
    end_date = models.DateField(_("End"), db_index=True)
    smv = models.DecimalField(_("SMV"), max_digits=6, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.01'))])
    target_efficiency = models.DecimalField(_("Target%"), max_digits=5, decimal_places=2, default=Decimal('75.00'), validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))])
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('planned', 'Planned'), ('running', 'Running'), ('completed', 'Completed'), ('cancelled', 'Cancelled')
    ], default='planned', db_index=True)
    
    class Meta:
        verbose_name = "Production Plan"
        ordering = ['-plan_date']
        indexes = [
            models.Index(fields=['factory', 'status']),
            models.Index(fields=['sewing_line', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.plan_number} - {self.order.order_number}"
    
    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date must be before end date')


class DailyProduction(TimeStampedModel):
    """Daily production tracking"""
    production_date = models.DateField(_("Date"), db_index=True)
    production_plan = models.ForeignKey(ProductionPlan, on_delete=models.PROTECT, related_name='daily_productions', db_index=True)
    sewing_line = models.ForeignKey(SewingLine, on_delete=models.PROTECT, db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.PROTECT, db_index=True)
    target_quantity = models.IntegerField(_("Target"), validators=[MinValueValidator(0)])
    produced_quantity = models.IntegerField(_("Produced"), default=0, validators=[MinValueValidator(0)])
    rejected_quantity = models.IntegerField(_("Rejected"), default=0, validators=[MinValueValidator(0)])
    rework_quantity = models.IntegerField(_("Rework"), default=0, validators=[MinValueValidator(0)])
    working_hours = models.DecimalField(_("Hours"), max_digits=4, decimal_places=2, default=Decimal('8.00'), validators=[MinValueValidator(Decimal('0.01'))])
    operators_present = models.IntegerField(_("Operators"), default=0, validators=[MinValueValidator(0)])
    efficiency_percent = models.DecimalField(_("Efficiency%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Daily Production"
        ordering = ['-production_date']
        unique_together = ['production_date', 'production_plan', 'sewing_line']
        indexes = [
            models.Index(fields=['production_date', 'sewing_line']),
            models.Index(fields=['production_plan', 'production_date']),
            models.Index(fields=['-production_date']),
        ]
    
    def __str__(self):
        return f"{self.sewing_line.line_number} - {self.production_date}"
    
    @cached_property
    def achievement_percent(self):
        if self.target_quantity > 0:
            return (self.produced_quantity / self.target_quantity) * 100
        return Decimal('0.00')
    
    @cached_property
    def rejection_percent(self):
        if self.produced_quantity > 0:
            return (self.rejected_quantity / self.produced_quantity) * 100
        return Decimal('0.00')


class FabricReceive(TimeStampedModel):
    """Fabric receiving"""
    receive_number = models.CharField(_("Receive#"), max_length=100, unique=True, db_index=True)
    receive_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.PROTECT, related_name='fabric_receives', db_index=True)
    fabric = models.ForeignKey(Fabric, on_delete=models.PROTECT, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, db_index=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, db_index=True)
    lot_number = models.CharField(_("Lot#"), max_length=100, db_index=True)
    roll_count = models.IntegerField(_("Rolls"), validators=[MinValueValidator(1)])
    received_quantity = models.DecimalField(_("Qty"), max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.CharField(_("Unit"), max_length=20, choices=[('meter', 'Meter'), ('yard', 'Yard'), ('kg', 'KG')], default='meter')
    challan_number = models.CharField(_("Challan#"), max_length=100, blank=True, db_index=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Fabric Receive"
        ordering = ['-receive_date']
        indexes = [
            models.Index(fields=['order', 'fabric']),
            models.Index(fields=['supplier', 'receive_date']),
            models.Index(fields=['-receive_date']),
        ]
    
    def __str__(self):
        return f"{self.receive_number} - {self.fabric.fabric_name}"


class TrimReceive(TimeStampedModel):
    """Trim receiving"""
    receive_number = models.CharField(_("Receive#"), max_length=100, unique=True, db_index=True)
    receive_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.PROTECT, related_name='trim_receives', db_index=True)
    trim = models.ForeignKey(Trim, on_delete=models.PROTECT, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, db_index=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, null=True, blank=True, db_index=True)
    lot_number = models.CharField(_("Lot#"), max_length=100, db_index=True)
    received_quantity = models.DecimalField(_("Qty"), max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    challan_number = models.CharField(_("Challan#"), max_length=100, blank=True, db_index=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Trim Receive"
        ordering = ['-receive_date']
        indexes = [
            models.Index(fields=['order', 'trim']),
            models.Index(fields=['supplier', 'receive_date']),
            models.Index(fields=['-receive_date']),
        ]
    
    def __str__(self):
        return f"{self.receive_number} - {self.trim.trim_name}"


class Shipment(TimeStampedModel):
    """Shipment tracking"""
    shipment_number = models.CharField(_("Shipment#"), max_length=100, unique=True, db_index=True)
    shipment_date = models.DateField(_("Date"), db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.PROTECT, related_name='shipments', db_index=True)
    invoice_number = models.CharField(_("Invoice#"), max_length=100, db_index=True)
    invoice_value = models.DecimalField(_("Value"), max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    shipped_quantity = models.IntegerField(_("Qty"), validators=[MinValueValidator(1)])
    shipment_mode = models.CharField(_("Mode"), max_length=50, choices=[
        ('sea', 'Sea'), ('air', 'Air'), ('courier', 'Courier')
    ], db_index=True)
    container_number = models.CharField(_("Container#"), max_length=100, blank=True, db_index=True)
    bl_number = models.CharField(_("BL#"), max_length=100, blank=True, db_index=True)
    bl_date = models.DateField(_("BL Date"), null=True, blank=True, db_index=True)
    etd = models.DateField(_("ETD"), null=True, blank=True, db_index=True)
    eta = models.DateField(_("ETA"), null=True, blank=True, db_index=True)
    port_of_loading = models.CharField(_("POL"), max_length=100, default="Chittagong")
    port_of_discharge = models.CharField(_("POD"), max_length=100)
    forwarder = models.CharField(_("Forwarder"), max_length=200, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('preparing', 'Preparing'), ('shipped', 'Shipped'), ('in_transit', 'In Transit'), 
        ('arrived', 'Arrived'), ('delivered', 'Delivered')
    ], default='preparing', db_index=True)
    
    class Meta:
        verbose_name = "Shipment"
        ordering = ['-shipment_date']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['-shipment_date']),
            models.Index(fields=['status', 'eta']),
        ]
    
    def __str__(self):
        return f"{self.shipment_number} - {self.order.order_number}"



# ==================== PHASE 6: COSTING & PRICING MANAGEMENT ====================

class CostingSheet(TimeStampedModel):
    """Detailed costing breakdown for styles"""
    costing_number = models.CharField(_("Costing#"), max_length=100, unique=True, db_index=True)
    style = models.ForeignKey(Style, on_delete=models.CASCADE, related_name='costing_sheets', db_index=True)
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT, db_index=True)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    version = models.IntegerField(_("Version"), default=1, validators=[MinValueValidator(1)])
    costing_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    
    # Costs
    fabric_cost = models.DecimalField(_("Fabric"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    trim_cost = models.DecimalField(_("Trim"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    embellishment_cost = models.DecimalField(_("Embellishment"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    cm_cost = models.DecimalField(_("CM"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    testing_cost = models.DecimalField(_("Testing"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    commercial_cost = models.DecimalField(_("Commercial"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    other_cost = models.DecimalField(_("Other"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(_("Total Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Pricing
    target_price = models.DecimalField(_("Target Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    quoted_price = models.DecimalField(_("Quoted Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    final_price = models.DecimalField(_("Final Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Margins
    margin_amount = models.DecimalField(_("Margin"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    margin_percent = models.DecimalField(_("Margin%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')
    ], default='draft', db_index=True)
    
    approved_by = models.CharField(_("Approved By"), max_length=100, blank=True)
    approved_date = models.DateField(_("Approved Date"), null=True, blank=True, db_index=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Costing Sheet"
        ordering = ['-costing_date']
        unique_together = ['style', 'version']
        indexes = [
            models.Index(fields=['style', 'status']),
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['-costing_date']),
            models.Index(fields=['status', 'approved_date']),
        ]
    
    def __str__(self):
        return f"{self.costing_number} - {self.style.style_number}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate totals
        self.total_cost = (
            self.fabric_cost + self.trim_cost + self.embellishment_cost + 
            self.cm_cost + self.testing_cost + self.commercial_cost + self.other_cost
        )
        if self.final_price > 0:
            self.margin_amount = self.final_price - self.total_cost
            self.margin_percent = (self.margin_amount / self.final_price) * 100
        super().save(*args, **kwargs)
    
    @cached_property
    def is_profitable(self):
        return self.margin_percent > 0


class CostingComponent(TimeStampedModel):
    """Individual cost components breakdown"""
    costing_sheet = models.ForeignKey(CostingSheet, on_delete=models.CASCADE, related_name='components', db_index=True)
    component_type = models.CharField(_("Type"), max_length=50, choices=[
        ('fabric', 'Fabric'), ('trim', 'Trim'), ('embellishment', 'Embellishment'),
        ('labor', 'Labor'), ('overhead', 'Overhead'), ('other', 'Other')
    ], db_index=True)
    description = models.CharField(_("Description"), max_length=200, db_index=True)
    quantity = models.DecimalField(_("Qty"), max_digits=10, decimal_places=4, validators=[MinValueValidator(Decimal('0.0001'))])
    unit = models.CharField(_("Unit"), max_length=20, default="PCS")
    unit_cost = models.DecimalField(_("Unit Cost"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    total_cost = models.DecimalField(_("Total"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    wastage_percent = models.DecimalField(_("Wastage%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    final_cost = models.DecimalField(_("Final Cost"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Costing Component"
        ordering = ['costing_sheet', 'component_type', 'description']
        indexes = [
            models.Index(fields=['costing_sheet', 'component_type']),
        ]
    
    def __str__(self):
        return f"{self.costing_sheet.costing_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        wastage_amount = self.total_cost * (self.wastage_percent / 100)
        self.final_cost = self.total_cost + wastage_amount
        super().save(*args, **kwargs)


class PriceList(TimeStampedModel):
    """Price lists for different buyers/markets"""
    price_list_name = models.CharField(_("Price List"), max_length=200, unique=True, db_index=True)
    price_list_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='price_lists', db_index=True)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    currency = models.CharField(_("Currency"), max_length=10, default="USD", db_index=True)
    valid_from = models.DateField(_("Valid From"), db_index=True)
    valid_to = models.DateField(_("Valid To"), db_index=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Price List"
        ordering = ['-valid_from']
        indexes = [
            models.Index(fields=['buyer', 'is_active']),
            models.Index(fields=['season', 'is_active']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]
    
    def __str__(self):
        return f"{self.price_list_name} - {self.buyer.buyer_name}"
    
    def clean(self):
        if self.valid_from and self.valid_to and self.valid_from >= self.valid_to:
            raise ValidationError('Valid From must be before Valid To')


class PriceListItem(TimeStampedModel):
    """Individual style prices in price list"""
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='items', db_index=True)
    style = models.ForeignKey(Style, on_delete=models.CASCADE, db_index=True)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    min_quantity = models.IntegerField(_("Min Qty"), default=0, validators=[MinValueValidator(0)])
    max_quantity = models.IntegerField(_("Max Qty"), default=0, validators=[MinValueValidator(0)])
    discount_percent = models.DecimalField(_("Discount%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    final_price = models.DecimalField(_("Final Price"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Price List Item"
        ordering = ['price_list', 'style']
        unique_together = ['price_list', 'style']
        indexes = [
            models.Index(fields=['price_list', 'style']),
        ]
    
    def __str__(self):
        return f"{self.price_list.price_list_name} - {self.style.style_number}"
    
    def save(self, *args, **kwargs):
        discount_amount = self.unit_price * (self.discount_percent / 100)
        self.final_price = self.unit_price - discount_amount
        super().save(*args, **kwargs)


class QuotationCosting(TimeStampedModel):
    """Costing at quotation level"""
    quotation_number = models.CharField(_("Quotation#"), max_length=100, unique=True, db_index=True)
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT, db_index=True)
    style = models.ForeignKey(Style, on_delete=models.PROTECT, db_index=True)
    costing_sheet = models.ForeignKey(CostingSheet, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    quotation_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    quantity = models.IntegerField(_("Qty"), validators=[MinValueValidator(1)])
    
    # Costs
    total_cost = models.DecimalField(_("Total Cost"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    quoted_price = models.DecimalField(_("Quoted Price"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    total_value = models.DecimalField(_("Total Value"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Margins
    margin_per_piece = models.DecimalField(_("Margin/Pc"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    margin_percent = models.DecimalField(_("Margin%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    total_margin = models.DecimalField(_("Total Margin"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('pending', 'Pending'), ('sent', 'Sent'), ('accepted', 'Accepted'), ('rejected', 'Rejected')
    ], default='pending', db_index=True)
    
    class Meta:
        verbose_name = "Quotation Costing"
        ordering = ['-quotation_date']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['style', 'status']),
            models.Index(fields=['-quotation_date']),
        ]
    
    def __str__(self):
        return f"{self.quotation_number} - {self.style.style_number}"
    
    def save(self, *args, **kwargs):
        self.total_value = self.quantity * self.quoted_price
        if self.costing_sheet:
            self.total_cost = self.quantity * self.costing_sheet.total_cost
            self.margin_per_piece = self.quoted_price - self.costing_sheet.total_cost
            if self.quoted_price > 0:
                self.margin_percent = (self.margin_per_piece / self.quoted_price) * 100
            self.total_margin = self.quantity * self.margin_per_piece
        super().save(*args, **kwargs)


class OrderCosting(TimeStampedModel):
    """Actual costing for confirmed orders"""
    order = models.OneToOneField(BuyerOrder, on_delete=models.CASCADE, related_name='order_costing', db_index=True)
    costing_sheet = models.ForeignKey(CostingSheet, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    
    # Budgeted Costs (from costing sheet)
    budgeted_fabric = models.DecimalField(_("Budget Fabric"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    budgeted_trim = models.DecimalField(_("Budget Trim"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    budgeted_cm = models.DecimalField(_("Budget CM"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    budgeted_other = models.DecimalField(_("Budget Other"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    budgeted_total = models.DecimalField(_("Budget Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Actual Costs (from actual transactions)
    actual_fabric = models.DecimalField(_("Actual Fabric"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    actual_trim = models.DecimalField(_("Actual Trim"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    actual_cm = models.DecimalField(_("Actual CM"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    actual_other = models.DecimalField(_("Actual Other"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    actual_total = models.DecimalField(_("Actual Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Revenue
    order_value = models.DecimalField(_("Order Value"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Profit
    budgeted_profit = models.DecimalField(_("Budget Profit"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    actual_profit = models.DecimalField(_("Actual Profit"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    profit_variance = models.DecimalField(_("Variance"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    last_updated = models.DateTimeField(_("Last Updated"), auto_now=True)
    
    class Meta:
        verbose_name = "Order Costing"
        ordering = ['-last_updated']
        indexes = [
            models.Index(fields=['order', 'last_updated']),
        ]
    
    def __str__(self):
        return f"Costing - {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        self.budgeted_total = self.budgeted_fabric + self.budgeted_trim + self.budgeted_cm + self.budgeted_other
        self.actual_total = self.actual_fabric + self.actual_trim + self.actual_cm + self.actual_other
        self.budgeted_profit = self.order_value - self.budgeted_total
        self.actual_profit = self.order_value - self.actual_total
        self.profit_variance = self.actual_profit - self.budgeted_profit
        super().save(*args, **kwargs)
    
    @cached_property
    def budgeted_margin_percent(self):
        if self.order_value > 0:
            return (self.budgeted_profit / self.order_value) * 100
        return Decimal('0.00')
    
    @cached_property
    def actual_margin_percent(self):
        if self.order_value > 0:
            return (self.actual_profit / self.order_value) * 100
        return Decimal('0.00')


class ProfitAnalysis(TimeStampedModel):
    """Profit analysis per order/style/buyer"""
    analysis_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    analysis_type = models.CharField(_("Type"), max_length=20, choices=[
        ('order', 'Order'), ('style', 'Style'), ('buyer', 'Buyer'), ('season', 'Season')
    ], db_index=True)
    
    # References
    order = models.ForeignKey(BuyerOrder, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    style = models.ForeignKey(Style, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    
    # Metrics
    total_revenue = models.DecimalField(_("Revenue"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(_("Cost"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    gross_profit = models.DecimalField(_("Gross Profit"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    gross_margin_percent = models.DecimalField(_("Margin%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    quantity = models.IntegerField(_("Qty"), default=0)
    profit_per_piece = models.DecimalField(_("Profit/Pc"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Profit Analysis"
        ordering = ['-analysis_date']
        indexes = [
            models.Index(fields=['analysis_type', 'analysis_date']),
            models.Index(fields=['buyer', 'analysis_date']),
            models.Index(fields=['season', 'analysis_date']),
            models.Index(fields=['-analysis_date']),
        ]
    
    def __str__(self):
        return f"Profit Analysis - {self.analysis_date}"
    
    def save(self, *args, **kwargs):
        self.gross_profit = self.total_revenue - self.total_cost
        if self.total_revenue > 0:
            self.gross_margin_percent = (self.gross_profit / self.total_revenue) * 100
        if self.quantity > 0:
            self.profit_per_piece = self.gross_profit / self.quantity
        super().save(*args, **kwargs)


class CostVariance(TimeStampedModel):
    """Track cost variances between budgeted and actual"""
    order = models.ForeignKey(BuyerOrder, on_delete=models.CASCADE, related_name='cost_variances', db_index=True)
    variance_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    cost_category = models.CharField(_("Category"), max_length=50, choices=[
        ('fabric', 'Fabric'), ('trim', 'Trim'), ('cm', 'CM'), ('overhead', 'Overhead'), ('other', 'Other')
    ], db_index=True)
    
    budgeted_amount = models.DecimalField(_("Budgeted"), max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    actual_amount = models.DecimalField(_("Actual"), max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    variance_amount = models.DecimalField(_("Variance"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    variance_percent = models.DecimalField(_("Variance%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    variance_type = models.CharField(_("Type"), max_length=20, choices=[
        ('favorable', 'Favorable'), ('unfavorable', 'Unfavorable'), ('neutral', 'Neutral')
    ], default='neutral', db_index=True)
    
    reason = models.TextField(_("Reason"), blank=True)
    action_taken = models.TextField(_("Action"), blank=True)
    
    class Meta:
        verbose_name = "Cost Variance"
        ordering = ['-variance_date']
        indexes = [
            models.Index(fields=['order', 'cost_category']),
            models.Index(fields=['variance_type', 'variance_date']),
            models.Index(fields=['-variance_date']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.cost_category}"
    
    def save(self, *args, **kwargs):
        self.variance_amount = self.actual_amount - self.budgeted_amount
        if self.budgeted_amount > 0:
            self.variance_percent = (self.variance_amount / self.budgeted_amount) * 100
        
        # Determine variance type
        if self.variance_amount < 0:
            self.variance_type = 'favorable'  # Actual less than budget
        elif self.variance_amount > 0:
            self.variance_type = 'unfavorable'  # Actual more than budget
        else:
            self.variance_type = 'neutral'
        
        super().save(*args, **kwargs)



# ==================== PHASE 7: CAPACITY PLANNING & SCHEDULING ====================

class CapacityPlan(TimeStampedModel):
    """Factory capacity planning"""
    plan_number = models.CharField(_("Plan#"), max_length=100, unique=True, db_index=True)
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE, related_name='capacity_plans', db_index=True)
    plan_month = models.DateField(_("Month"), db_index=True)
    total_working_days = models.IntegerField(_("Working Days"), validators=[MinValueValidator(1), MaxValueValidator(31)])
    total_working_hours = models.DecimalField(_("Working Hours"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Capacity
    total_operators = models.IntegerField(_("Operators"), validators=[MinValueValidator(0)])
    total_machines = models.IntegerField(_("Machines"), validators=[MinValueValidator(0)])
    total_lines = models.IntegerField(_("Lines"), validators=[MinValueValidator(0)])
    capacity_minutes = models.DecimalField(_("Capacity (Min)"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Utilization
    planned_minutes = models.DecimalField(_("Planned (Min)"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    utilization_percent = models.DecimalField(_("Utilization%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('in_progress', 'In Progress'), ('completed', 'Completed')
    ], default='draft', db_index=True)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Capacity Plan"
        ordering = ['-plan_month']
        unique_together = ['factory', 'plan_month']
        indexes = [
            models.Index(fields=['factory', 'status']),
            models.Index(fields=['-plan_month']),
            models.Index(fields=['status', 'plan_month']),
        ]
    
    def __str__(self):
        return f"{self.plan_number} - {self.factory.factory_name}"
    
    def save(self, *args, **kwargs):
        # Calculate capacity minutes
        self.capacity_minutes = Decimal(str(self.total_operators)) * Decimal(str(self.total_working_hours)) * Decimal('60')
        
        # Calculate utilization
        if self.capacity_minutes > 0:
            self.utilization_percent = (self.planned_minutes / self.capacity_minutes) * 100
        
        super().save(*args, **kwargs)
    
    @cached_property
    def available_minutes(self):
        return self.capacity_minutes - self.planned_minutes


class LineCapacity(TimeStampedModel):
    """Line-wise capacity details"""
    capacity_plan = models.ForeignKey(CapacityPlan, on_delete=models.CASCADE, related_name='line_capacities', db_index=True)
    sewing_line = models.ForeignKey(SewingLine, on_delete=models.CASCADE, db_index=True)
    
    working_days = models.IntegerField(_("Working Days"), validators=[MinValueValidator(1)])
    working_hours_per_day = models.DecimalField(_("Hours/Day"), max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    operators = models.IntegerField(_("Operators"), validators=[MinValueValidator(1)])
    
    # Capacity
    capacity_minutes = models.DecimalField(_("Capacity (Min)"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    planned_minutes = models.DecimalField(_("Planned (Min)"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    utilization_percent = models.DecimalField(_("Utilization%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Efficiency
    target_efficiency = models.DecimalField(_("Target Eff%"), max_digits=5, decimal_places=2, default=Decimal('85.00'))
    actual_efficiency = models.DecimalField(_("Actual Eff%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Line Capacity"
        ordering = ['capacity_plan', 'sewing_line']
        unique_together = ['capacity_plan', 'sewing_line']
        indexes = [
            models.Index(fields=['capacity_plan', 'sewing_line']),
        ]
    
    def __str__(self):
        return f"{self.capacity_plan.plan_number} - {self.sewing_line.line_number}"
    
    def save(self, *args, **kwargs):
        # Calculate capacity
        total_hours = Decimal(str(self.working_days)) * self.working_hours_per_day
        self.capacity_minutes = Decimal(str(self.operators)) * total_hours * Decimal('60')
        
        # Calculate utilization
        if self.capacity_minutes > 0:
            self.utilization_percent = (self.planned_minutes / self.capacity_minutes) * 100
        
        super().save(*args, **kwargs)


class ProductionSchedule(TimeStampedModel):
    """Detailed production schedule"""
    schedule_number = models.CharField(_("Schedule#"), max_length=100, unique=True, db_index=True)
    capacity_plan = models.ForeignKey(CapacityPlan, on_delete=models.CASCADE, related_name='schedules', db_index=True)
    sewing_line = models.ForeignKey(SewingLine, on_delete=models.CASCADE, db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.CASCADE, db_index=True)
    style = models.ForeignKey(Style, on_delete=models.CASCADE, db_index=True)
    
    # Schedule
    scheduled_date = models.DateField(_("Date"), db_index=True)
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    
    # Quantity
    planned_quantity = models.IntegerField(_("Planned Qty"), validators=[MinValueValidator(1)])
    actual_quantity = models.IntegerField(_("Actual Qty"), default=0, validators=[MinValueValidator(0)])
    
    # Time
    smv = models.DecimalField(_("SMV"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    required_minutes = models.DecimalField(_("Required Min"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('scheduled', 'Scheduled'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')
    ], default='scheduled', db_index=True)
    
    priority = models.IntegerField(_("Priority"), default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Production Schedule"
        ordering = ['scheduled_date', 'start_time', 'priority']
        indexes = [
            models.Index(fields=['sewing_line', 'scheduled_date']),
            models.Index(fields=['order', 'status']),
            models.Index(fields=['scheduled_date', 'status']),
            models.Index(fields=['status', 'priority']),
        ]
    
    def __str__(self):
        return f"{self.schedule_number} - {self.sewing_line.line_number}"
    
    def save(self, *args, **kwargs):
        self.required_minutes = Decimal(str(self.planned_quantity)) * self.smv
        super().save(*args, **kwargs)
    
    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Start time must be before end time')


class ScheduleConflict(TimeStampedModel):
    """Track scheduling conflicts"""
    conflict_date = models.DateField(_("Date"), db_index=True)
    sewing_line = models.ForeignKey(SewingLine, on_delete=models.CASCADE, db_index=True)
    schedule1 = models.ForeignKey(ProductionSchedule, on_delete=models.CASCADE, related_name='conflicts_as_first', db_index=True)
    schedule2 = models.ForeignKey(ProductionSchedule, on_delete=models.CASCADE, related_name='conflicts_as_second', db_index=True)
    
    conflict_type = models.CharField(_("Type"), max_length=50, choices=[
        ('time_overlap', 'Time Overlap'),
        ('capacity_exceeded', 'Capacity Exceeded'),
        ('resource_unavailable', 'Resource Unavailable'),
        ('other', 'Other')
    ], db_index=True)
    
    severity = models.CharField(_("Severity"), max_length=20, choices=[
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')
    ], default='medium', db_index=True)
    
    description = models.TextField(_("Description"))
    resolution = models.TextField(_("Resolution"), blank=True)
    
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('open', 'Open'), ('resolved', 'Resolved'), ('ignored', 'Ignored')
    ], default='open', db_index=True)
    
    resolved_by = models.CharField(_("Resolved By"), max_length=100, blank=True)
    resolved_date = models.DateTimeField(_("Resolved Date"), null=True, blank=True, db_index=True)
    
    class Meta:
        verbose_name = "Schedule Conflict"
        ordering = ['-conflict_date', '-severity']
        indexes = [
            models.Index(fields=['sewing_line', 'status']),
            models.Index(fields=['conflict_date', 'status']),
            models.Index(fields=['severity', 'status']),
        ]
    
    def __str__(self):
        return f"Conflict - {self.sewing_line.line_number} - {self.conflict_date}"


class ResourceAllocation(TimeStampedModel):
    """Allocate resources (machines, operators) to production"""
    allocation_number = models.CharField(_("Allocation#"), max_length=100, unique=True, db_index=True)
    production_schedule = models.ForeignKey(ProductionSchedule, on_delete=models.CASCADE, related_name='resource_allocations', db_index=True)
    
    resource_type = models.CharField(_("Type"), max_length=50, choices=[
        ('operator', 'Operator'),
        ('machine', 'Machine'),
        ('helper', 'Helper'),
        ('supervisor', 'Supervisor'),
        ('other', 'Other')
    ], db_index=True)
    
    resource_name = models.CharField(_("Resource"), max_length=200, db_index=True)
    quantity = models.IntegerField(_("Qty"), validators=[MinValueValidator(1)])
    
    allocated_from = models.DateTimeField(_("From"), db_index=True)
    allocated_to = models.DateTimeField(_("To"), db_index=True)
    
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('allocated', 'Allocated'), ('in_use', 'In Use'), ('released', 'Released'), ('cancelled', 'Cancelled')
    ], default='allocated', db_index=True)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Resource Allocation"
        ordering = ['allocated_from']
        indexes = [
            models.Index(fields=['production_schedule', 'resource_type']),
            models.Index(fields=['resource_type', 'status']),
            models.Index(fields=['allocated_from', 'allocated_to']),
        ]
    
    def __str__(self):
        return f"{self.allocation_number} - {self.resource_name}"
    
    def clean(self):
        if self.allocated_from and self.allocated_to and self.allocated_from >= self.allocated_to:
            raise ValidationError('Allocated From must be before Allocated To')


class DowntimeTracking(TimeStampedModel):
    """Track machine/line downtime"""
    downtime_number = models.CharField(_("Downtime#"), max_length=100, unique=True, db_index=True)
    downtime_date = models.DateField(_("Date"), db_index=True)
    sewing_line = models.ForeignKey(SewingLine, on_delete=models.CASCADE, related_name='downtimes', db_index=True)
    
    downtime_type = models.CharField(_("Type"), max_length=50, choices=[
        ('machine_breakdown', 'Machine Breakdown'),
        ('power_failure', 'Power Failure'),
        ('material_shortage', 'Material Shortage'),
        ('maintenance', 'Maintenance'),
        ('no_work', 'No Work'),
        ('other', 'Other')
    ], db_index=True)
    
    start_time = models.DateTimeField(_("Start Time"), db_index=True)
    end_time = models.DateTimeField(_("End Time"), null=True, blank=True, db_index=True)
    duration_minutes = models.DecimalField(_("Duration (Min)"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    reason = models.TextField(_("Reason"))
    action_taken = models.TextField(_("Action"), blank=True)
    
    reported_by = models.CharField(_("Reported By"), max_length=100)
    resolved_by = models.CharField(_("Resolved By"), max_length=100, blank=True)
    
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('ongoing', 'Ongoing'), ('resolved', 'Resolved')
    ], default='ongoing', db_index=True)
    
    class Meta:
        verbose_name = "Downtime Tracking"
        ordering = ['-downtime_date', '-start_time']
        indexes = [
            models.Index(fields=['sewing_line', 'downtime_date']),
            models.Index(fields=['downtime_type', 'status']),
            models.Index(fields=['-downtime_date']),
        ]
    
    def __str__(self):
        return f"{self.downtime_number} - {self.sewing_line.line_number}"
    
    def save(self, *args, **kwargs):
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            self.duration_minutes = Decimal(str(duration.total_seconds() / 60))
        super().save(*args, **kwargs)


class EfficiencyTracking(TimeStampedModel):
    """Track line efficiency over time"""
    tracking_date = models.DateField(_("Date"), db_index=True)
    sewing_line = models.ForeignKey(SewingLine, on_delete=models.CASCADE, related_name='efficiency_records', db_index=True)
    production_schedule = models.ForeignKey(ProductionSchedule, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    
    # Manpower
    operators_present = models.IntegerField(_("Operators"), validators=[MinValueValidator(0)])
    helpers_present = models.IntegerField(_("Helpers"), default=0, validators=[MinValueValidator(0)])
    
    # Time
    working_hours = models.DecimalField(_("Working Hours"), max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    available_minutes = models.DecimalField(_("Available Min"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Production
    target_quantity = models.IntegerField(_("Target Qty"), validators=[MinValueValidator(0)])
    produced_quantity = models.IntegerField(_("Produced Qty"), validators=[MinValueValidator(0)])
    smv = models.DecimalField(_("SMV"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Calculated
    earned_minutes = models.DecimalField(_("Earned Min"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    efficiency_percent = models.DecimalField(_("Efficiency%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    achievement_percent = models.DecimalField(_("Achievement%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Downtime
    downtime_minutes = models.DecimalField(_("Downtime (Min)"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Efficiency Tracking"
        ordering = ['-tracking_date']
        unique_together = ['tracking_date', 'sewing_line']
        indexes = [
            models.Index(fields=['sewing_line', 'tracking_date']),
            models.Index(fields=['-tracking_date']),
        ]
    
    def __str__(self):
        return f"{self.sewing_line.line_number} - {self.tracking_date}"
    
    def save(self, *args, **kwargs):
        # Calculate available minutes
        self.available_minutes = Decimal(str(self.operators_present)) * self.working_hours * Decimal('60')
        
        # Calculate earned minutes
        self.earned_minutes = Decimal(str(self.produced_quantity)) * self.smv
        
        # Calculate efficiency
        if self.available_minutes > 0:
            self.efficiency_percent = (self.earned_minutes / self.available_minutes) * 100
        
        # Calculate achievement
        if self.target_quantity > 0:
            self.achievement_percent = (Decimal(str(self.produced_quantity)) / Decimal(str(self.target_quantity))) * 100
        
        super().save(*args, **kwargs)
    
    @cached_property
    def is_target_achieved(self):
        return self.achievement_percent >= 100



# ==================== PHASE 8: QUALITY MANAGEMENT SYSTEM ====================

class QualityStandard(TimeStampedModel):
    """Quality standards (AQL, buyer standards)"""
    standard_name = models.CharField(_("Standard"), max_length=200, unique=True, db_index=True)
    standard_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    standard_type = models.CharField(_("Type"), max_length=50, choices=[
        ('aql', 'AQL'), ('buyer', 'Buyer Standard'), ('iso', 'ISO'), ('internal', 'Internal'), ('other', 'Other')
    ], db_index=True)
    description = models.TextField(_("Description"), blank=True)
    aql_level = models.CharField(_("AQL Level"), max_length=20, blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Quality Standard"
        ordering = ['standard_name']
        indexes = [models.Index(fields=['standard_type', 'is_active'])]
    
    def __str__(self):
        return self.standard_name


class InspectionPlan(TimeStampedModel):
    """Inspection plan per style"""
    plan_number = models.CharField(_("Plan#"), max_length=100, unique=True, db_index=True)
    style = models.ForeignKey(Style, on_delete=models.CASCADE, related_name='inspection_plans', db_index=True)
    quality_standard = models.ForeignKey(QualityStandard, on_delete=models.PROTECT, db_index=True)
    inspection_stage = models.CharField(_("Stage"), max_length=50, choices=[
        ('inline', 'Inline'), ('midline', 'Midline'), ('endline', 'Endline'), 
        ('final', 'Final'), ('pre_shipment', 'Pre-Shipment')
    ], db_index=True)
    sample_size = models.IntegerField(_("Sample Size"), validators=[MinValueValidator(1)])
    acceptance_level = models.DecimalField(_("Acceptance%"), max_digits=5, decimal_places=2, default=Decimal('95.00'))
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Inspection Plan"
        ordering = ['style', 'inspection_stage']
        indexes = [models.Index(fields=['style', 'inspection_stage'])]
    
    def __str__(self):
        return f"{self.plan_number} - {self.style.style_number}"



class InspectionCheckpoint(TimeStampedModel):
    """Checkpoints in inspection"""
    inspection_plan = models.ForeignKey(InspectionPlan, on_delete=models.CASCADE, related_name='checkpoints', db_index=True)
    checkpoint_name = models.CharField(_("Checkpoint"), max_length=200, db_index=True)
    checkpoint_type = models.CharField(_("Type"), max_length=50, choices=[
        ('measurement', 'Measurement'), ('visual', 'Visual'), ('functional', 'Functional'), ('other', 'Other')
    ], db_index=True)
    description = models.TextField(_("Description"), blank=True)
    acceptance_criteria = models.TextField(_("Criteria"))
    is_critical = models.BooleanField(_("Critical"), default=False, db_index=True)
    sort_order = models.IntegerField(_("Order"), default=0)
    
    class Meta:
        verbose_name = "Inspection Checkpoint"
        ordering = ['inspection_plan', 'sort_order']
        indexes = [models.Index(fields=['inspection_plan', 'is_critical'])]
    
    def __str__(self):
        return f"{self.inspection_plan.plan_number} - {self.checkpoint_name}"


class QualityParameter(TimeStampedModel):
    """Measurable quality parameters"""
    parameter_name = models.CharField(_("Parameter"), max_length=200, db_index=True)
    parameter_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    unit = models.CharField(_("Unit"), max_length=20)
    min_value = models.DecimalField(_("Min"), max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(_("Max"), max_digits=10, decimal_places=2, null=True, blank=True)
    target_value = models.DecimalField(_("Target"), max_digits=10, decimal_places=2, null=True, blank=True)
    tolerance = models.DecimalField(_("Tolerance"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Quality Parameter"
        ordering = ['parameter_name']
    
    def __str__(self):
        return f"{self.parameter_name} ({self.unit})"



class MeasurementRecord(TimeStampedModel):
    """Record measurements"""
    record_number = models.CharField(_("Record#"), max_length=100, unique=True, db_index=True)
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='measurements', db_index=True)
    quality_parameter = models.ForeignKey(QualityParameter, on_delete=models.PROTECT, db_index=True)
    measured_value = models.DecimalField(_("Value"), max_digits=10, decimal_places=2)
    is_within_tolerance = models.BooleanField(_("OK"), default=True, db_index=True)
    measured_by = models.CharField(_("Measured By"), max_length=100)
    measured_date = models.DateTimeField(_("Date"), default=timezone.now, db_index=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Measurement Record"
        ordering = ['-measured_date']
        indexes = [models.Index(fields=['inspection', 'quality_parameter'])]
    
    def __str__(self):
        return f"{self.record_number} - {self.quality_parameter.parameter_name}"
    
    def save(self, *args, **kwargs):
        param = self.quality_parameter
        if param.min_value and param.max_value:
            self.is_within_tolerance = param.min_value <= self.measured_value <= param.max_value
        super().save(*args, **kwargs)


class NonConformance(TimeStampedModel):
    """NCR (Non-Conformance Report)"""
    ncr_number = models.CharField(_("NCR#"), max_length=100, unique=True, db_index=True)
    ncr_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.CASCADE, db_index=True)
    inspection = models.ForeignKey(Inspection, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    defect_type = models.ForeignKey(DefectType, on_delete=models.PROTECT, db_index=True)
    quantity_affected = models.IntegerField(_("Qty Affected"), validators=[MinValueValidator(1)])
    severity = models.CharField(_("Severity"), max_length=20, choices=[
        ('minor', 'Minor'), ('major', 'Major'), ('critical', 'Critical')
    ], db_index=True)
    description = models.TextField(_("Description"))
    root_cause = models.TextField(_("Root Cause"), blank=True)
    immediate_action = models.TextField(_("Immediate Action"), blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('open', 'Open'), ('under_review', 'Under Review'), ('closed', 'Closed')
    ], default='open', db_index=True)
    reported_by = models.CharField(_("Reported By"), max_length=100)
    
    class Meta:
        verbose_name = "Non-Conformance"
        ordering = ['-ncr_date']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['severity', 'status']),
        ]
    
    def __str__(self):
        return f"{self.ncr_number} - {self.order.order_number}"



class CorrectiveAction(TimeStampedModel):
    """CAPA (Corrective & Preventive Action)"""
    capa_number = models.CharField(_("CAPA#"), max_length=100, unique=True, db_index=True)
    non_conformance = models.ForeignKey(NonConformance, on_delete=models.CASCADE, related_name='corrective_actions', db_index=True)
    action_type = models.CharField(_("Type"), max_length=20, choices=[
        ('corrective', 'Corrective'), ('preventive', 'Preventive')
    ], db_index=True)
    action_description = models.TextField(_("Action"))
    responsible_person = models.CharField(_("Responsible"), max_length=100, db_index=True)
    target_date = models.DateField(_("Target Date"), db_index=True)
    completion_date = models.DateField(_("Completed"), null=True, blank=True, db_index=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('planned', 'Planned'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('overdue', 'Overdue')
    ], default='planned', db_index=True)
    effectiveness_check = models.TextField(_("Effectiveness"), blank=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Corrective Action"
        ordering = ['target_date']
        indexes = [
            models.Index(fields=['non_conformance', 'status']),
            models.Index(fields=['responsible_person', 'status']),
        ]
    
    def __str__(self):
        return f"{self.capa_number} - {self.action_type}"


class QualityAudit(TimeStampedModel):
    """Internal/external audits"""
    audit_number = models.CharField(_("Audit#"), max_length=100, unique=True, db_index=True)
    audit_date = models.DateField(_("Date"), db_index=True)
    audit_type = models.CharField(_("Type"), max_length=50, choices=[
        ('internal', 'Internal'), ('external', 'External'), ('buyer', 'Buyer'), ('certification', 'Certification')
    ], db_index=True)
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE, db_index=True)
    auditor_name = models.CharField(_("Auditor"), max_length=200)
    audit_scope = models.TextField(_("Scope"))
    findings = models.TextField(_("Findings"), blank=True)
    score = models.DecimalField(_("Score"), max_digits=5, decimal_places=2, null=True, blank=True)
    result = models.CharField(_("Result"), max_length=20, choices=[
        ('pass', 'Pass'), ('conditional', 'Conditional'), ('fail', 'Fail')
    ], db_index=True)
    next_audit_date = models.DateField(_("Next Audit"), null=True, blank=True, db_index=True)
    
    class Meta:
        verbose_name = "Quality Audit"
        ordering = ['-audit_date']
        indexes = [models.Index(fields=['factory', 'audit_type'])]
    
    def __str__(self):
        return f"{self.audit_number} - {self.factory.factory_name}"



class QualityMetrics(TimeStampedModel):
    """Quality KPIs and metrics"""
    metric_date = models.DateField(_("Date"), db_index=True)
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE, db_index=True)
    total_inspected = models.IntegerField(_("Inspected"), validators=[MinValueValidator(0)])
    total_passed = models.IntegerField(_("Passed"), validators=[MinValueValidator(0)])
    total_failed = models.IntegerField(_("Failed"), validators=[MinValueValidator(0)])
    pass_rate = models.DecimalField(_("Pass Rate%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    defect_rate = models.DecimalField(_("Defect Rate%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    rework_quantity = models.IntegerField(_("Rework"), default=0, validators=[MinValueValidator(0)])
    rejection_quantity = models.IntegerField(_("Rejection"), default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        verbose_name = "Quality Metrics"
        ordering = ['-metric_date']
        unique_together = ['metric_date', 'factory']
        indexes = [models.Index(fields=['factory', 'metric_date'])]
    
    def __str__(self):
        return f"{self.factory.factory_name} - {self.metric_date}"
    
    def save(self, *args, **kwargs):
        if self.total_inspected > 0:
            self.pass_rate = (Decimal(str(self.total_passed)) / Decimal(str(self.total_inspected))) * 100
            self.defect_rate = (Decimal(str(self.total_failed)) / Decimal(str(self.total_inspected))) * 100
        super().save(*args, **kwargs)


# ==================== PHASE 9: SAMPLE MANAGEMENT ====================

class SampleType(TimeStampedModel):
    """Sample types (Proto, Fit, PP, SMS, etc.)"""
    type_name = models.CharField(_("Type"), max_length=100, unique=True, db_index=True)
    type_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    description = models.TextField(_("Description"), blank=True)
    sort_order = models.IntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Sample Type"
        ordering = ['sort_order', 'type_name']
    
    def __str__(self):
        return self.type_name



class SampleRequest(TimeStampedModel):
    """Sample request from buyer"""
    request_number = models.CharField(_("Request#"), max_length=100, unique=True, db_index=True)
    request_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT, db_index=True)
    merchandiser = models.ForeignKey(Merchandiser, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    style = models.ForeignKey(Style, on_delete=models.CASCADE, db_index=True)
    sample_type = models.ForeignKey(SampleType, on_delete=models.PROTECT, db_index=True)
    quantity = models.IntegerField(_("Qty"), validators=[MinValueValidator(1)])
    required_date = models.DateField(_("Required"), db_index=True)
    special_instructions = models.TextField(_("Instructions"), blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('in_progress', 'In Progress'), 
        ('completed', 'Completed'), ('cancelled', 'Cancelled')
    ], default='pending', db_index=True)
    
    class Meta:
        verbose_name = "Sample Request"
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['style', 'status']),
        ]
    
    def __str__(self):
        return f"{self.request_number} - {self.style.style_number}"


class SampleDevelopment(TimeStampedModel):
    """Sample development tracking"""
    development_number = models.CharField(_("Dev#"), max_length=100, unique=True, db_index=True)
    sample_request = models.ForeignKey(SampleRequest, on_delete=models.CASCADE, related_name='developments', db_index=True)
    start_date = models.DateField(_("Start"), db_index=True)
    target_completion = models.DateField(_("Target"), db_index=True)
    actual_completion = models.DateField(_("Completed"), null=True, blank=True, db_index=True)
    assigned_to = models.CharField(_("Assigned To"), max_length=100, db_index=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('not_started', 'Not Started'), ('in_progress', 'In Progress'), 
        ('completed', 'Completed'), ('on_hold', 'On Hold')
    ], default='not_started', db_index=True)
    progress_notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = "Sample Development"
        ordering = ['target_completion']
        indexes = [
            models.Index(fields=['sample_request', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f"{self.development_number}"



class SampleApproval(TimeStampedModel):
    """Approval workflow"""
    approval_number = models.CharField(_("Approval#"), max_length=100, unique=True, db_index=True)
    sample_development = models.ForeignKey(SampleDevelopment, on_delete=models.CASCADE, related_name='approvals', db_index=True)
    submission_date = models.DateField(_("Submitted"), db_index=True)
    approval_date = models.DateField(_("Approved"), null=True, blank=True, db_index=True)
    approved_by = models.CharField(_("Approved By"), max_length=100, blank=True)
    result = models.CharField(_("Result"), max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('conditional', 'Conditional')
    ], default='pending', db_index=True)
    feedback = models.TextField(_("Feedback"), blank=True)
    
    class Meta:
        verbose_name = "Sample Approval"
        ordering = ['-submission_date']
        indexes = [models.Index(fields=['sample_development', 'result'])]
    
    def __str__(self):
        return f"{self.approval_number} - {self.result}"


class SampleComment(TimeStampedModel):
    """Comments and feedback"""
    sample_development = models.ForeignKey(SampleDevelopment, on_delete=models.CASCADE, related_name='comments', db_index=True)
    comment_date = models.DateTimeField(_("Date"), default=timezone.now, db_index=True)
    commented_by = models.CharField(_("By"), max_length=100, db_index=True)
    comment_text = models.TextField(_("Comment"))
    is_internal = models.BooleanField(_("Internal"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Sample Comment"
        ordering = ['-comment_date']
        indexes = [models.Index(fields=['sample_development', 'is_internal'])]
    
    def __str__(self):
        return f"Comment by {self.commented_by}"


class SampleCost(TimeStampedModel):
    """Sample costing"""
    sample_development = models.OneToOneField(SampleDevelopment, on_delete=models.CASCADE, related_name='cost', db_index=True)
    fabric_cost = models.DecimalField(_("Fabric"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    trim_cost = models.DecimalField(_("Trim"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    labor_cost = models.DecimalField(_("Labor"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    other_cost = models.DecimalField(_("Other"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(_("Total"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = "Sample Cost"
    
    def __str__(self):
        return f"Cost - {self.sample_development.development_number}"
    
    def save(self, *args, **kwargs):
        self.total_cost = self.fabric_cost + self.trim_cost + self.labor_cost + self.other_cost
        super().save(*args, **kwargs)



# ==================== PHASE 10: FABRIC & TRIM INVENTORY ====================

class FabricStock(TimeStampedModel):
    """Fabric stock by warehouse"""
    fabric = models.ForeignKey(Fabric, on_delete=models.CASCADE, db_index=True)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, db_index=True)
    warehouse = models.CharField(_("Warehouse"), max_length=100, db_index=True)
    opening_stock = models.DecimalField(_("Opening"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    received_quantity = models.DecimalField(_("Received"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    issued_quantity = models.DecimalField(_("Issued"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    returned_quantity = models.DecimalField(_("Returned"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    current_stock = models.DecimalField(_("Current"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    unit = models.CharField(_("Unit"), max_length=20, default="KG")
    
    class Meta:
        verbose_name = "Fabric Stock"
        unique_together = ['fabric', 'color', 'warehouse']
        indexes = [
            models.Index(fields=['fabric', 'warehouse']),
            models.Index(fields=['color', 'warehouse']),
        ]
    
    def __str__(self):
        return f"{self.fabric.fabric_name} - {self.color.name}"
    
    def save(self, *args, **kwargs):
        self.current_stock = self.opening_stock + self.received_quantity - self.issued_quantity + self.returned_quantity
        super().save(*args, **kwargs)


class FabricRoll(TimeStampedModel):
    """Individual roll tracking"""
    roll_number = models.CharField(_("Roll#"), max_length=100, unique=True, db_index=True)
    fabric_receive = models.ForeignKey(FabricReceive, on_delete=models.CASCADE, related_name='rolls', db_index=True)
    roll_length = models.DecimalField(_("Length"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    roll_weight = models.DecimalField(_("Weight"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('in_stock', 'In Stock'), ('issued', 'Issued'), ('consumed', 'Consumed')
    ], default='in_stock', db_index=True)
    location = models.CharField(_("Location"), max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Fabric Roll"
        ordering = ['roll_number']
        indexes = [models.Index(fields=['fabric_receive', 'status'])]
    
    def __str__(self):
        return self.roll_number



class FabricIssue(TimeStampedModel):
    """Fabric issue to cutting"""
    issue_number = models.CharField(_("Issue#"), max_length=100, unique=True, db_index=True)
    issue_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    cutting_order = models.ForeignKey(CuttingOrder, on_delete=models.CASCADE, db_index=True)
    fabric = models.ForeignKey(Fabric, on_delete=models.PROTECT, db_index=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, db_index=True)
    issued_quantity = models.DecimalField(_("Qty"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.CharField(_("Unit"), max_length=20, default="KG")
    issued_by = models.CharField(_("Issued By"), max_length=100)
    received_by = models.CharField(_("Received By"), max_length=100)
    
    class Meta:
        verbose_name = "Fabric Issue"
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['cutting_order', 'fabric']),
            models.Index(fields=['fabric', 'color']),
        ]
    
    def __str__(self):
        return f"{self.issue_number}"


class FabricReturn(TimeStampedModel):
    """Fabric return from cutting"""
    return_number = models.CharField(_("Return#"), max_length=100, unique=True, db_index=True)
    return_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    fabric_issue = models.ForeignKey(FabricIssue, on_delete=models.CASCADE, related_name='returns', db_index=True)
    returned_quantity = models.DecimalField(_("Qty"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    return_reason = models.TextField(_("Reason"))
    returned_by = models.CharField(_("Returned By"), max_length=100)
    
    class Meta:
        verbose_name = "Fabric Return"
        ordering = ['-return_date']
        indexes = [models.Index(fields=['fabric_issue', 'return_date'])]
    
    def __str__(self):
        return f"{self.return_number}"


class TrimStock(TimeStampedModel):
    """Trim stock by warehouse"""
    trim = models.ForeignKey(Trim, on_delete=models.CASCADE, db_index=True)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    warehouse = models.CharField(_("Warehouse"), max_length=100, db_index=True)
    opening_stock = models.DecimalField(_("Opening"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    received_quantity = models.DecimalField(_("Received"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    issued_quantity = models.DecimalField(_("Issued"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    returned_quantity = models.DecimalField(_("Returned"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    current_stock = models.DecimalField(_("Current"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = "Trim Stock"
        unique_together = ['trim', 'color', 'warehouse']
        indexes = [models.Index(fields=['trim', 'warehouse'])]
    
    def __str__(self):
        return f"{self.trim.trim_name}"
    
    def save(self, *args, **kwargs):
        self.current_stock = self.opening_stock + self.received_quantity - self.issued_quantity + self.returned_quantity
        super().save(*args, **kwargs)



class TrimIssue(TimeStampedModel):
    """Trim issue to production"""
    issue_number = models.CharField(_("Issue#"), max_length=100, unique=True, db_index=True)
    issue_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.CASCADE, db_index=True)
    trim = models.ForeignKey(Trim, on_delete=models.PROTECT, db_index=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, null=True, blank=True, db_index=True)
    issued_quantity = models.DecimalField(_("Qty"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    issued_by = models.CharField(_("Issued By"), max_length=100)
    received_by = models.CharField(_("Received By"), max_length=100)
    
    class Meta:
        verbose_name = "Trim Issue"
        ordering = ['-issue_date']
        indexes = [models.Index(fields=['order', 'trim'])]
    
    def __str__(self):
        return f"{self.issue_number}"


class TrimReturn(TimeStampedModel):
    """Trim return from production"""
    return_number = models.CharField(_("Return#"), max_length=100, unique=True, db_index=True)
    return_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    trim_issue = models.ForeignKey(TrimIssue, on_delete=models.CASCADE, related_name='returns', db_index=True)
    returned_quantity = models.DecimalField(_("Qty"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    return_reason = models.TextField(_("Reason"))
    returned_by = models.CharField(_("Returned By"), max_length=100)
    
    class Meta:
        verbose_name = "Trim Return"
        ordering = ['-return_date']
        indexes = [models.Index(fields=['trim_issue', 'return_date'])]
    
    def __str__(self):
        return f"{self.return_number}"


class MaterialRequisition(TimeStampedModel):
    """Material requisition system"""
    requisition_number = models.CharField(_("Req#"), max_length=100, unique=True, db_index=True)
    requisition_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.CASCADE, db_index=True)
    requisition_type = models.CharField(_("Type"), max_length=20, choices=[
        ('fabric', 'Fabric'), ('trim', 'Trim'), ('both', 'Both')
    ], db_index=True)
    required_date = models.DateField(_("Required"), db_index=True)
    requested_by = models.CharField(_("Requested By"), max_length=100, db_index=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('pending', 'Pending'), ('approved', 'Approved'), ('issued', 'Issued'), ('rejected', 'Rejected')
    ], default='pending', db_index=True)
    approved_by = models.CharField(_("Approved By"), max_length=100, blank=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Material Requisition"
        ordering = ['-requisition_date']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['requisition_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.requisition_number}"


# ==================== PHASE 11: SUBCONTRACTING MANAGEMENT ====================

class Subcontractor(TimeStampedModel):
    """Subcontractor master"""
    subcontractor_name = models.CharField(_("Name"), max_length=200, db_index=True)
    subcontractor_code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
    contact_person = models.CharField(_("Contact"), max_length=100)
    phone = models.CharField(_("Phone"), max_length=20)
    email = models.EmailField(_("Email"), blank=True)
    address = models.TextField(_("Address"))
    specialization = models.CharField(_("Specialization"), max_length=200, blank=True)
    capacity_per_month = models.IntegerField(_("Capacity/Month"), default=0)
    payment_terms = models.CharField(_("Payment Terms"), max_length=100, blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    
    class Meta:
        verbose_name = "Subcontractor"
        ordering = ['subcontractor_name']
    
    def __str__(self):
        return self.subcontractor_name


class SubcontractOrder(TimeStampedModel):
    """Orders to subcontractors"""
    subcontract_number = models.CharField(_("SC#"), max_length=100, unique=True, db_index=True)
    subcontract_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    subcontractor = models.ForeignKey(Subcontractor, on_delete=models.PROTECT, db_index=True)
    order = models.ForeignKey(BuyerOrder, on_delete=models.CASCADE, db_index=True)
    operation_type = models.CharField(_("Operation"), max_length=100, db_index=True)
    quantity = models.IntegerField(_("Qty"), validators=[MinValueValidator(1)])
    rate_per_piece = models.DecimalField(_("Rate/Pc"), max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(_("Total"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    delivery_date = models.DateField(_("Delivery"), db_index=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')
    ], default='pending', db_index=True)
    
    class Meta:
        verbose_name = "Subcontract Order"
        ordering = ['-subcontract_date']
        indexes = [models.Index(fields=['subcontractor', 'status'])]
    
    def __str__(self):
        return f"{self.subcontract_number}"
    
    def save(self, *args, **kwargs):
        self.total_amount = Decimal(str(self.quantity)) * self.rate_per_piece
        super().save(*args, **kwargs)


class SubcontractDelivery(TimeStampedModel):
    """Delivery from subcontractor"""
    delivery_number = models.CharField(_("Delivery#"), max_length=100, unique=True, db_index=True)
    delivery_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    subcontract_order = models.ForeignKey(SubcontractOrder, on_delete=models.CASCADE, related_name='deliveries', db_index=True)
    delivered_quantity = models.IntegerField(_("Qty"), validators=[MinValueValidator(1)])
    accepted_quantity = models.IntegerField(_("Accepted"), validators=[MinValueValidator(0)])
    rejected_quantity = models.IntegerField(_("Rejected"), default=0, validators=[MinValueValidator(0)])
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True)
    received_by = models.CharField(_("Received By"), max_length=100)
    
    class Meta:
        verbose_name = "Subcontract Delivery"
        ordering = ['-delivery_date']
        indexes = [models.Index(fields=['subcontract_order', 'delivery_date'])]
    
    def __str__(self):
        return f"{self.delivery_number}"


class SubcontractPayment(TimeStampedModel):
    """Payment to subcontractor"""
    payment_number = models.CharField(_("Payment#"), max_length=100, unique=True, db_index=True)
    payment_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    subcontractor = models.ForeignKey(Subcontractor, on_delete=models.PROTECT, db_index=True)
    subcontract_order = models.ForeignKey(SubcontractOrder, on_delete=models.CASCADE, db_index=True)
    payment_amount = models.DecimalField(_("Amount"), max_digits=12, decimal_places=2)
    payment_method = models.CharField(_("Method"), max_length=50, db_index=True)
    reference_number = models.CharField(_("Reference"), max_length=100, blank=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Subcontract Payment"
        ordering = ['-payment_date']
        indexes = [models.Index(fields=['subcontractor', 'payment_date'])]
    
    def __str__(self):
        return f"{self.payment_number}"


class SubcontractQuality(TimeStampedModel):
    """Quality tracking"""
    subcontract_delivery = models.ForeignKey(SubcontractDelivery, on_delete=models.CASCADE, related_name='quality_checks', db_index=True)
    check_date = models.DateField(_("Date"), default=timezone.now, db_index=True)
    checked_quantity = models.IntegerField(_("Checked"), validators=[MinValueValidator(1)])
    defect_quantity = models.IntegerField(_("Defects"), default=0, validators=[MinValueValidator(0)])
    defect_rate = models.DecimalField(_("Defect%"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    quality_rating = models.CharField(_("Rating"), max_length=20, choices=[
        ('excellent', 'Excellent'), ('good', 'Good'), ('average', 'Average'), ('poor', 'Poor')
    ], db_index=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = "Subcontract Quality"
        ordering = ['-check_date']
    
    def __str__(self):
        return f"Quality - {self.subcontract_delivery.delivery_number}"
    
    def save(self, *args, **kwargs):
        if self.checked_quantity > 0:
            self.defect_rate = (Decimal(str(self.defect_quantity)) / Decimal(str(self.checked_quantity))) * 100
        super().save(*args, **kwargs)

# Note: Phase 12 (HR & Payroll), Phase 13 (Document Management), and Phase 14 (Analytics & Reporting)
# are intentionally skipped as they are better handled by:
# - Phase 12: Integrated with existing HRM app
# - Phase 13: Can use Django's FileField or external DMS
# - Phase 14: Can use Django admin actions and external BI tools

# Total Models Added:
# Phase 1-4: 44 models (Foundation, TNA, Compliance, Advanced)
# Phase 6: 8 models (Costing & Pricing)
# Phase 7: 7 models (Capacity Planning)
# Phase 8: 9 models (Quality Management)
# Phase 9: 6 models (Sample Management)
# Phase 10: 8 models (Fabric & Trim Inventory)
# Phase 11: 5 models (Subcontracting)
# TOTAL: 87 PRODUCTION-READY MODELS FOR GARMENTS ERP
