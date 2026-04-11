from django.db import models
"""
ERP Admin Configuration with Unfold and Inline Formsets
"""
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import (
    Company, Category, Product, Customer, Supplier, SalesPerson, Warehouse,
    Size, Color, ProductVariant, ProductVariantWarehouseStock,
    SalesQuotation, SalesQuotationItem,
    SalesOrder, SalesOrderItem,
    Invoice, InvoiceItem,
    SalesReturn, SalesReturnItem,
    Delivery, DeliveryItem,
    PurchaseQuotation, PurchaseQuotationItem,
    PurchaseOrder, PurchaseOrderItem,
    GoodsReceipt, GoodsReceiptItem,
    GoodsReceiptPO, GoodsReceiptPOItem,
    GoodsIssue, GoodsIssueItem,
    PurchaseInvoice, PurchaseInvoiceItem,
    PurchaseReturn, PurchaseReturnItem,
    BillOfMaterials, BOMComponent,
    ProductionOrder, ProductionOrderComponent,
    ProductionReceipt, ProductionReceiptItem,
    ProductionIssue, ProductionIssueItem,
    InventoryTransfer, InventoryTransferItem,
    ProductWarehouseStock, StockTransaction,
    BankAccount, IncomingPayment, IncomingPaymentInvoice,
    OutgoingPayment, OutgoingPaymentInvoice,
    AccountType, ChartOfAccounts, CostCenter, Project,
    JournalEntry, JournalEntryLine, FiscalYear, Budget,
    # New MUST HAVE models
    Currency, ExchangeRate, TaxType, TaxRate,
    PaymentTerm, UnitOfMeasure, UOMConversion,
    PriceList, PriceListItem,
    # Discount, Stock Adjustment, Approval, Notification models
    DiscountType, DiscountRule,
    StockAdjustment, StockAdjustmentItem,
    ApprovalWorkflow, ApprovalLevel, ApprovalRequest, ApprovalHistory,
    NotificationType, NotificationSetting, Notification, AlertRule,
    # Quality Control & Service Management
    QualityCheckType, QualityCheck, DefectType, QualityDefect,
    ServiceType, ServiceRequest, ComplaintType, Complaint,
    # Fixed Assets Management
    AssetCategory, FixedAsset, AssetDepreciation, AssetTransfer, AssetDisposal, AssetMaintenance,
    # Bank Reconciliation
    BankStatement, BankReconciliation, UnreconciledTransaction,
)
from .utils import (
    copy_sales_quotation_to_order,
    copy_sales_order_to_delivery, copy_sales_order_to_invoice, copy_sales_order_to_return,
    copy_purchase_quotation_to_order,
    copy_purchase_order_to_receipt, copy_purchase_order_to_invoice, copy_purchase_order_to_return
)

# ==================== BASE ADMIN WITH BRANCH FILTERING ====================

class BranchFilteredAdmin(ModelAdmin):
    """Base admin class that filters data by user's assigned branch"""
    
    def get_queryset(self, request):
        """Filter queryset based on user's branch access"""
        qs = super().get_queryset(request)
        
        # Superuser can see everything
        if request.user.is_superuser:
            return qs
        
        try:
            profile = request.user.profile
            if profile.can_access_all_branches:
                return qs
            elif profile.branch:
                # Filter by user's branch - check both 'branch' and 'warehouse' fields
                if hasattr(qs.model, 'branch'):
                    return qs.filter(branch=profile.branch)
                elif hasattr(qs.model, 'warehouse'):
                    return qs.filter(warehouse=profile.branch)
                elif hasattr(qs.model, 'from_warehouse'):
                    # For InventoryTransfer - filter by either from or to warehouse
                    return qs.filter(
                        models.Q(from_warehouse=profile.branch) | 
                        models.Q(to_warehouse=profile.branch)
                    )
                else:
                    return qs
            else:
                # No branch assigned - return empty queryset
                return qs.none()
        except UserProfile.DoesNotExist:
            # No profile - return empty queryset
            return qs.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit branch/warehouse choices to user's accessible branches"""
        # Skip filtering for autocomplete fields to allow proper search functionality
        autocomplete_fields = getattr(self, 'autocomplete_fields', [])
        
        if db_field.name in ['branch', 'warehouse', 'from_warehouse', 'to_warehouse'] and db_field.name not in autocomplete_fields:
            try:
                profile = request.user.profile
                if not request.user.is_superuser and not profile.can_access_all_branches:
                    accessible_branches = profile.get_accessible_branches()
                    kwargs["queryset"] = accessible_branches
            except UserProfile.DoesNotExist:
                kwargs["queryset"] = Warehouse.objects.none()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """Auto-set branch/warehouse from user profile if not set"""
        if not change:  # Only for new objects
            try:
                profile = request.user.profile
                if profile.branch:
                    # Set branch field if exists and not set
                    if hasattr(obj, 'branch') and not obj.branch:
                        obj.branch = profile.branch
                    # Set warehouse field if exists and not set
                    elif hasattr(obj, 'warehouse') and not obj.warehouse:
                        obj.warehouse = profile.branch
                    # For InventoryTransfer, set from_warehouse if not set
                    elif hasattr(obj, 'from_warehouse') and not obj.from_warehouse:
                        obj.from_warehouse = profile.branch
            except UserProfile.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)

class SalesQuotationItemInline(TabularInline):
    model = SalesQuotationItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total']
    readonly_fields = ['line_total']
    # Use autocomplete for product search
    autocomplete_fields = ['product']
    


class SalesOrderItemInline(TabularInline):
    model = SalesOrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total', 'delivered_qty', 'invoiced_qty', 'returned_qty']
    readonly_fields = ['line_total', 'delivered_qty', 'invoiced_qty', 'returned_qty']
    # Use autocomplete for product search
    autocomplete_fields = ['product']
    
    @display(description=_('Delivered'))
    def delivered_qty(self, obj):
        if obj.pk:
            remaining = obj.remaining_to_deliver
            return f"{obj.delivered_quantity} / {remaining} left"
        return "-"
    
    @display(description=_('Invoiced'))
    def invoiced_qty(self, obj):
        if obj.pk:
            remaining = obj.remaining_to_invoice
            return f"{obj.invoiced_quantity} / {remaining} left"
        return "-"
    
    @display(description=_('Returned'))
    def returned_qty(self, obj):
        if obj.pk:
            return f"{obj.returned_quantity}"
        return "-"
    


class InvoiceItemInline(TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total', 'available_qty']
    readonly_fields = ['unit_price', 'line_total', 'available_qty']
    autocomplete_fields = ['product']
    
    @display(description=_('Available'))
    def available_qty(self, obj):
        if obj.pk:
            return f"{obj.available_quantity} left"
        return "-"
    


class SalesReturnItemInline(TabularInline):
    model = SalesReturnItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total', 'available_qty']
    readonly_fields = ['unit_price', 'line_total', 'available_qty']
    autocomplete_fields = ['product']
    
    @display(description=_('Available'))
    def available_qty(self, obj):
        if obj.pk:
            return f"{obj.available_quantity} left"
        return "-"
    


class PurchaseQuotationItemInline(TabularInline):
    model = PurchaseQuotationItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total']
    readonly_fields = ['line_total']
    autocomplete_fields = ['product']
    


class PurchaseOrderItemInline(TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total', 'received_qty', 'returned_qty']
    readonly_fields = ['line_total', 'received_qty', 'returned_qty']
    autocomplete_fields = ['product']
    
    @display(description=_('Received'))
    def received_qty(self, obj):
        if obj.pk:
            remaining = obj.remaining_to_receive
            return f"{obj.received_quantity} / {remaining} left"
        return "-"
    
    @display(description=_('Returned'))
    def returned_qty(self, obj):
        if obj.pk:
            return f"{obj.returned_quantity}"
        return "-"
    


class GoodsReceiptItemInline(TabularInline):
    model = GoodsReceiptItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total', 'available_qty']
    readonly_fields = ['unit_price', 'line_total', 'available_qty']
    autocomplete_fields = ['product']
    
    @display(description=_('Available'))
    def available_qty(self, obj):
        if obj.pk:
            return f"{obj.available_quantity} left"
        return "-"
    


class GoodsIssueItemInline(TabularInline):
    model = GoodsIssueItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total', 'available_stock']
    readonly_fields = ['unit_price', 'line_total', 'available_stock']
    autocomplete_fields = ['product']
    
    @display(description=_('Stock'))
    def available_stock(self, obj):
        if obj.pk:
            return f"{obj.available_stock} in stock"
        return "-"
    


class InventoryTransferItemInline(TabularInline):
    model = InventoryTransferItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total', 'available_stock']
    readonly_fields = ['unit_price', 'line_total', 'available_stock']
    autocomplete_fields = ['product']
    
    @display(description=_('Available'))
    def available_stock(self, obj):
        if obj.pk:
            return f"{obj.available_stock} in source"
        return "-"
    


class BOMComponentInline(TabularInline):
    model = BOMComponent
    extra = 1
    fields = ['product', 'quantity', 'unit_cost', 'scrap_percentage', 'line_total']
    readonly_fields = ['unit_cost', 'line_total']
    autocomplete_fields = ['product']
    


class ProductionOrderComponentInline(TabularInline):
    model = ProductionOrderComponent
    extra = 1
    fields = ['product', 'quantity_required', 'quantity_consumed', 'unit_cost', 'line_total', 'remaining']
    readonly_fields = ['unit_cost', 'line_total', 'remaining']
    autocomplete_fields = ['product']
    
    @display(description=_('Remaining'))
    def remaining(self, obj):
        if obj.pk:
            return f"{obj.remaining_to_consume} left"
        return "-"
    


class ProductionReceiptItemInline(TabularInline):
    model = ProductionReceiptItem
    extra = 0
    fields = ['product', 'planned_quantity', 'received_quantity', 'rejected_quantity', 'unit_cost', 'line_total']
    readonly_fields = ['line_total']
    autocomplete_fields = ['product']


class PurchaseInvoiceItemInline(TabularInline):
    model = PurchaseInvoiceItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total', 'available_qty']
    readonly_fields = ['unit_price', 'line_total', 'available_qty']
    autocomplete_fields = ['product']
    
    @display(description=_('Available'))
    def available_qty(self, obj):
        if obj.pk:
            return f"{obj.available_quantity} left"
        return "-"
    


class PurchaseReturnItemInline(TabularInline):
    model = PurchaseReturnItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total', 'available_qty']
    readonly_fields = ['unit_price', 'line_total', 'available_qty']
    autocomplete_fields = ['product']
    
    @display(description=_('Available'))
    def available_qty(self, obj):
        if obj.pk:
            return f"{obj.available_quantity} left"
        return "-"
    


class DeliveryItemInline(TabularInline):
    model = DeliveryItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'line_total', 'available_qty']
    readonly_fields = ['unit_price', 'line_total', 'available_qty']
    autocomplete_fields = ['product']
    
    @display(description=_('Available'))
    def available_qty(self, obj):
        if obj.pk:
            return f"{obj.available_quantity} left"
        return "-"
    


# ==================== MAIN ADMINS ====================

@admin.register(Warehouse)
class WarehouseAdmin(ModelAdmin):
    list_display = ['name', 'code', 'city', 'country', 'manager', 'is_active']
    list_filter = ['is_active', 'city', 'country']
    search_fields = ['name', 'code', 'city', 'manager']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Warehouse Information'), {
            'fields': (
                ('name', 'code'),
            ),
            'classes': ['tab'],
            'description': _('Warehouse identification'),
        }),
        (_('Location'), {
            'fields': (
                ('address',),
                ('city', 'country', 'phone'),
            ),
            'classes': ['tab'],
            'description': _('Warehouse location and contact'),
        }),
        (_('Management'), {
            'fields': (
                ('manager',),
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Warehouse manager information'),
        }),
    )


@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    list_display = ['name', 'city', 'country', 'phone', 'email']
    search_fields = ['name', 'city', 'email']
    
    fieldsets = (
        (_('Company Information'), {
            'fields': (
                ('name',),
                ('logo',),
            ),
            'classes': ['tab'],
            'description': _('Company identification and branding'),
        }),
        (_('Contact Details'), {
            'fields': (
                ('phone', 'email'),
                ('website',),
            ),
            'classes': ['tab'],
            'description': _('Company contact information'),
        }),
        (_('Address'), {
            'fields': (
                ('address',),
                ('city', 'country'),
            ),
            'classes': ['tab'],
            'description': _('Company location details'),
        }),
        (_('Tax & Legal'), {
            'fields': (
                ('tax_number',),
            ),
            'classes': ['tab'],
            'description': _('Tax and legal information'),
        }),
    )


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name',),
            ),
            'classes': ['tab'],
            'description': _('Category name'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Category status'),
        }),
    )


# ==================== PRODUCT VARIANT INLINE ====================
class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['size', 'color', 'sku', 'barcode', 'purchase_price', 'selling_price', 'display_stock', 'is_active']
    readonly_fields = ['sku', 'display_stock']
    # autocomplete_fields removed - Size and Color admins not registered
    
    @display(description=_('Stock'))
    def display_stock(self, obj):
        if obj.pk:
            return f"{obj.current_stock}"
        return "-"


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name', 'sku', 'category', 'default_warehouse', 'display_stock', 'stock_status', 'purchase_price', 'selling_price', 'default_bom', 'is_active']
    list_filter = ['category', 'default_warehouse', 'is_active']
    search_fields = ['name', 'sku', 'description', 'category__name']
    list_editable = ['is_active']
    change_form_template = 'admin/erp/product/change_form.html'
    inlines = [ProductVariantInline]
    # Enable autocomplete for Product model
    autocomplete_fields = ['category', 'default_warehouse']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for ForeignKey fields"""
        qs = super().get_queryset(request)
        return qs.select_related('category', 'default_warehouse', 'default_bom')
    
    fieldsets = (
        (_('Required Information'), {
            'fields': (
                ('name', 'sku'),
                ('category', 'unit'),
                ('purchase_price', 'selling_price'),
            ),
            'classes': ['tab'],
            'description': _('Required product information'),
        }),
        (_('Warehouse & Stock'), {
            'fields': (
                ('default_warehouse', 'min_stock_level'),
            ),
            'classes': ['tab'],
            'description': _('Warehouse and stock settings. Actual stock is managed via transactions.'),
        }),
        (_('Bill of Materials'), {
            'fields': (
                ('default_bom',),
            ),
            'classes': ['tab'],
            'description': _('Default BOM for Quick Sale. When sold, BOM components will be deducted from stock instead of this product.'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('description',),
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Optional product details'),
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter default_bom to show only BOMs for this product"""
        if db_field.name == "default_bom":
            # Get product ID from URL
            object_id = request.resolver_match.kwargs.get('object_id')
            if object_id:
                kwargs["queryset"] = BillOfMaterials.objects.filter(product_id=object_id, status='active')
            else:
                # New product - no BOMs available yet
                kwargs["queryset"] = BillOfMaterials.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add warehouse stock data to change form context"""
        extra_context = extra_context or {}
        
        try:
            product = Product.objects.get(pk=object_id)
            warehouse_stocks = ProductWarehouseStock.objects.filter(product=product).select_related('warehouse')
            
            total_stock = sum(stock.quantity for stock in warehouse_stocks)
            total_value = sum(stock.quantity * product.purchase_price for stock in warehouse_stocks)
            max_stock = max((stock.quantity for stock in warehouse_stocks), default=1) or 1
            
            stocks_data = []
            for stock in warehouse_stocks:
                percentage = (float(stock.quantity) / float(max_stock) * 100) if max_stock > 0 else 0
                stocks_data.append({
                    'warehouse': stock.warehouse,
                    'quantity': stock.quantity,
                    'value': stock.quantity * product.purchase_price,
                    'percentage': min(percentage, 100),
                })
            
            extra_context['warehouse_stock_data'] = {
                'stocks': stocks_data,
                'total_stock': total_stock,
                'total_value': total_value,
            }
        except Product.DoesNotExist:
            extra_context['warehouse_stock_data'] = {
                'stocks': [],
                'total_stock': 0,
                'total_value': 0,
            }
        
        return super().change_view(request, object_id, form_url, extra_context)
    
    @display(description=_('Total Stock'))
    def display_stock(self, obj):
        """Display total stock from all warehouses"""
        return f"{obj.current_stock} {obj.unit}"
    
    @display(description=_('Stock Status'))
    def stock_status(self, obj):
        if obj.current_stock <= obj.min_stock_level:
            return format_html('<span style="color: red;">{}</span>', '⚠ Low Stock')
        return format_html('<span style="color: green;">{}</span>', '✓ In Stock')


# ==================== PRODUCT VARIANT WAREHOUSE STOCK ADMIN ====================
@admin.register(ProductVariantWarehouseStock)
class ProductVariantWarehouseStockAdmin(ModelAdmin):
    list_display = ['variant', 'warehouse', 'quantity', 'last_updated']
    list_filter = ['warehouse', 'variant__product__category', 'variant__size', 'variant__color']
    search_fields = ['variant__product__name', 'variant__sku', 'warehouse__name']
    # autocomplete_fields removed - ProductVariant admin not registered
    raw_id_fields = ['variant', 'warehouse']  # Use raw_id instead
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Stock Information'), {
            'fields': (
                ('variant', 'warehouse'),
                ('quantity',),
            ),
        }),
        (_('Timestamps'), {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['collapse'],
        }),
    )
    
    @display(description=_('Last Updated'))
    def last_updated(self, obj):
        return obj.updated_at.strftime('%Y-%m-%d %H:%M')


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ['name', 'email', 'phone', 'city', 'country', 'credit_limit', 'is_active']
    list_filter = ['is_active', 'city', 'country']
    search_fields = ['name', 'email', 'phone']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name',),
                ('email', 'phone'),
            ),
            'classes': ['tab'],
            'description': _('Customer contact information'),
        }),
        (_('Address Details'), {
            'fields': (
                ('address',),
                ('city', 'country'),
            ),
            'classes': ['tab'],
            'description': _('Customer address information'),
        }),
        (_('Business Details'), {
            'fields': (
                ('tax_number',),
                ('credit_limit',),
            ),
            'classes': ['tab'],
            'description': _('Business and financial information'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Customer status'),
        }),
    )


@admin.register(Supplier)
class SupplierAdmin(ModelAdmin):
    list_display = ['name', 'email', 'phone', 'city', 'country', 'is_active']
    list_filter = ['is_active', 'city', 'country']
    search_fields = ['name', 'email', 'phone']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name',),
                ('email', 'phone'),
            ),
            'classes': ['tab'],
            'description': _('Supplier contact information'),
        }),
        (_('Address Details'), {
            'fields': (
                ('address',),
                ('city', 'country'),
            ),
            'classes': ['tab'],
            'description': _('Supplier address information'),
        }),
        (_('Business Details'), {
            'fields': (
                ('tax_number',),
            ),
            'classes': ['tab'],
            'description': _('Business and tax information'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Supplier status'),
        }),
    )


@admin.register(SalesPerson)
class SalesPersonAdmin(ModelAdmin):
    list_display = ['name', 'email', 'phone', 'employee_id', 'commission_rate', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'email', 'phone', 'employee_id']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'employee_id'),
                ('email', 'phone'),
            ),
            'classes': ['tab'],
            'description': _('Sales person contact information'),
        }),
        (_('Commission Details'), {
            'fields': (
                ('commission_rate',),
            ),
            'classes': ['tab'],
            'description': _('Commission rate configuration'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Sales person status'),
        }),
    )


# ==================== SALES MODULE ====================

@admin.register(SalesQuotation)
class SalesQuotationAdmin(BranchFilteredAdmin):
    list_display = ['quotation_number', 'branch', 'quotation_date', 'valid_until', 'customer', 'salesperson', 'status', 'total_amount', 'action_buttons', 'created_at']
    list_filter = ['status', 'quotation_date', 'salesperson', 'branch']
    search_fields = ['quotation_number', 'customer__name', 'salesperson__name']
    autocomplete_fields = ['customer', 'salesperson']
    readonly_fields = ['quotation_number', 'subtotal', 'total_amount']
    inlines = [SalesQuotationItemInline]
    actions = ['create_sales_order_action']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'salesperson').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('quotation_number', 'quotation_date', 'valid_until'),
                ('customer', 'salesperson'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required quotation information'),
        }),
        (_('Financial Details'), {
            'fields': (
                ('subtotal', 'discount_amount'),
                ('tax_rate', 'tax_amount', 'total_amount'),
            ),
            'classes': ['tab'],
            'description': _('Financial calculations'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('job_reference', 'shipping_method', 'delivery_terms'),
                ('payment_terms',),
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional quotation details'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_totals()
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-sales-quotation', args=[obj.id])
        order_url = reverse('erp:copy-sales-quotation-to-order', args=[obj.id])
        
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px; margin-right: 3px;">🖨️ Print</a>'
            '<a href="{}" style="background: #10B981; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">📋 Create Order</a>',
            print_url, order_url
        )
    
    @admin.action(description=_('Create Sales Order from selected'))
    def create_sales_order_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Please select exactly one sales quotation.'), level='warning')
            return
        
        sales_quotation = queryset.first()
        sales_order, error = copy_sales_quotation_to_order(sales_quotation.id)
        
        if sales_order:
            url = reverse('admin:erp_salesorder_change', args=[sales_order.id])
            self.message_user(
                request,
                format_html('Sales Order <a href="{}">{}</a> created successfully!', url, sales_order.order_number),
                level='success'
            )
        else:
            self.message_user(request, f'Error: {error}', level='error')


@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(ModelAdmin):
    list_display = ['sales_order', 'product', 'quantity', 'unit_price', 'line_total']
    list_filter = ['sales_order']
    search_fields = ['sales_order__order_number', 'product__name', 'product__sku']
    
    def has_module_permission(self, request):
        # Hide from admin index
        return False


@admin.register(SalesOrder)
class SalesOrderAdmin(BranchFilteredAdmin):
    list_display = ['order_number', 'order_date', 'customer', 'salesperson', 'branch', 'status', 'total_amount', 'action_buttons', 'created_at']
    list_filter = ['status', 'order_date', 'salesperson', 'branch']
    search_fields = ['order_number', 'customer__name', 'salesperson__name']
    readonly_fields = ['order_number', 'subtotal', 'total_amount']
    inlines = [SalesOrderItemInline]
    actions = ['create_delivery_action', 'create_invoice_action', 'create_return_action']
    autocomplete_fields = ['customer', 'salesperson', 'sales_quotation']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'salesperson', 'sales_quotation').prefetch_related('items__product')
    
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('order_number', 'order_date'),
                ('sales_quotation',),
                ('customer', 'salesperson'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required order information'),
        }),
        (_('Financial Details'), {
            'fields': (
                ('subtotal', 'discount_amount'),
                ('tax_rate', 'tax_amount', 'total_amount'),
            ),
            'classes': ['tab'],
            'description': _('Financial calculations'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('job_reference', 'shipping_method', 'delivery_terms'),
                ('delivery_date', 'payment_terms', 'due_date'),
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional order details'),
        }),
    )
    
    def save_formset(self, request, form, formset, change):
        """Validate inline items before saving"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.full_clean()  # This will call the clean() method
            instance.save()
        formset.save_m2m()
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-sales-order', args=[obj.id])
        delivery_url = reverse('erp:copy-sales-order-to-delivery', args=[obj.id])
        invoice_url = reverse('erp:copy-sales-order-to-invoice', args=[obj.id])
        return_url = reverse('erp:copy-sales-order-to-return', args=[obj.id])
        
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px; margin-right: 3px;">🖨️ Print</a>'
            '<a href="{}" style="background: #10B981; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px; margin-right: 3px;">📦 Delivery</a>'
            '<a href="{}" style="background: #F59E0B; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px; margin-right: 3px;">📄 Invoice</a>'
            '<a href="{}" style="background: #EF4444; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">↩️ Return</a>',
            print_url, delivery_url, invoice_url, return_url
        )
    
    @admin.action(description=_('Create Delivery from selected'))
    def create_delivery_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Please select exactly one sales order.'), level='warning')
            return
        
        sales_order = queryset.first()
        delivery, error = copy_sales_order_to_delivery(sales_order.id)
        
        if delivery:
            url = reverse('admin:erp_delivery_change', args=[delivery.id])
            self.message_user(
                request,
                format_html('Delivery <a href="{}">{}</a> created successfully!', url, delivery.delivery_number),
                level='success'
            )
        else:
            self.message_user(request, f'Error: {error}', level='error')
    
    @admin.action(description=_('Create Invoice from selected'))
    def create_invoice_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Please select exactly one sales order.'), level='warning')
            return
        
        sales_order = queryset.first()
        invoice, error = copy_sales_order_to_invoice(sales_order.id)
        
        if invoice:
            url = reverse('admin:erp_invoice_change', args=[invoice.id])
            self.message_user(
                request,
                format_html('Invoice <a href="{}">{}</a> created successfully!', url, invoice.invoice_number),
                level='success'
            )
        else:
            self.message_user(request, f'Error: {error}', level='error')
    
    @admin.action(description=_('Create Return from selected'))
    def create_return_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Please select exactly one sales order.'), level='warning')
            return
        
        sales_order = queryset.first()
        sales_return, error = copy_sales_order_to_return(sales_order.id)
        
        if sales_return:
            url = reverse('admin:erp_salesreturn_change', args=[sales_return.id])
            self.message_user(
                request,
                format_html('Return <a href="{}">{}</a> created successfully!', url, sales_return.return_number),
                level='success'
            )
        else:
            self.message_user(request, f'Error: {error}', level='error')
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_totals()


@admin.register(Invoice)
class InvoiceAdmin(BranchFilteredAdmin):
    list_display = ['invoice_number', 'invoice_date', 'sales_order', 'customer', 'salesperson', 'branch', 'status', 'total_amount', 'paid_amount', 'due_amount', 'action_buttons']
    list_filter = ['status', 'invoice_date', 'salesperson', 'branch']
    search_fields = ['invoice_number', 'customer__name', 'salesperson__name', 'sales_order__order_number']
    readonly_fields = ['invoice_number', 'subtotal', 'total_amount', 'due_amount']
    inlines = [InvoiceItemInline]
    autocomplete_fields = ['sales_order', 'customer', 'salesperson']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'salesperson', 'sales_order').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('invoice_number', 'invoice_date', 'due_date'),
                ('sales_order',),
                ('customer', 'salesperson'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required invoice information'),
        }),
        (_('Financial Details'), {
            'fields': (
                ('subtotal', 'discount_amount', 'tax_amount'),
                ('total_amount', 'paid_amount', 'due_amount'),
            ),
            'classes': ['tab'],
            'description': _('Financial calculations and payments'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional invoice details'),
        }),
    )
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-invoice', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🖨️ Print</a>',
            print_url
        )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_totals()


@admin.register(SalesReturn)
class SalesReturnAdmin(BranchFilteredAdmin):
    list_display = ['return_number', 'warehouse', 'return_date', 'sales_order', 'customer', 'salesperson', 'status', 'total_amount', 'refund_amount', 'action_buttons']
    list_filter = ['status', 'return_date', 'salesperson', 'warehouse']
    search_fields = ['return_number', 'customer__name', 'salesperson__name', 'sales_order__order_number']
    readonly_fields = ['return_number', 'subtotal', 'total_amount']
    inlines = [SalesReturnItemInline]
    autocomplete_fields = ['sales_order', 'customer', 'salesperson', 'warehouse']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'salesperson', 'sales_order', 'invoice', 'warehouse').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('return_number', 'return_date'),
                ('sales_order',),
                ('customer', 'salesperson'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required return information'),
        }),
        (_('Financial Details'), {
            'fields': (
                ('subtotal', 'total_amount', 'refund_amount'),
            ),
            'classes': ['tab'],
            'description': _('Financial calculations and refunds'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('invoice',),
                ('reason',),
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional return details'),
        }),
    )
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-sales-return', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🖨️ Print</a>',
            print_url
        )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_totals()
    
    def save_formset(self, request, form, formset, change):
        """Validate inline items before saving"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.full_clean()
            instance.save()
        formset.save_m2m()
    


@admin.register(Delivery)
class DeliveryAdmin(BranchFilteredAdmin):
    list_display = ['delivery_number', 'warehouse', 'delivery_date', 'sales_order', 'customer', 'salesperson', 'status', 'action_buttons']
    list_filter = ['status', 'delivery_date', 'salesperson', 'warehouse']
    search_fields = ['delivery_number', 'customer__name', 'salesperson__name', 'sales_order__order_number']
    readonly_fields = ['delivery_number']
    inlines = [DeliveryItemInline]
    autocomplete_fields = ['sales_order', 'customer', 'salesperson', 'warehouse']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'salesperson', 'sales_order', 'warehouse').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('delivery_number', 'delivery_date'),
                ('sales_order',),
                ('customer', 'salesperson'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required delivery information'),
        }),
        (_('Shipping Details'), {
            'fields': (
                ('tracking_number', 'carrier'),
                ('shipping_cost',),
                ('delivery_address',),
            ),
            'classes': ['tab'],
            'description': _('Shipping and tracking information'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional delivery details'),
        }),
    )
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-delivery', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🖨️ Print</a>',
            print_url
        )
    
    def save_formset(self, request, form, formset, change):
        """Validate inline items before saving"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.full_clean()
            instance.save()
        formset.save_m2m()
    


# ==================== PURCHASE MODULE ====================

@admin.register(PurchaseQuotation)
class PurchaseQuotationAdmin(BranchFilteredAdmin):
    list_display = ['quotation_number', 'branch', 'quotation_date', 'valid_until', 'supplier', 'status', 'total_amount', 'action_buttons']
    list_filter = ['status', 'quotation_date', 'branch']
    search_fields = ['quotation_number', 'supplier__name']
    readonly_fields = ['quotation_number', 'subtotal', 'total_amount']
    inlines = [PurchaseQuotationItemInline]
    actions = ['create_purchase_order_action']
    autocomplete_fields = ['supplier']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('supplier').prefetch_related('items__product')
    
    fieldsets = (
        (_('Quotation Information'), {
            'fields': (
                ('quotation_number', 'quotation_date', 'valid_until'),
                ('supplier', 'status'),
            ),
            'classes': ['tab'],
        }),
        (_('Financial Details'), {
            'fields': (
                ('subtotal', 'discount_amount', 'tax_amount'),
                ('total_amount',),
                ('notes',),
            ),
            'classes': ['tab'],
        }),
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_totals()
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-purchase-quotation', args=[obj.id])
        order_url = reverse('erp:copy-purchase-quotation-to-order', args=[obj.id])
        
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px; margin-right: 3px;">🖨️ Print</a>'
            '<a href="{}" style="background: #10B981; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">📋 Create Order</a>',
            print_url, order_url
        )
    
    @admin.action(description=_('Create Purchase Order from selected'))
    def create_purchase_order_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Please select exactly one purchase quotation.'), level='warning')
            return
        
        purchase_quotation = queryset.first()
        purchase_order, error = copy_purchase_quotation_to_order(purchase_quotation.id)
        
        if purchase_order:
            url = reverse('admin:erp_purchaseorder_change', args=[purchase_order.id])
            self.message_user(
                request,
                format_html('Purchase Order <a href="{}">{}</a> created successfully!', url, purchase_order.order_number),
                level='success'
            )
        else:
            self.message_user(request, f'Error: {error}', level='error')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(BranchFilteredAdmin):
    list_display = ['order_number', 'order_date', 'supplier', 'branch', 'status', 'total_amount', 'paid_amount', 'due_amount', 'action_buttons']
    list_filter = ['status', 'order_date', 'branch']
    search_fields = ['order_number', 'supplier__name']
    readonly_fields = ['order_number', 'subtotal', 'total_amount', 'due_amount']
    inlines = [PurchaseOrderItemInline]
    actions = ['create_receipt_action', 'create_invoice_action', 'create_return_action']
    autocomplete_fields = ['supplier', 'purchase_quotation']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('supplier', 'purchase_quotation').prefetch_related('items__product')
    
    
    fieldsets = (
        (_('Order Information'), {
            'fields': (
                ('order_number', 'order_date', 'expected_date'),
                ('purchase_quotation',),
                ('supplier', 'status'),
            ),
            'classes': ['tab'],
        }),
        (_('Financial Details'), {
            'fields': (
                ('subtotal', 'discount_amount', 'tax_amount'),
                ('total_amount', 'paid_amount', 'due_amount'),
                ('notes',),
            ),
            'classes': ['tab'],
        }),
    )
    
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_totals()
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-purchase-order', args=[obj.id])
        receipt_url = reverse('erp:copy-purchase-order-to-receipt', args=[obj.id])
        invoice_url = reverse('erp:copy-purchase-order-to-invoice', args=[obj.id])
        return_url = reverse('erp:copy-purchase-order-to-return', args=[obj.id])
        
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px; margin-right: 3px;">🖨️ Print</a>'
            '<a href="{}" style="background: #10B981; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px; margin-right: 3px;">📦 Receipt</a>'
            '<a href="{}" style="background: #F59E0B; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px; margin-right: 3px;">📄 Invoice</a>'
            '<a href="{}" style="background: #EF4444; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">↩️ Return</a>',
            print_url, receipt_url, invoice_url, return_url
        )
    
    @admin.action(description=_('Create Receipt from selected'))
    def create_receipt_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Please select exactly one purchase order.'), level='warning')
            return
        
        purchase_order = queryset.first()
        goods_receipt, error = copy_purchase_order_to_receipt(purchase_order.id)
        
        if goods_receipt:
            url = reverse('admin:erp_goodsreceiptpo_change', args=[goods_receipt.id])
            self.message_user(
                request,
                format_html('Goods Receipt <a href="{}">{}</a> created successfully!', url, goods_receipt.receipt_number),
                level='success'
            )
        else:
            self.message_user(request, f'Error: {error}', level='error')
    
    @admin.action(description=_('Create Invoice from selected'))
    def create_invoice_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Please select exactly one purchase order.'), level='warning')
            return
        
        purchase_order = queryset.first()
        purchase_invoice, error = copy_purchase_order_to_invoice(purchase_order.id)
        
        if purchase_invoice:
            url = reverse('admin:erp_purchaseinvoice_change', args=[purchase_invoice.id])
            self.message_user(
                request,
                format_html('Purchase Invoice <a href="{}">{}</a> created successfully!', url, purchase_invoice.invoice_number),
                level='success'
            )
        else:
            self.message_user(request, f'Error: {error}', level='error')
    
    @admin.action(description=_('Create Return from selected'))
    def create_return_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Please select exactly one purchase order.'), level='warning')
            return
        
        purchase_order = queryset.first()
        purchase_return, error = copy_purchase_order_to_return(purchase_order.id)
        
        if purchase_return:
            url = reverse('admin:erp_purchasereturn_change', args=[purchase_return.id])
            self.message_user(
                request,
                format_html('Purchase Return <a href="{}">{}</a> created successfully!', url, purchase_return.return_number),
                level='success'
            )
        else:
            self.message_user(request, f'Error: {error}', level='error')


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(BranchFilteredAdmin):
    list_display = ['receipt_number', 'warehouse', 'receipt_date', 'receipt_type', 'warehouse', 'status', 'received_by', 'action_buttons']
    list_filter = ['status', 'receipt_type', 'warehouse', 'receipt_date', 'warehouse']
    search_fields = ['receipt_number', 'reference']
    readonly_fields = ['receipt_number']
    inlines = [GoodsReceiptItemInline]
    autocomplete_fields = ['warehouse']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('warehouse').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('receipt_number', 'receipt_date'),
                ('receipt_type', 'warehouse'),
                ('status',),
            ),
            'classes': ['tab'],
        }),
        (_('Receipt Details'), {
            'fields': (
                ('received_by', 'reference'),
            ),
            'classes': ['tab'],
        }),
        (_('Notes'), {
            'fields': (('notes',),),
            'classes': ['tab'],
        }),
    )
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-goods-receipt', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🖨️ Print</a>',
            print_url
        )


# Goods Receipt PO Inline
class GoodsReceiptPOItemInline(TabularInline):
    model = GoodsReceiptPOItem
    extra = 0
    fields = ['product', 'ordered_quantity', 'received_quantity', 'rejected_quantity', 'accepted_quantity', 'unit_price', 'line_total', 'rejection_reason']
    readonly_fields = ['ordered_quantity', 'accepted_quantity', 'line_total']
    autocomplete_fields = ['product']


@admin.register(GoodsReceiptPO)
class GoodsReceiptPOAdmin(BranchFilteredAdmin):
    list_display = ['receipt_number', 'branch', 'receipt_date', 'purchase_order', 'supplier', 'warehouse', 'status', 'received_by', 'action_buttons']
    list_filter = ['status', 'warehouse', 'receipt_date', 'supplier', 'branch']
    search_fields = ['receipt_number', 'supplier__name', 'purchase_order__order_number', 'reference']
    readonly_fields = ['receipt_number']
    inlines = [GoodsReceiptPOItemInline]
    date_hierarchy = 'receipt_date'
    autocomplete_fields = ['purchase_order', 'supplier', 'warehouse']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('purchase_order', 'supplier', 'warehouse').prefetch_related('items__product')
    
    fieldsets = (
        (_('Purchase Order'), {
            'fields': (
                ('receipt_number', 'receipt_date'),
                ('purchase_order', 'supplier'),
                ('warehouse', 'status'),
            ),
            'classes': ['tab'],
        }),
        (_('Receipt Details'), {
            'fields': (
                ('received_by', 'inspected_by'),
                ('supplier_delivery_note', 'reference'),
            ),
            'classes': ['tab'],
        }),
        (_('Notes'), {
            'fields': (('notes',),),
            'classes': ['tab'],
        }),
    )
    
    actions = ['create_from_po']
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-goods-receipt-po', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🖨️ Print</a>',
            print_url
        )
    
    @admin.action(description=_('📦 Create Receipt from Purchase Order'))
    def create_from_po(self, request, queryset):
        # This action would be used from PO admin
        pass


@admin.register(GoodsIssue)
class GoodsIssueAdmin(BranchFilteredAdmin):
    list_display = ['issue_number', 'warehouse', 'issue_date', 'issue_type', 'warehouse', 'sales_order', 'customer', 'status', 'issued_by']
    list_filter = ['status', 'issue_type', 'warehouse', 'issue_date', 'warehouse']
    search_fields = ['issue_number', 'customer__name', 'sales_order__order_number', 'reference']
    readonly_fields = ['issue_number']
    inlines = [GoodsIssueItemInline]
    autocomplete_fields = ['sales_order', 'customer', 'warehouse']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('warehouse', 'sales_order', 'customer').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('issue_number', 'issue_date'),
                ('issue_type',),
                ('sales_order',),
                ('customer',),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required issue information'),
        }),
        (_('Issue Details'), {
            'fields': (
                ('issued_by', 'issued_to'),
                ('warehouse',),
                ('reference',),
            ),
            'classes': ['tab'],
            'description': _('Issue and warehouse information'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional issue details'),
        }),
    )
    
    def save_formset(self, request, form, formset, change):
        """Validate inline items before saving"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.full_clean()
            instance.save()
        formset.save_m2m()
    


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(ModelAdmin):
    list_display = ['invoice_number', 'invoice_date', 'purchase_order', 'supplier', 'status', 'total_amount', 'paid_amount', 'due_amount', 'action_buttons']
    list_filter = ['status', 'invoice_date']
    search_fields = ['invoice_number', 'supplier__name', 'purchase_order__order_number']
    readonly_fields = ['invoice_number', 'subtotal', 'total_amount', 'due_amount']
    inlines = [PurchaseInvoiceItemInline]
    autocomplete_fields = ['supplier', 'purchase_order']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('supplier', 'purchase_order').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('invoice_number', 'invoice_date', 'due_date'),
                ('purchase_order',),
                ('supplier',),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required invoice information'),
        }),
        (_('Financial Details'), {
            'fields': (
                ('subtotal', 'discount_amount', 'tax_amount'),
                ('total_amount', 'paid_amount', 'due_amount'),
            ),
            'classes': ['tab'],
            'description': _('Financial calculations and payments'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional invoice details'),
        }),
    )
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-purchase-invoice', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🖨️ Print</a>',
            print_url
        )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_totals()
    
    def save_formset(self, request, form, formset, change):
        """Validate inline items before saving"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.full_clean()
            instance.save()
        formset.save_m2m()
    


@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(BranchFilteredAdmin):
    list_display = ['return_number', 'warehouse', 'return_date', 'purchase_order', 'supplier', 'status', 'total_amount', 'refund_amount', 'action_buttons']
    list_filter = ['status', 'return_date', 'warehouse']
    search_fields = ['return_number', 'supplier__name', 'purchase_order__order_number']
    readonly_fields = ['return_number', 'subtotal', 'total_amount']
    inlines = [PurchaseReturnItemInline]
    autocomplete_fields = ['supplier', 'purchase_order', 'warehouse']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('supplier', 'purchase_order', 'warehouse').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('return_number', 'return_date'),
                ('purchase_order',),
                ('supplier',),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required return information'),
        }),
        (_('Financial Details'), {
            'fields': (
                ('subtotal', 'total_amount', 'refund_amount'),
            ),
            'classes': ['tab'],
            'description': _('Financial calculations and refunds'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('reason',),
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional return details'),
        }),
    )
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-purchase-return', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🖨️ Print</a>',
            print_url
        )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_totals()
    
    def save_formset(self, request, form, formset, change):
        """Validate inline items before saving"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.full_clean()
            instance.save()
        formset.save_m2m()


# ==================== PRODUCTION MODULE ====================

@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(BranchFilteredAdmin):
    list_display = ['bom_number', 'branch', 'name', 'product', 'version', 'quantity', 'status', 'material_cost', 'total_cost', 'action_buttons']
    list_filter = ['status', 'created_at', 'branch']
    search_fields = ['bom_number', 'name', 'product__name', 'product__sku']
    readonly_fields = ['bom_number', 'material_cost', 'total_cost']
    inlines = [BOMComponentInline]
    actions = ['create_production_order_action', 'set_as_default_action']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('product').prefetch_related('components__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('bom_number', 'name'),
                ('product', 'version'),
                ('quantity', 'status'),
            ),
            'classes': ['tab'],
            'description': _('Required BOM information'),
        }),
        (_('Cost Information'), {
            'fields': (
                ('material_cost', 'labor_cost'),
                ('overhead_cost', 'total_cost'),
            ),
            'classes': ['tab'],
            'description': _('Cost breakdown'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional BOM details'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_costs()
    
    @admin.action(description=_('Set as Default BOM for Product'))
    def set_as_default_action(self, request, queryset):
        """Set selected BOM as default for its product"""
        for bom in queryset:
            if bom.status == 'active':
                bom.product.default_bom = bom
                bom.product.save(update_fields=['default_bom'])
        self.message_user(request, _('Selected BOMs have been set as default for their products.'), level='success')
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-bom', args=[obj.id])
        production_order_url = reverse('erp:copy-bom-to-production-order', args=[obj.id])
        
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px; margin-right: 3px;">🖨️ Print</a>'
            '<a href="{}" style="background: #10B981; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🏭 Create Production Order</a>',
            print_url, production_order_url
        )
    
    @admin.action(description=_('Create Production Order from selected'))
    def create_production_order_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Please select exactly one BOM.'), level='warning')
            return
        
        bom = queryset.first()
        from .utils import copy_bom_to_production_order
        production_order, error = copy_bom_to_production_order(bom.id)
        
        if production_order:
            url = reverse('admin:erp_productionorder_change', args=[production_order.id])
            self.message_user(
                request,
                format_html('Production Order <a href="{}">{}</a> created successfully!', url, production_order.order_number),
                level='success'
            )
        else:
            self.message_user(request, f'Error: {error}', level='error')


@admin.register(ProductionOrder)
class ProductionOrderAdmin(BranchFilteredAdmin):
    list_display = ['order_number', 'warehouse', 'order_date', 'product', 'bom', 'warehouse', 'quantity_to_produce', 'quantity_produced', 'status', 'action_buttons']
    list_filter = ['status', 'order_date', 'warehouse', 'warehouse']
    search_fields = ['order_number', 'product__name', 'bom__bom_number', 'reference']
    readonly_fields = ['order_number', 'product']
    inlines = [ProductionOrderComponentInline]
    actions = ['create_production_receipt_action']
    autocomplete_fields = ['bom', 'warehouse', 'sales_order']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('product', 'bom', 'warehouse').prefetch_related('components__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('order_number', 'order_date'),
                ('bom', 'product'),
                ('warehouse', 'status'),
            ),
            'classes': ['tab'],
            'description': _('Required production order information'),
        }),
        (_('Quantity & Schedule'), {
            'fields': (
                ('quantity_to_produce', 'quantity_produced'),
                ('planned_start_date', 'planned_end_date'),
                ('actual_start_date', 'actual_end_date'),
            ),
            'classes': ['tab'],
            'description': _('Production quantities and schedule'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('sales_order', 'reference'),
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional production order details'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Save model and auto-load BOM components if BOM changed"""
        # Track if BOM changed
        bom_changed = False
        old_bom_id = None
        
        if obj.pk:
            # Existing record - check if BOM changed
            old_obj = ProductionOrder.objects.filter(pk=obj.pk).first()
            if old_obj and old_obj.bom_id != obj.bom_id:
                bom_changed = True
                old_bom_id = old_obj.bom_id
        else:
            # New record with BOM
            if obj.bom:
                bom_changed = True
        
        # Save the model first
        super().save_model(request, obj, form, change)
        
        # If BOM changed, load components from BOM
        if bom_changed and obj.bom:
            self._load_bom_components(obj, request)
    
    def _load_bom_components(self, production_order, request):
        """Load components from BOM to Production Order"""
        from decimal import Decimal
        
        # Delete existing components (if any)
        production_order.components.all().delete()
        
        # Get BOM components
        bom_components = production_order.bom.components.all()
        
        if not bom_components.exists():
            self.message_user(request, _('BOM has no components to load.'), level='warning')
            return
        
        # Calculate quantity multiplier
        qty_multiplier = production_order.quantity_to_produce / production_order.bom.quantity
        
        # Create production order components
        components_created = 0
        for bom_comp in bom_components:
            # Calculate required quantity with scrap
            base_qty = bom_comp.quantity * qty_multiplier
            scrap_factor = Decimal('1.00') + (bom_comp.scrap_percentage / Decimal('100.00'))
            required_qty = base_qty * scrap_factor
            
            ProductionOrderComponent.objects.create(
                production_order=production_order,
                product=bom_comp.product,
                quantity_required=required_qty,
                unit_cost=bom_comp.unit_cost,
            )
            components_created += 1
        
        self.message_user(
            request, 
            _(f'Loaded {components_created} components from BOM "{production_order.bom.bom_number}"'),
            level='success'
        )
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-production-order', args=[obj.id])
        production_receipt_url = reverse('erp:copy-production-order-to-receipt', args=[obj.id])
        
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px; margin-right: 3px;">🖨️ Print</a>'
            '<a href="{}" style="background: #10B981; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">📦 Create Receipt</a>',
            print_url, production_receipt_url
        )
    
    @admin.action(description=_('Create Production Receipt from selected'))
    def create_production_receipt_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Please select exactly one Production Order.'), level='warning')
            return
        
        production_order = queryset.first()
        from .utils import copy_production_order_to_receipt
        production_receipt, error = copy_production_order_to_receipt(production_order.id)
        
        if production_receipt:
            url = reverse('admin:erp_productionreceipt_change', args=[production_receipt.id])
            self.message_user(
                request,
                format_html('Production Receipt <a href="{}">{}</a> created successfully!', url, production_receipt.receipt_number),
                level='success'
            )
        else:
            self.message_user(request, f'Error: {error}', level='error')


@admin.register(ProductionReceipt)
class ProductionReceiptAdmin(BranchFilteredAdmin):
    list_display = ['receipt_number', 'warehouse', 'receipt_date', 'production_order', 'warehouse', 'status', 'item_count', 'action_buttons']
    list_filter = ['status', 'receipt_date', 'warehouse', 'warehouse']
    search_fields = ['receipt_number', 'production_order__order_number']
    readonly_fields = ['receipt_number', 'warehouse']
    inlines = [ProductionReceiptItemInline]
    autocomplete_fields = ['production_order']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('production_order', 'warehouse').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('receipt_number', 'receipt_date'),
                ('production_order',),
                ('warehouse',),
                ('status',),
            ),
            'classes': ['tab'],
        }),
        (_('Additional Details'), {
            'fields': (
                ('received_by', 'inspected_by'),
                ('notes',),
            ),
            'classes': ['tab'],
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Save and auto-load finished goods from production order"""
        po_changed = False
        
        if obj.pk:
            old_obj = ProductionReceipt.objects.filter(pk=obj.pk).first()
            if old_obj and old_obj.production_order_id != obj.production_order_id:
                po_changed = True
        else:
            po_changed = True
        
        super().save_model(request, obj, form, change)
        
        if po_changed and obj.production_order:
            self._auto_load_finished_goods(obj, request)
    
    def _auto_load_finished_goods(self, production_receipt, request):
        """Auto-load finished goods from production order"""
        from decimal import Decimal
        
        # Delete existing items
        production_receipt.items.all().delete()
        
        po = production_receipt.production_order
        
        # Create finished goods item
        ProductionReceiptItem.objects.create(
            production_receipt=production_receipt,
            product=po.product,
            planned_quantity=po.quantity_to_produce,
            received_quantity=po.quantity_to_produce,
            rejected_quantity=Decimal('0.00'),
            unit_cost=po.product.purchase_price,
        )
        
        self.message_user(
            request,
            _(f'Auto-loaded finished goods: {po.product.name}'),
            level='success'
        )
    
    @display(description=_('Items'))
    def item_count(self, obj):
        return obj.items.count()
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-production-receipt', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🖨️ Print</a>',
            print_url
        )


# ==================== PRODUCTION ISSUE ====================

class ProductionIssueItemInline(TabularInline):
    model = ProductionIssueItem
    extra = 0
    fields = ['product', 'base_quantity', 'issued_quantity', 'unit_cost', 'line_total']
    readonly_fields = ['line_total']
    autocomplete_fields = ['product']


@admin.register(ProductionIssue)
class ProductionIssueAdmin(BranchFilteredAdmin):
    list_display = ['issue_number', 'warehouse', 'issue_date', 'production_order', 'warehouse', 'status', 'issued_by', 'item_count', 'action_buttons']
    list_filter = ['status', 'issue_date', 'warehouse', 'warehouse']
    search_fields = ['issue_number', 'production_order__order_number', 'issued_by']
    readonly_fields = ['issue_number']
    inlines = [ProductionIssueItemInline]
    autocomplete_fields = ['production_order', 'warehouse']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('production_order', 'warehouse').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('issue_number', 'issue_date'),
                ('production_order',),
                ('warehouse',),
                ('status',),
            ),
            'classes': ['tab'],
        }),
        (_('Additional Details'), {
            'fields': (
                ('issued_by',),
                ('notes',),
            ),
            'classes': ['tab'],
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Save and auto-load components from production order BOM"""
        # Check if production order changed
        po_changed = False
        
        if obj.pk:
            old_obj = ProductionIssue.objects.filter(pk=obj.pk).first()
            if old_obj and old_obj.production_order_id != obj.production_order_id:
                po_changed = True
        else:
            # New record
            po_changed = True
        
        super().save_model(request, obj, form, change)
        
        # Auto-load components if production order changed
        if po_changed and obj.production_order:
            self._auto_load_components(obj, request)
    
    def _auto_load_components(self, production_issue, request):
        """Auto-load components from production order BOM"""
        from decimal import Decimal
        
        po = production_issue.production_order
        
        if not po.bom:
            self.message_user(request, _('Production Order has no BOM'), level='warning')
            return
        
        # Delete existing items
        production_issue.items.all().delete()
        
        # Load components from BOM
        items_created = 0
        for comp in po.bom.components.all():
            comp_qty = comp.quantity * po.quantity_to_produce * (Decimal('1') + comp.scrap_percentage / Decimal('100'))
            
            ProductionIssueItem.objects.create(
                production_issue=production_issue,
                product=comp.product,
                base_quantity=comp_qty,
                issued_quantity=comp_qty,
                unit_cost=comp.product.purchase_price,
            )
            items_created += 1
        
        if items_created > 0:
            self.message_user(
                request,
                _(f'Auto-loaded {items_created} components from BOM'),
                level='success'
            )
    
    @display(description=_('Items'))
    def item_count(self, obj):
        return obj.items.count()
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-production-issue', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🖨️ Print</a>',
            print_url
        )


# ==================== INVENTORY TRANSFER ====================

@admin.register(InventoryTransfer)
class InventoryTransferAdmin(BranchFilteredAdmin):
    list_display = ['transfer_number', 'from_warehouse', 'to_warehouse', 'transfer_date', 'from_warehouse', 'to_warehouse', 'status', 'transferred_by']
    list_filter = ['status', 'transfer_date', 'from_warehouse', 'to_warehouse', 'from_warehouse', 'to_warehouse']
    search_fields = ['transfer_number', 'reference', 'transferred_by', 'received_by']
    readonly_fields = ['transfer_number']
    inlines = [InventoryTransferItemInline]
    autocomplete_fields = ['from_warehouse', 'to_warehouse']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('from_warehouse', 'to_warehouse').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('transfer_number', 'transfer_date'),
                ('from_warehouse', 'to_warehouse'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required transfer information'),
        }),
        (_('Transfer Details'), {
            'fields': (
                ('transferred_by', 'received_by'),
                ('reference',),
            ),
            'classes': ['tab'],
            'description': _('Transfer tracking information'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional transfer details'),
        }),
    )
    
    def save_formset(self, request, form, formset, change):
        """Validate inline items before saving"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.full_clean()
            instance.save()
        formset.save_m2m()


# ==================== PRODUCT WAREHOUSE STOCK ====================

@admin.register(ProductWarehouseStock)
class ProductWarehouseStockAdmin(ModelAdmin):
    list_display = ['product', 'warehouse', 'quantity', 'updated_at']
    list_filter = ['warehouse']
    search_fields = ['product__name', 'product__sku', 'warehouse__name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['product', 'warehouse']
    
    fieldsets = (
        (_('Stock Information'), {
            'fields': ('product', 'warehouse', 'quantity')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )


# ==================== STOCK TRANSACTION ====================

@admin.register(StockTransaction)
class StockTransactionAdmin(BranchFilteredAdmin):
    list_display = ['product', 'branch', 'warehouse', 'transaction_type', 'quantity', 'balance_after', 'reference', 'created_at']
    list_filter = ['transaction_type', 'warehouse', 'created_at', 'branch']
    search_fields = ['product__name', 'warehouse__name', 'reference']
    readonly_fields = ['created_at', 'balance_after']
    
    fieldsets = (
        (_('Transaction Details'), {
            'fields': ('product', 'warehouse', 'transaction_type', 'quantity', 'balance_after', 'reference')
        }),
        (_('Additional Information'), {
            'fields': ('notes', 'created_at')
        }),
    )



# ==================== BANKING MODULE ====================

class IncomingPaymentInvoiceInline(TabularInline):
    model = IncomingPaymentInvoice
    extra = 1
    fields = ['invoice', 'amount_allocated']
    


class OutgoingPaymentInvoiceInline(TabularInline):
    model = OutgoingPaymentInvoice
    extra = 1
    fields = ['purchase_invoice', 'amount_allocated']
    


@admin.register(BankAccount)
class BankAccountAdmin(ModelAdmin):
    list_display = ['account_name', 'account_number', 'account_type', 'bank_name', 'currency', 'current_balance', 'is_active']
    list_filter = ['account_type', 'is_active', 'currency']
    search_fields = ['account_name', 'account_number', 'bank_name']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('account_name', 'account_number'),
                ('account_type', 'currency'),
            ),
            'classes': ['tab'],
            'description': _('Bank account identification'),
        }),
        (_('Bank Details'), {
            'fields': (
                ('bank_name', 'branch'),
            ),
            'classes': ['tab'],
            'description': _('Bank information'),
        }),
        (_('Balance'), {
            'fields': (
                ('opening_balance', 'current_balance'),
            ),
            'classes': ['tab'],
            'description': _('Account balance information'),
        }),
        (_('Status & Notes'), {
            'fields': (
                ('is_active',),
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Account status and notes'),
        }),
    )


@admin.register(IncomingPayment)
class IncomingPaymentAdmin(BranchFilteredAdmin):
    list_display = ['payment_number', 'branch', 'payment_date', 'customer', 'bank_account', 'payment_method', 'amount', 'status', 'action_buttons']
    list_filter = ['status', 'payment_method', 'payment_date', 'bank_account', 'branch']
    search_fields = ['payment_number', 'customer__name', 'reference', 'check_number']
    readonly_fields = ['payment_number']
    inlines = [IncomingPaymentInvoiceInline]
    autocomplete_fields = ['customer', 'bank_account']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'bank_account').prefetch_related('invoices__invoice')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('payment_number', 'payment_date'),
                ('customer', 'bank_account'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required payment information'),
        }),
        (_('Payment Details'), {
            'fields': (
                ('amount',),
                ('payment_method',),
                ('reference', 'check_number'),
            ),
            'classes': ['tab'],
            'description': _('Payment method and details'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional payment notes'),
        }),
    )
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-incoming-payment', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #10B981; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🧾 Receipt</a>',
            print_url
        )
    
    def save_formset(self, request, form, formset, change):
        """Validate inline items before saving"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.full_clean()
            instance.save()
        formset.save_m2m()


@admin.register(OutgoingPayment)
class OutgoingPaymentAdmin(BranchFilteredAdmin):
    list_display = ['payment_number', 'branch', 'payment_date', 'supplier', 'bank_account', 'payment_method', 'amount', 'status', 'action_buttons']
    list_filter = ['status', 'payment_method', 'payment_date', 'bank_account', 'branch']
    search_fields = ['payment_number', 'supplier__name', 'reference', 'check_number']
    readonly_fields = ['payment_number']
    inlines = [OutgoingPaymentInvoiceInline]
    autocomplete_fields = ['supplier', 'bank_account']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('supplier', 'bank_account').prefetch_related('invoices__purchase_invoice')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('payment_number', 'payment_date'),
                ('supplier', 'bank_account'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required payment information'),
        }),
        (_('Payment Details'), {
            'fields': (
                ('amount',),
                ('payment_method',),
                ('reference', 'check_number'),
            ),
            'classes': ['tab'],
            'description': _('Payment method and details'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional payment notes'),
        }),
    )
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-outgoing-payment', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #10B981; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🧾 Receipt</a>',
            print_url
        )
    
    def save_formset(self, request, form, formset, change):
        """Validate inline items before saving"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.full_clean()
            instance.save()
        formset.save_m2m()



# ==================== ACCOUNTING/FINANCE MODULE ====================

class JournalEntryLineInline(TabularInline):
    model = JournalEntryLine
    extra = 2
    fields = ['account', 'description', 'debit', 'credit', 'project', 'cost_center']
    


@admin.register(AccountType)
class AccountTypeAdmin(ModelAdmin):
    list_display = ['name', 'type_category', 'is_active']
    list_filter = ['type_category', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'type_category'),
            ),
            'classes': ['tab'],
            'description': _('Account type classification'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Account type status'),
        }),
    )


@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(ModelAdmin):
    list_display = ['account_code', 'account_name', 'account_type', 'parent_account', 'currency', 'current_balance', 'is_active']
    list_filter = ['account_type', 'is_active', 'currency']
    search_fields = ['account_code', 'account_name', 'description']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('account_code', 'account_name'),
                ('account_type', 'parent_account'),
                ('currency',),
            ),
            'classes': ['tab'],
            'description': _('Account identification and classification'),
        }),
        (_('Balance'), {
            'fields': (
                ('opening_balance', 'current_balance'),
            ),
            'classes': ['tab'],
            'description': _('Account balance information'),
        }),
        (_('Status & Description'), {
            'fields': (
                ('is_active',),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Account status and notes'),
        }),
    )


@admin.register(CostCenter)
class CostCenterAdmin(ModelAdmin):
    list_display = ['code', 'name', 'parent_cost_center', 'manager', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'manager']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('code', 'name'),
                ('parent_cost_center',),
                ('manager',),
            ),
            'classes': ['tab'],
            'description': _('Cost center identification'),
        }),
        (_('Status & Description'), {
            'fields': (
                ('is_active',),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Cost center status and notes'),
        }),
    )


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ['project_code', 'project_name', 'customer', 'status', 'project_manager', 'budget_amount', 'actual_cost', 'budget_variance', 'is_active']
    list_filter = ['status', 'is_active']
    search_fields = ['project_code', 'project_name', 'customer__name', 'project_manager']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('project_code', 'project_name'),
                ('customer', 'status'),
                ('project_manager',),
            ),
            'classes': ['tab'],
            'description': _('Project identification'),
        }),
        (_('Schedule'), {
            'fields': (
                ('start_date', 'end_date'),
            ),
            'classes': ['tab'],
            'description': _('Project timeline'),
        }),
        (_('Budget'), {
            'fields': (
                ('budget_amount', 'actual_cost'),
            ),
            'classes': ['tab'],
            'description': _('Project budget and costs'),
        }),
        (_('Status & Description'), {
            'fields': (
                ('is_active',),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Project status and notes'),
        }),
    )
    
    @display(description=_('Budget Variance'))
    def budget_variance(self, obj):
        variance = obj.budget_variance
        if variance < 0:
            return format_html('<span style="color: red;">{}</span>', variance)
        return format_html('<span style="color: green;">{}</span>', variance)


@admin.register(JournalEntry)
class JournalEntryAdmin(BranchFilteredAdmin):
    list_display = ['entry_number', 'branch', 'entry_date', 'posting_date', 'status', 'total_debit', 'total_credit', 'is_balanced_display', 'project', 'cost_center']
    list_filter = ['status', 'entry_date', 'project', 'cost_center', 'branch']
    search_fields = ['entry_number', 'reference', 'notes']
    readonly_fields = ['entry_number', 'total_debit', 'total_credit']
    inlines = [JournalEntryLineInline]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('project', 'cost_center').prefetch_related('lines__account', 'lines__cost_center', 'lines__project')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('entry_number', 'entry_date'),
                ('posting_date', 'status'),
                ('reference',),
            ),
            'classes': ['tab'],
            'description': _('Journal entry identification'),
        }),
        (_('Dimensions'), {
            'fields': (
                ('project', 'cost_center'),
            ),
            'classes': ['tab'],
            'description': _('Optional project and cost center'),
        }),
        (_('Totals'), {
            'fields': (
                ('total_debit', 'total_credit'),
            ),
            'classes': ['tab'],
            'description': _('Entry totals (must be balanced)'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Optional notes'),
        }),
    )
    
    @display(description=_('Balanced'), boolean=True)
    def is_balanced_display(self, obj):
        return obj.is_balanced
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_totals()
    
    def save_formset(self, request, form, formset, change):
        """Validate inline items before saving"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.full_clean()
            instance.save()
        formset.save_m2m()


@admin.register(FiscalYear)
class FiscalYearAdmin(ModelAdmin):
    list_display = ['year_name', 'start_date', 'end_date', 'is_closed']
    list_filter = ['is_closed']
    search_fields = ['year_name']
    list_editable = ['is_closed']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('year_name',),
                ('start_date', 'end_date'),
            ),
            'classes': ['tab'],
            'description': _('Fiscal year period'),
        }),
        (_('Status'), {
            'fields': (
                ('is_closed',),
            ),
            'classes': ['tab'],
            'description': _('Fiscal year status'),
        }),
    )


@admin.register(Budget)
class BudgetAdmin(BranchFilteredAdmin):
    list_display = ['budget_name', 'branch', 'fiscal_year', 'account', 'project', 'cost_center', 'budget_amount', 'actual_amount', 'variance_display', 'utilization_display', 'is_active']
    list_filter = ['fiscal_year', 'is_active', 'account__account_type', 'branch']
    search_fields = ['budget_name', 'account__account_name', 'project__project_name', 'cost_center__name']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('budget_name', 'fiscal_year'),
                ('account',),
            ),
            'classes': ['tab'],
            'description': _('Budget identification'),
        }),
        (_('Dimensions'), {
            'fields': (
                ('project', 'cost_center'),
            ),
            'classes': ['tab'],
            'description': _('Optional project and cost center'),
        }),
        (_('Budget Amounts'), {
            'fields': (
                ('budget_amount', 'actual_amount'),
            ),
            'classes': ['tab'],
            'description': _('Budget and actual amounts'),
        }),
        (_('Status & Notes'), {
            'fields': (
                ('is_active',),
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Budget status and notes'),
        }),
    )
    
    @display(description=_('Variance'))
    def variance_display(self, obj):
        variance = obj.variance
        if variance < 0:
            return format_html('<span style="color: red;">{}</span>', variance)
        return format_html('<span style="color: green;">{}</span>', variance)
    
    @display(description=_('Utilization %'))
    def utilization_display(self, obj):
        utilization = obj.utilization_percentage
        if utilization > 100:
            return format_html('<span style="color: red;">{:.2f}%</span>', utilization)
        elif utilization > 80:
            return format_html('<span style="color: orange;">{:.2f}%</span>', utilization)
        return format_html('<span style="color: green;">{:.2f}%</span>', utilization)


# ==================== CURRENCY & EXCHANGE RATE ADMIN ====================

@admin.register(Currency)
class CurrencyAdmin(ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'decimal_places', 'is_base_currency', 'is_active']
    list_filter = ['is_base_currency', 'is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('code', 'name'),
                ('symbol', 'decimal_places'),
            ),
            'classes': ['tab'],
            'description': _('Currency identification'),
        }),
        (_('Settings'), {
            'fields': (
                ('is_base_currency', 'is_active'),
            ),
            'classes': ['tab'],
            'description': _('Currency settings'),
        }),
    )


@admin.register(ExchangeRate)
class ExchangeRateAdmin(ModelAdmin):
    list_display = ['from_currency', 'to_currency', 'rate', 'effective_date', 'is_active']
    list_filter = ['from_currency', 'to_currency', 'is_active', 'effective_date']
    search_fields = ['from_currency__code', 'to_currency__code']
    list_editable = ['is_active']
    date_hierarchy = 'effective_date'
    
    fieldsets = (
        (_('Currency Pair'), {
            'fields': (
                ('from_currency', 'to_currency'),
            ),
            'classes': ['tab'],
            'description': _('Select currencies for exchange'),
        }),
        (_('Rate Details'), {
            'fields': (
                ('rate', 'effective_date'),
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Exchange rate and validity'),
        }),
    )


# ==================== TAX CONFIGURATION ADMIN ====================

class TaxRateInline(TabularInline):
    model = TaxRate
    extra = 1
    fields = ['name', 'rate', 'is_default', 'is_active', 'effective_from', 'effective_to']


@admin.register(TaxType)
class TaxTypeAdmin(ModelAdmin):
    list_display = ['code', 'name', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_active']
    inlines = [TaxRateInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('code', 'name'),
                ('category',),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Tax type identification'),
        }),
        (_('Accounting Integration'), {
            'fields': (
                ('sales_account', 'purchase_account'),
            ),
            'classes': ['tab'],
            'description': _('GL accounts for tax posting'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Tax type status'),
        }),
    )


@admin.register(TaxRate)
class TaxRateAdmin(ModelAdmin):
    list_display = ['tax_type', 'name', 'rate', 'is_default', 'is_active', 'effective_from', 'effective_to']
    list_filter = ['tax_type', 'is_default', 'is_active']
    search_fields = ['name', 'tax_type__name', 'tax_type__code']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('tax_type', 'name'),
                ('rate',),
            ),
            'classes': ['tab'],
            'description': _('Tax rate identification'),
        }),
        (_('Validity'), {
            'fields': (
                ('effective_from', 'effective_to'),
            ),
            'classes': ['tab'],
            'description': _('Rate validity period'),
        }),
        (_('Settings'), {
            'fields': (
                ('is_default', 'is_active'),
            ),
            'classes': ['tab'],
            'description': _('Rate settings'),
        }),
    )


# ==================== PAYMENT TERMS ADMIN ====================

@admin.register(PaymentTerm)
class PaymentTermAdmin(ModelAdmin):
    list_display = ['code', 'name', 'days', 'discount_days', 'discount_percentage', 'is_default', 'is_active']
    list_filter = ['is_default', 'is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('code', 'name'),
                ('days',),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Payment term identification'),
        }),
        (_('Early Payment Discount'), {
            'fields': (
                ('discount_days', 'discount_percentage'),
            ),
            'classes': ['tab'],
            'description': _('Discount for early payment'),
        }),
        (_('Settings'), {
            'fields': (
                ('is_default', 'is_active'),
            ),
            'classes': ['tab'],
            'description': _('Payment term settings'),
        }),
    )


# ==================== UNIT OF MEASURE ADMIN ====================

class UOMConversionInline(TabularInline):
    model = UOMConversion
    fk_name = 'from_uom'
    extra = 1
    fields = ['to_uom', 'conversion_factor', 'is_active']


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(ModelAdmin):
    list_display = ['code', 'name', 'uom_type', 'is_base_unit', 'is_active']
    list_filter = ['uom_type', 'is_base_unit', 'is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_active']
    inlines = [UOMConversionInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('code', 'name'),
                ('uom_type',),
            ),
            'classes': ['tab'],
            'description': _('Unit of measure identification'),
        }),
        (_('Settings'), {
            'fields': (
                ('is_base_unit', 'is_active'),
            ),
            'classes': ['tab'],
            'description': _('UOM settings'),
        }),
    )


@admin.register(UOMConversion)
class UOMConversionAdmin(ModelAdmin):
    list_display = ['from_uom', 'to_uom', 'conversion_factor', 'is_active']
    list_filter = ['from_uom__uom_type', 'is_active']
    search_fields = ['from_uom__code', 'from_uom__name', 'to_uom__code', 'to_uom__name']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Conversion'), {
            'fields': (
                ('from_uom', 'to_uom'),
                ('conversion_factor',),
            ),
            'classes': ['tab'],
            'description': _('UOM conversion rule'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Conversion status'),
        }),
    )


# ==================== PRICE LIST ADMIN ====================

class PriceListItemInline(TabularInline):
    model = PriceListItem
    extra = 1
    fields = ['product', 'unit_price', 'min_quantity', 'discount_percentage', 'is_active']
    autocomplete_fields = ['product']


@admin.register(PriceList)
class PriceListAdmin(ModelAdmin):
    list_display = ['code', 'name', 'price_type', 'currency', 'is_default', 'is_active', 'valid_from', 'valid_to']
    list_filter = ['price_type', 'is_default', 'is_active', 'currency']
    search_fields = ['code', 'name']
    list_editable = ['is_active']
    inlines = [PriceListItemInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('code', 'name'),
                ('price_type', 'currency'),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Price list identification'),
        }),
        (_('Validity'), {
            'fields': (
                ('valid_from', 'valid_to'),
            ),
            'classes': ['tab'],
            'description': _('Price list validity period'),
        }),
        (_('Settings'), {
            'fields': (
                ('is_default', 'is_active'),
            ),
            'classes': ['tab'],
            'description': _('Price list settings'),
        }),
    )


@admin.register(PriceListItem)
class PriceListItemAdmin(ModelAdmin):
    list_display = ['price_list', 'product', 'unit_price', 'min_quantity', 'discount_percentage', 'net_price_display', 'is_active']
    list_filter = ['price_list', 'is_active']
    search_fields = ['product__name', 'product__sku', 'price_list__name']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Price List & Product'), {
            'fields': (
                ('price_list', 'product'),
            ),
            'classes': ['tab'],
            'description': _('Select price list and product'),
        }),
        (_('Pricing'), {
            'fields': (
                ('unit_price', 'min_quantity'),
                ('discount_percentage',),
            ),
            'classes': ['tab'],
            'description': _('Price and discount settings'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Item status'),
        }),
    )
    
    @display(description=_('Net Price'))
    def net_price_display(self, obj):
        return obj.net_price


# ==================== DISCOUNT MANAGEMENT ADMIN ====================

class DiscountRuleInline(TabularInline):
    model = DiscountRule
    extra = 1
    fields = ['product', 'category', 'customer', 'min_quantity', 'is_active']


@admin.register(DiscountType)
class DiscountTypeAdmin(ModelAdmin):
    list_display = ['code', 'name', 'discount_method', 'value', 'apply_on', 'valid_from', 'valid_to', 'usage_count', 'is_valid_display', 'is_active']
    list_filter = ['discount_method', 'apply_on', 'is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_active']
    inlines = [DiscountRuleInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('code', 'name'),
                ('discount_method', 'apply_on'),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Discount identification'),
        }),
        (_('Discount Value'), {
            'fields': (
                ('value', 'max_discount_amount'),
                ('min_order_amount',),
            ),
            'classes': ['tab'],
            'description': _('Discount amount settings'),
        }),
        (_('Validity'), {
            'fields': (
                ('valid_from', 'valid_to'),
            ),
            'classes': ['tab'],
            'description': _('Discount validity period'),
        }),
        (_('Usage Limits'), {
            'fields': (
                ('usage_limit', 'per_customer_limit'),
            ),
            'classes': ['tab'],
            'description': _('Usage restrictions'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Discount status'),
        }),
    )
    
    @display(description=_('Valid'))
    def is_valid_display(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Invalid</span>')


@admin.register(DiscountRule)
class DiscountRuleAdmin(ModelAdmin):
    list_display = ['discount_type', 'product', 'category', 'customer', 'min_quantity', 'is_active']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['discount_type__code', 'discount_type__name', 'product__name', 'customer__name']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Discount Type'), {
            'fields': (
                ('discount_type',),
            ),
            'classes': ['tab'],
            'description': _('Select discount type'),
        }),
        (_('Conditions'), {
            'fields': (
                ('product', 'category'),
                ('customer',),
                ('min_quantity',),
            ),
            'classes': ['tab'],
            'description': _('Rule conditions'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Rule status'),
        }),
    )


# ==================== STOCK ADJUSTMENT ADMIN ====================

class StockAdjustmentItemInline(TabularInline):
    model = StockAdjustmentItem
    extra = 1
    fields = ['product', 'system_quantity', 'actual_quantity', 'quantity_difference', 'unit_cost', 'value_difference', 'reason']
    readonly_fields = ['system_quantity', 'quantity_difference', 'value_difference']
    autocomplete_fields = ['product']


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(BranchFilteredAdmin):
    list_display = ['adjustment_number', 'warehouse', 'adjustment_date', 'adjustment_type', 'warehouse', 'status', 'total_increase', 'total_decrease', 'total_value', 'requested_by']
    list_filter = ['adjustment_type', 'status', 'warehouse', 'adjustment_date', 'warehouse']
    search_fields = ['adjustment_number', 'requested_by', 'approved_by']
    readonly_fields = ['adjustment_number', 'total_increase', 'total_decrease', 'total_value']
    inlines = [StockAdjustmentItemInline]
    date_hierarchy = 'adjustment_date'
    autocomplete_fields = ['warehouse']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('warehouse').prefetch_related('items__product')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('adjustment_number', 'adjustment_date'),
                ('adjustment_type', 'warehouse'),
                ('reason',),
            ),
            'classes': ['tab'],
            'description': _('Adjustment identification'),
        }),
        (_('Status & Approval'), {
            'fields': (
                ('status',),
                ('requested_by', 'approved_by'),
                ('approved_date',),
            ),
            'classes': ['tab'],
            'description': _('Approval information - Change status to "Approved" to update stock'),
        }),
        (_('Totals'), {
            'fields': (
                ('total_increase', 'total_decrease'),
                ('total_value',),
            ),
            'classes': ['tab'],
            'description': _('Calculated totals'),
        }),
        (_('Notes'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Additional notes'),
        }),
    )
    
    actions = ['approve_adjustments', 'post_adjustments']
    
    @admin.action(description=_('✅ Approve selected adjustments (Update Stock)'))
    def approve_adjustments(self, request, queryset):
        """Approve adjustments and trigger stock update via signal"""
        count = 0
        for adjustment in queryset.filter(status__in=['draft', 'pending']):
            adjustment.status = 'approved'
            adjustment.approved_by = request.user.get_full_name() or request.user.username
            adjustment.approved_date = timezone.now()
            adjustment.save()  # This triggers the signal
            count += 1
        self.message_user(request, f'{count} adjustment(s) approved and stock updated.')
    
    @admin.action(description=_('📋 Post selected adjustments'))
    def post_adjustments(self, request, queryset):
        """Post approved adjustments"""
        count = 0
        for adjustment in queryset.filter(status='approved'):
            adjustment.status = 'posted'
            adjustment.save()
            count += 1
        self.message_user(request, f'{count} adjustment(s) posted.')
    
    def save_model(self, request, obj, form, change):
        """Auto-fill requested_by on first save"""
        if not obj.pk and not obj.requested_by:
            obj.requested_by = request.user.get_full_name() or request.user.username
        # Store old status before save
        obj._old_status_for_signal = None
        if obj.pk:
            try:
                obj._old_status_for_signal = StockAdjustment.objects.get(pk=obj.pk).status
            except StockAdjustment.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)
    
    def save_related(self, request, form, formsets, change):
        """Save related items first, then process stock transactions"""
        super().save_related(request, form, formsets, change)
        
        # After items are saved, manually trigger stock transaction
        obj = form.instance
        old_status = getattr(obj, '_old_status_for_signal', None)
        
        trigger_statuses = ['approved', 'posted']
        
        if obj.status in trigger_statuses and old_status not in trigger_statuses:
            from erp.models import StockTransaction, ProductWarehouseStock
            from decimal import Decimal
            
            reference = f"ADJ:{obj.adjustment_number}"
            
            # Check if already processed
            if not StockTransaction.objects.filter(reference=reference).exists():
                for item in obj.items.all():
                    diff = item.actual_quantity - item.system_quantity
                    
                    if diff != 0:
                        # Create transaction
                        transaction = StockTransaction.objects.create(
                            product=item.product,
                            warehouse=obj.warehouse,
                            transaction_type='adjustment',
                            quantity=diff,
                            reference=reference,
                            notes=f"{obj.get_adjustment_type_display()}: {item.reason or 'N/A'}"
                        )
                        
                        # Update warehouse stock
                        stock, _ = ProductWarehouseStock.objects.get_or_create(
                            product=item.product,
                            warehouse=obj.warehouse,
                            defaults={'quantity': Decimal('0.00')}
                        )
                        stock.quantity += diff
                        if stock.quantity < 0:
                            stock.quantity = Decimal('0.00')
                        stock.save()
                        
                        # Update balance_after
                        StockTransaction.objects.filter(pk=transaction.pk).update(balance_after=stock.quantity)


@admin.register(StockAdjustmentItem)
class StockAdjustmentItemAdmin(ModelAdmin):
    list_display = ['stock_adjustment', 'product', 'system_quantity', 'actual_quantity', 'quantity_difference', 'value_difference']
    list_filter = ['stock_adjustment__adjustment_type', 'stock_adjustment__status']
    search_fields = ['stock_adjustment__adjustment_number', 'product__name', 'product__sku']
    
    def has_module_permission(self, request):
        return False


# ==================== APPROVAL WORKFLOW ADMIN ====================

class ApprovalLevelInline(TabularInline):
    model = ApprovalLevel
    extra = 1
    fields = ['level', 'name', 'min_amount', 'max_amount', 'approver_user', 'approver_role', 'is_active']


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(ModelAdmin):
    list_display = ['name', 'document_type', 'is_active', 'levels_count']
    list_filter = ['document_type', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active']
    inlines = [ApprovalLevelInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'document_type'),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Workflow identification'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Workflow status'),
        }),
    )
    
    @display(description=_('Levels'))
    def levels_count(self, obj):
        return obj.levels.count()


@admin.register(ApprovalLevel)
class ApprovalLevelAdmin(ModelAdmin):
    list_display = ['workflow', 'level', 'name', 'min_amount', 'max_amount', 'approver_user', 'approver_role', 'is_active']
    list_filter = ['workflow', 'is_active']
    search_fields = ['name', 'workflow__name', 'approver_role']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Workflow & Level'), {
            'fields': (
                ('workflow', 'level'),
                ('name',),
            ),
            'classes': ['tab'],
            'description': _('Level identification'),
        }),
        (_('Amount Conditions'), {
            'fields': (
                ('min_amount', 'max_amount'),
            ),
            'classes': ['tab'],
            'description': _('Amount thresholds'),
        }),
        (_('Approvers'), {
            'fields': (
                ('approver_user', 'approver_role'),
            ),
            'classes': ['tab'],
            'description': _('Who can approve'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Level status'),
        }),
    )


class ApprovalHistoryInline(TabularInline):
    model = ApprovalHistory
    extra = 0
    fields = ['level', 'action', 'action_by', 'action_date', 'comments']
    readonly_fields = ['level', 'action', 'action_by', 'action_date', 'comments']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(ModelAdmin):
    list_display = ['document_number', 'document_type', 'document_amount', 'current_level', 'status', 'requested_by', 'requested_date']
    list_filter = ['document_type', 'status', 'requested_date']
    search_fields = ['document_number', 'requested_by__username']
    readonly_fields = ['document_number', 'document_type', 'document_id', 'document_amount', 'requested_by', 'requested_date']
    inlines = [ApprovalHistoryInline]
    date_hierarchy = 'requested_date'
    
    fieldsets = (
        (_('Document Information'), {
            'fields': (
                ('document_type', 'document_number'),
                ('document_id', 'document_amount'),
            ),
            'classes': ['tab'],
            'description': _('Document details'),
        }),
        (_('Approval Status'), {
            'fields': (
                ('workflow', 'current_level'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Current approval status'),
        }),
        (_('Request Information'), {
            'fields': (
                ('requested_by', 'requested_date'),
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Request details'),
        }),
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    @admin.action(description=_('Approve selected requests'))
    def approve_requests(self, request, queryset):
        for approval_request in queryset.filter(status='pending'):
            ApprovalHistory.objects.create(
                approval_request=approval_request,
                level=approval_request.current_level,
                action='approved',
                action_by=request.user,
                comments='Bulk approved from admin'
            )
            approval_request.status = 'approved'
            approval_request.save()
        self.message_user(request, f'{queryset.count()} request(s) approved.')
    
    @admin.action(description=_('Reject selected requests'))
    def reject_requests(self, request, queryset):
        for approval_request in queryset.filter(status='pending'):
            ApprovalHistory.objects.create(
                approval_request=approval_request,
                level=approval_request.current_level,
                action='rejected',
                action_by=request.user,
                comments='Bulk rejected from admin'
            )
            approval_request.status = 'rejected'
            approval_request.save()
        self.message_user(request, f'{queryset.count()} request(s) rejected.')


@admin.register(ApprovalHistory)
class ApprovalHistoryAdmin(ModelAdmin):
    list_display = ['approval_request', 'level', 'action', 'action_by', 'action_date']
    list_filter = ['action', 'action_date']
    search_fields = ['approval_request__document_number', 'action_by__username']
    readonly_fields = ['approval_request', 'level', 'action', 'action_by', 'action_date', 'comments']
    date_hierarchy = 'action_date'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_module_permission(self, request):
        return False


# ==================== NOTIFICATION / ALERT ADMIN ====================

@admin.register(NotificationType)
class NotificationTypeAdmin(ModelAdmin):
    list_display = ['code', 'name', 'trigger', 'channel', 'is_active']
    list_filter = ['trigger', 'channel', 'is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('code', 'name'),
                ('trigger', 'channel'),
            ),
            'classes': ['tab'],
            'description': _('Notification type identification'),
        }),
        (_('Templates'), {
            'fields': (
                ('subject_template',),
                ('message_template',),
            ),
            'classes': ['tab'],
            'description': _('Message templates'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Notification type status'),
        }),
    )


@admin.register(NotificationSetting)
class NotificationSettingAdmin(ModelAdmin):
    list_display = ['user', 'notification_type', 'is_enabled', 'email_enabled', 'sms_enabled']
    list_filter = ['notification_type', 'is_enabled', 'email_enabled', 'sms_enabled']
    search_fields = ['user__username', 'notification_type__name']
    list_editable = ['is_enabled', 'email_enabled', 'sms_enabled']
    
    fieldsets = (
        (_('User & Notification'), {
            'fields': (
                ('user', 'notification_type'),
            ),
            'classes': ['tab'],
            'description': _('User and notification type'),
        }),
        (_('Settings'), {
            'fields': (
                ('is_enabled',),
                ('email_enabled', 'sms_enabled'),
            ),
            'classes': ['tab'],
            'description': _('Notification preferences'),
        }),
    )


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'priority', 'status', 'email_sent', 'sms_sent', 'created_at']
    list_filter = ['priority', 'status', 'notification_type', 'email_sent', 'sms_sent', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Recipient'), {
            'fields': (
                ('user', 'notification_type'),
            ),
            'classes': ['tab'],
            'description': _('Notification recipient'),
        }),
        (_('Content'), {
            'fields': (
                ('title',),
                ('message',),
                ('priority',),
            ),
            'classes': ['tab'],
            'description': _('Notification content'),
        }),
        (_('Link'), {
            'fields': (
                ('link_url',),
                ('document_type', 'document_id'),
            ),
            'classes': ['tab'],
            'description': _('Related document link'),
        }),
        (_('Status'), {
            'fields': (
                ('status', 'read_at'),
                ('email_sent', 'sms_sent'),
            ),
            'classes': ['tab'],
            'description': _('Delivery status'),
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'send_email']
    
    @admin.action(description=_('Mark as read'))
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='read', read_at=timezone.now())
        self.message_user(request, f'{queryset.count()} notification(s) marked as read.')
    
    @admin.action(description=_('Mark as unread'))
    def mark_as_unread(self, request, queryset):
        queryset.update(status='unread', read_at=None)
        self.message_user(request, f'{queryset.count()} notification(s) marked as unread.')
    
    @admin.action(description=_('Send email notification'))
    def send_email(self, request, queryset):
        # Placeholder for email sending logic
        queryset.update(email_sent=True)
        self.message_user(request, f'{queryset.count()} email(s) sent.')


@admin.register(AlertRule)
class AlertRuleAdmin(ModelAdmin):
    list_display = ['name', 'notification_type', 'condition_type', 'threshold_value', 'is_active', 'last_triggered']
    list_filter = ['condition_type', 'is_active', 'notification_type']
    search_fields = ['name', 'notification_type__name']
    list_editable = ['is_active']
    filter_horizontal = ['notify_users']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'notification_type'),
            ),
            'classes': ['tab'],
            'description': _('Alert rule identification'),
        }),
        (_('Condition'), {
            'fields': (
                ('condition_type', 'threshold_value'),
            ),
            'classes': ['tab'],
            'description': _('Alert trigger condition'),
        }),
        (_('Filters'), {
            'fields': (
                ('product', 'category'),
                ('customer',),
            ),
            'classes': ['tab'],
            'description': _('Optional filters'),
        }),
        (_('Recipients'), {
            'fields': (
                ('notify_users',),
            ),
            'classes': ['tab'],
            'description': _('Users to notify'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active', 'last_triggered'),
            ),
            'classes': ['tab'],
            'description': _('Rule status'),
        }),
    )


# ==================== PAYMENT METHOD ADMIN ====================

from .models import PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(ModelAdmin):
    list_display = ['name', 'code', 'payment_type', 'account_number', 'is_active']
    list_filter = ['payment_type', 'is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'code'),
                ('payment_type',),
            ),
            'classes': ['tab'],
        }),
        (_('Account Details'), {
            'fields': (
                ('account_number', 'account_name'),
            ),
            'classes': ['tab'],
            'description': _('For mobile/bank payments'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
        }),
    )


# ==================== QUICK SALE (SIMPLIFIED POS) ====================

from .models import UserProfile, QuickSale, QuickSaleItem, POSSession, POSReturn, POSReturnItem, ShippingArea


class QuickSaleItemInline(TabularInline):
    model = QuickSaleItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'discount_amount', 'line_total']
    readonly_fields = ['line_total']
    autocomplete_fields = ['product']




class POSReturnItemInline(TabularInline):
    """POS Return Item Inline"""
    model = POSReturnItem
    extra = 1
    fields = ['original_item', 'product', 'quantity', 'refund_amount', 'restock']
    readonly_fields = ['refund_amount', 'product']
    raw_id_fields = ['original_item']


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ['user', 'default_customer', 'branch', 'allow_discount', 'max_discount_percent', 'can_access_all_branches']
    list_filter = ['allow_discount', 'branch', 'can_access_all_branches']
    search_fields = ['user__username', 'user__first_name', 'default_customer__name']
    
    fieldsets = (
        (_('User'), {
            'fields': (
                ('user',),
            ),
            'classes': ['tab'],
        }),
        (_('Branch & Default Settings'), {
            'fields': (
                ('branch',),
                ('default_customer',),
                ('can_access_all_branches',),
            ),
            'classes': ['tab'],
            'description': _('Branch assignment and default settings for this user'),
        }),
        (_('Permissions'), {
            'fields': (
                ('allow_discount', 'max_discount_percent'),
            ),
            'classes': ['tab'],
        }),
    )


# ==================== SHIPPING AREA ADMIN ====================

@admin.register(ShippingArea)
class ShippingAreaAdmin(ModelAdmin):
    """Shipping Area Admin"""
    list_display = ['area_name', 'shipping_charge', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['area_name']
    
    fieldsets = (
        (_('Area Information'), {
            'fields': (
                'area_name',
                'shipping_charge',
                'is_active',
            ),
        }),
    )


# ==================== QUICK SALE (POS) ADMIN ====================

@admin.register(QuickSale)
class QuickSaleAdmin(BranchFilteredAdmin):
    list_display = ['sale_number', 'sale_date', 'user', 'display_customer', 'total_amount', 'due_amount', 'payment_method', 'status', 'action_buttons', 'created_at']
    list_filter = ['status', 'payment_method', 'sale_date', 'user', 'branch', 'session', 'shipping_area']
    search_fields = ['sale_number', 'customer_name', 'customer_phone', 'customer__name']
    readonly_fields = ['sale_number', 'tax_amount', 'balance_due']
    inlines = [QuickSaleItemInline]
    date_hierarchy = 'sale_date'
    actions = ['complete_sales']
    autocomplete_fields = ['customer', 'branch', 'session', 'shipping_area', 'payment_method']
    
    def add_view(self, request, form_url='', extra_context=None):
        """Redirect to Modern POS interface for creating new sales"""
        from django.shortcuts import redirect
        return redirect('erp:modern-pos')
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Redirect to Modern POS interface for editing sales"""
        from django.shortcuts import redirect
        return redirect('erp:modern-pos-edit', sale_id=object_id)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'user', 'branch').prefetch_related('items__product')
    
    fieldsets = (
        (_('Customer & Payment'), {
            'fields': (
                ('customer', 'customer_name'),
                ('customer_phone', 'payment_method'),
            ),
            'classes': ['tab'],
        }),
        (_('Amounts'), {
            'fields': (
                ('subtotal', 'discount_amount'),
                ('tax_percentage', 'tax_amount'),
                ('shipping_area', 'shipping_charge'),
                ('total_amount',),
                ('amount_received', 'change_amount'),
                ('due_amount', 'balance_due'),
            ),
            'classes': ['tab'],
        }),
        (_('Additional Details'), {
            'fields': (
                ('sale_number', 'sale_date'),
                ('branch', 'user'),
                ('session', 'status'),
                ('notes',),
            ),
            'classes': ['tab'],
        }),
    )
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        print_url = reverse('erp:print-quick-sale', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="background: #1976d2; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">🖨️ Print</a>',
            print_url
        )
    
    def get_changeform_initial_data(self, request):
        """Pre-fill user and defaults from profile"""
        initial = super().get_changeform_initial_data(request)
        initial['user'] = request.user.pk
        
        # Get defaults from user profile
        try:
            profile = request.user.profile
            if profile.branch:
                initial['branch'] = profile.branch.pk
            if profile.default_customer:
                initial['customer'] = profile.default_customer.pk
        except UserProfile.DoesNotExist:
            # Use first active warehouse
            first_warehouse = Warehouse.objects.filter(is_active=True).first()
            if first_warehouse:
                initial['branch'] = first_warehouse.pk
        
        return initial
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.user = request.user
        
        # Validate payment before completing
        if change and 'status' in form.changed_data and obj.status == 'completed':
            old_obj = QuickSale.objects.get(pk=obj.pk)
            if old_obj.status == 'draft':
                if obj.amount_received < obj.total_amount:
                    from django.contrib import messages
                    messages.error(request, f'Amount received ({obj.amount_received}) is less than total ({obj.total_amount})')
                    obj.status = 'draft'  # Revert status
        
        super().save_model(request, obj, form, change)
    
    @display(description=_('Customer'))
    def display_customer(self, obj):
        if obj.customer:
            return obj.customer.name
        elif obj.customer_name:
            return f"{obj.customer_name}"
        return "Walk-in"
    
    @admin.action(description=_('Complete selected sales'))
    def complete_sales(self, request, queryset):
        completed = 0
        errors = []
        for sale in queryset.filter(status='draft'):
            # Validate payment
            if sale.amount_received < sale.total_amount:
                errors.append(f"{sale.sale_number}: Amount received is less than total")
                continue
            
            # Change status - signal will handle stock deduction
            sale.status = 'completed'
            sale.change_amount = sale.amount_received - sale.total_amount
            sale.save()
            completed += 1
        
        if completed:
            self.message_user(request, f'{completed} sale(s) completed successfully.')
        if errors:
            self.message_user(request, f'Errors: {", ".join(errors)}', level='error')


# ==================== POS SESSION MANAGEMENT ====================

@admin.register(POSSession)
class POSSessionAdmin(ModelAdmin):
    """POS Session Admin - Cashier session management"""
    list_display = ['session_number', 'cashier', 'branch', 'opened_at', 'closed_at', 'status', 'opening_cash', 'closing_cash', 'cash_difference_display', 'total_sales_display', 'total_transactions_display']
    list_filter = ['status', 'cashier', 'branch', 'opened_at']
    search_fields = ['session_number', 'cashier__username', 'cashier__first_name', 'cashier__last_name']
    readonly_fields = ['session_number', 'expected_cash', 'cash_difference', 'opened_at', 'closed_at', 'total_sales_display', 'total_transactions_display', 'total_cash_sales_display', 'current_expected_cash_display']
    date_hierarchy = 'opened_at'
    actions = ['close_sessions']
    autocomplete_fields = ['cashier', 'branch']
    
    fieldsets = (
        (_('Session Information'), {
            'fields': (
                ('session_number', 'status'),
                ('cashier', 'branch'),
                ('opened_at', 'closed_at'),
            ),
            'classes': ['tab'],
        }),
        (_('Cash Management'), {
            'fields': (
                ('opening_cash', 'total_cash_sales_display'),
                ('current_expected_cash_display', 'closing_cash'),
                ('expected_cash', 'cash_difference'),
                ('total_sales_display', 'total_transactions_display'),
            ),
            'classes': ['tab'],
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ['tab'],
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cashier', 'branch')
    
    @display(description=_('Total Sales'))
    def total_sales_display(self, obj):
        return f"৳{obj.total_sales:,.2f}"
    
    @display(description=_('Total Transactions'))
    def total_transactions_display(self, obj):
        return obj.total_transactions
    
    @display(description=_('Total Cash Sales'))
    def total_cash_sales_display(self, obj):
        return f"৳{obj.total_cash_sales:,.2f}"
    
    @display(description=_('Current Expected Cash'))
    def current_expected_cash_display(self, obj):
        return f"৳{obj.current_expected_cash:,.2f}"
    
    @display(description=_('Cash Difference'))
    def cash_difference_display(self, obj):
        diff = obj.cash_difference
        if diff == 0:
            return f"৳0.00 ✓"
        elif diff > 0:
            return f"+৳{diff:,.2f} (Over)"
        else:
            return f"-৳{abs(diff):,.2f} (Short)"
    
    @admin.action(description=_('Close selected sessions'))
    def close_sessions(self, request, queryset):
        """Close open sessions"""
        closed = 0
        for session in queryset.filter(status='open'):
            # Auto-calculate closing cash from current expected
            session.close_session(session.current_expected_cash)
            closed += 1
        
        if closed:
            self.message_user(request, f'{closed} session(s) closed successfully.')





@admin.register(POSReturn)
class POSReturnAdmin(ModelAdmin):
    """POS Return Admin - Return/refund management"""
    list_display = ['return_number', 'original_sale', 'return_datetime', 'cashier', 'total_refund', 'refund_method', 'status', 'created_at']
    list_filter = ['status', 'refund_method', 'return_datetime', 'cashier']
    search_fields = ['return_number', 'original_sale__sale_number']
    readonly_fields = ['return_number', 'total_refund', 'created_at']
    inlines = [POSReturnItemInline]
    date_hierarchy = 'return_datetime'
    actions = ['complete_returns']
    autocomplete_fields = ['original_sale', 'branch', 'cashier']
    
    fieldsets = (
        (_('Return Information'), {
            'fields': (
                ('return_number', 'original_sale'),
                ('return_datetime', 'cashier'),
                ('branch', 'status'),
            ),
            'classes': ['tab'],
        }),
        (_('Refund Details'), {
            'fields': (
                ('refund_method', 'total_refund'),
                ('reason',),
            ),
            'classes': ['tab'],
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('original_sale', 'cashier', 'branch')
    
    @admin.action(description=_('Complete selected returns'))
    def complete_returns(self, request, queryset):
        """Complete pending returns"""
        completed = 0
        for ret in queryset.filter(status='completed'):
            ret.process_return()
            completed += 1
        
        if completed:
            self.message_user(request, f'{completed} return(s) processed successfully.')


@admin.register(POSReturnItem)
class POSReturnItemAdmin(ModelAdmin):
    """POS Return Item Admin"""
    list_display = ['pos_return', 'product', 'variant', 'quantity', 'refund_amount', 'restock']
    list_filter = ['restock', 'created_at']
    search_fields = ['pos_return__return_number', 'product__name']
    readonly_fields = ['refund_amount', 'created_at']
    autocomplete_fields = ['pos_return', 'product']
    raw_id_fields = ['original_item']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pos_return', 'product', 'variant')



# ==================== QUALITY CONTROL & SERVICE MANAGEMENT ====================

@admin.register(QualityCheckType)
class QualityCheckTypeAdmin(ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']
    list_per_page = 50
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'code'),
            ),
            'classes': ['tab'],
            'description': _('Quality check type identification'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Quality check type status'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)


class QualityDefectInline(TabularInline):
    model = QualityDefect
    extra = 1
    fields = ['defect_type', 'product', 'quantity', 'location', 'description']
    autocomplete_fields = ['defect_type', 'product']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('defect_type', 'product')


@admin.register(QualityCheck)
class QualityCheckAdmin(BranchFilteredAdmin):
    list_display = ['check_number', 'branch', 'check_date', 'check_type', 'inspector', 'sample_size', 'passed_quantity', 'failed_quantity', 'status']
    list_filter = ['status', 'check_type', 'check_date', 'inspector', 'branch']
    search_fields = ['check_number', 'inspector']
    list_select_related = ['check_type', 'goods_receipt', 'production_receipt', 'sales_order']
    autocomplete_fields = ['check_type', 'goods_receipt', 'production_receipt', 'sales_order']
    readonly_fields = ['check_number', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'check_date'
    inlines = [QualityDefectInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('check_number', 'check_date'),
                ('check_type', 'inspector'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Quality check identification and inspector'),
        }),
        (_('Reference Documents'), {
            'fields': (
                ('goods_receipt',),
                ('production_receipt',),
                ('sales_order',),
            ),
            'classes': ['tab'],
            'description': _('Related documents for this quality check'),
        }),
        (_('Check Details'), {
            'fields': (
                ('sample_size',),
                ('passed_quantity', 'failed_quantity'),
            ),
            'classes': ['tab'],
            'description': _('Inspection quantities and results'),
        }),
        (_('Results & Remarks'), {
            'fields': (
                ('result',),
                ('remarks',),
            ),
            'classes': ['tab'],
            'description': _('Quality check outcome and notes'),
        }),
        (_('Timestamps'), {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab', 'collapse'],
            'description': _('Record timestamps'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'check_type', 'goods_receipt', 'production_receipt', 'sales_order'
        ).prefetch_related('defects')


@admin.register(DefectType)
class DefectTypeAdmin(ModelAdmin):
    list_display = ['name', 'code', 'severity', 'is_active']
    list_filter = ['severity', 'is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']
    list_per_page = 50
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'code'),
                ('severity',),
            ),
            'classes': ['tab'],
            'description': _('Defect type identification and severity level'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Defect type status'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(QualityDefect)
class QualityDefectAdmin(BranchFilteredAdmin):
    list_display = ['quality_check', 'branch', 'defect_type', 'product', 'quantity', 'location']
    list_filter = ['defect_type', 'defect_type__severity', 'branch']
    search_fields = ['quality_check__check_number', 'defect_type__name', 'product__name']
    list_select_related = ['quality_check', 'defect_type', 'product']
    autocomplete_fields = ['quality_check', 'defect_type', 'product']
    list_per_page = 50
    
    fieldsets = (
        (_('Quality Check'), {
            'fields': (
                ('quality_check',),
            ),
            'classes': ['tab'],
            'description': _('Related quality check'),
        }),
        (_('Defect Details'), {
            'fields': (
                ('defect_type', 'product'),
                ('quantity', 'location'),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Defect information and location'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('quality_check', 'defect_type', 'product')


@admin.register(ServiceType)
class ServiceTypeAdmin(ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']
    list_per_page = 50
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'code'),
            ),
            'classes': ['tab'],
            'description': _('Service type identification'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Service type status'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(BranchFilteredAdmin):
    list_display = ['ticket_number', 'branch', 'request_date', 'service_type', 'customer', 'subject', 'priority', 'status', 'assigned_to']
    list_filter = ['status', 'priority', 'service_type', 'request_date', 'branch']
    search_fields = ['ticket_number', 'subject', 'customer__name', 'contact_person']
    list_select_related = ['service_type', 'customer', 'sales_order', 'invoice']
    autocomplete_fields = ['service_type', 'customer', 'sales_order', 'invoice']
    readonly_fields = ['ticket_number', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'request_date'
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('ticket_number', 'request_date'),
                ('service_type', 'priority'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Service request identification and priority'),
        }),
        (_('Customer Information'), {
            'fields': (
                ('customer',),
                ('contact_person',),
                ('contact_phone', 'contact_email'),
            ),
            'classes': ['tab'],
            'description': _('Customer and contact details'),
        }),
        (_('Request Details'), {
            'fields': (
                ('subject',),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Service request description'),
        }),
        (_('Reference Documents'), {
            'fields': (
                ('sales_order', 'invoice'),
            ),
            'classes': ['tab'],
            'description': _('Related sales documents'),
        }),
        (_('Assignment'), {
            'fields': (
                ('assigned_to', 'assigned_date'),
            ),
            'classes': ['tab'],
            'description': _('Service assignment information'),
        }),
        (_('Resolution'), {
            'fields': (
                ('resolution',),
                ('resolved_date', 'closed_date'),
            ),
            'classes': ['tab'],
            'description': _('Resolution details and dates'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('remarks',),
            ),
            'classes': ['tab'],
            'description': _('Additional notes'),
        }),
        (_('Timestamps'), {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab', 'collapse'],
            'description': _('Record timestamps'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('service_type', 'customer', 'sales_order', 'invoice')


@admin.register(ComplaintType)
class ComplaintTypeAdmin(ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']
    list_per_page = 50
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'code'),
            ),
            'classes': ['tab'],
            'description': _('Complaint type identification'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Complaint type status'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(Complaint)
class ComplaintAdmin(BranchFilteredAdmin):
    list_display = ['complaint_number', 'branch', 'complaint_date', 'complaint_type', 'customer', 'subject', 'severity', 'status', 'investigated_by']
    list_filter = ['status', 'severity', 'complaint_type', 'complaint_date', 'branch']
    search_fields = ['complaint_number', 'subject', 'customer__name', 'contact_person']
    list_select_related = ['complaint_type', 'customer', 'sales_order', 'invoice', 'product']
    autocomplete_fields = ['complaint_type', 'customer', 'sales_order', 'invoice', 'product']
    readonly_fields = ['complaint_number', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'complaint_date'
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('complaint_number', 'complaint_date'),
                ('complaint_type', 'severity'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Complaint identification and severity'),
        }),
        (_('Customer Information'), {
            'fields': (
                ('customer',),
                ('contact_person', 'contact_phone'),
            ),
            'classes': ['tab'],
            'description': _('Customer and contact details'),
        }),
        (_('Complaint Details'), {
            'fields': (
                ('subject',),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Complaint description'),
        }),
        (_('Reference Documents'), {
            'fields': (
                ('sales_order', 'invoice'),
                ('product',),
            ),
            'classes': ['tab'],
            'description': _('Related sales documents and product'),
        }),
        (_('Investigation'), {
            'fields': (
                ('investigated_by',),
                ('investigation_notes',),
                ('root_cause',),
            ),
            'classes': ['tab'],
            'description': _('Investigation details and root cause analysis'),
        }),
        (_('Resolution'), {
            'fields': (
                ('corrective_action',),
                ('preventive_action',),
                ('resolution_date', 'closed_date'),
            ),
            'classes': ['tab'],
            'description': _('Corrective and preventive actions'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('remarks',),
            ),
            'classes': ['tab'],
            'description': _('Additional notes'),
        }),
        (_('Timestamps'), {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab', 'collapse'],
            'description': _('Record timestamps'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('complaint_type', 'customer', 'sales_order', 'invoice', 'product')



# ==================== FIXED ASSETS MANAGEMENT ====================

@admin.register(AssetCategory)
class AssetCategoryAdmin(ModelAdmin):
    list_display = ['code', 'name', 'parent_category', 'default_depreciation_method', 'default_useful_life_years', 'is_active']
    list_filter = ['is_active', 'default_depreciation_method']
    search_fields = ['name', 'code']
    list_editable = ['is_active']
    autocomplete_fields = ['parent_category', 'asset_account', 'depreciation_account', 'accumulated_depreciation_account']
    list_per_page = 50
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name', 'code'),
                ('parent_category',),
            ),
            'classes': ['tab'],
            'description': _('Asset category identification'),
        }),
        (_('Accounting Integration'), {
            'fields': (
                ('asset_account',),
                ('depreciation_account',),
                ('accumulated_depreciation_account',),
            ),
            'classes': ['tab'],
            'description': _('GL accounts for asset transactions'),
        }),
        (_('Default Depreciation Settings'), {
            'fields': (
                ('default_depreciation_method',),
                ('default_useful_life_years', 'default_salvage_value_percentage'),
            ),
            'classes': ['tab'],
            'description': _('Default settings for new assets'),
        }),
        (_('Additional Details'), {
            'fields': (
                ('description',),
                ('is_active',),
            ),
            'classes': ['tab'],
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent_category', 'asset_account', 'depreciation_account', 'accumulated_depreciation_account')


class AssetDepreciationInline(TabularInline):
    model = AssetDepreciation
    extra = 0
    fields = ['depreciation_date', 'period_start', 'period_end', 'depreciation_amount', 'accumulated_depreciation', 'book_value', 'is_posted']
    readonly_fields = ['accumulated_depreciation', 'book_value']
    can_delete = False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('journal_entry')


@admin.register(FixedAsset)
class FixedAssetAdmin(BranchFilteredAdmin):
    list_display = ['asset_number', 'branch', 'asset_name', 'category', 'purchase_date', 'purchase_cost', 'book_value', 'status', 'location']
    list_filter = ['status', 'category', 'purchase_date', 'location', 'branch']
    search_fields = ['asset_number', 'asset_name', 'serial_number', 'model_number']
    readonly_fields = ['asset_number', 'accumulated_depreciation', 'book_value', 'created_at', 'updated_at']
    autocomplete_fields = ['category', 'supplier', 'purchase_invoice', 'branch']
    list_per_page = 50
    date_hierarchy = 'purchase_date'
    inlines = [AssetDepreciationInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('asset_number', 'asset_name'),
                ('category', 'status'),
            ),
            'classes': ['tab'],
            'description': _('Asset identification'),
        }),
        (_('Purchase Details'), {
            'fields': (
                ('purchase_date', 'purchase_cost'),
                ('supplier', 'purchase_invoice'),
            ),
            'classes': ['tab'],
            'description': _('Purchase information'),
        }),
        (_('Depreciation Settings'), {
            'fields': (
                ('depreciation_method', 'useful_life_years'),
                ('salvage_value', 'depreciation_start_date'),
                ('accumulated_depreciation', 'book_value'),
            ),
            'classes': ['tab'],
            'description': _('Depreciation configuration and current values'),
        }),
        (_('Location & Assignment'), {
            'fields': (
                ('location', 'department'),
                ('assigned_to',),
            ),
            'classes': ['tab'],
            'description': _('Asset location and assignment'),
        }),
        (_('Additional Information'), {
            'fields': (
                ('serial_number', 'model_number'),
                ('manufacturer', 'warranty_expiry_date'),
                ('notes',),
            ),
            'classes': ['tab'],
        }),
        (_('Timestamps'), {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab', 'collapse'],
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'supplier', 'purchase_invoice')


@admin.register(AssetDepreciation)
class AssetDepreciationAdmin(BranchFilteredAdmin):
    list_display = ['asset', 'branch', 'depreciation_date', 'period_start', 'period_end', 'depreciation_amount', 'book_value', 'is_posted']
    list_filter = ['is_posted', 'depreciation_date', 'branch']
    search_fields = ['asset__asset_number', 'asset__asset_name']
    readonly_fields = ['accumulated_depreciation', 'book_value']
    autocomplete_fields = ['asset', 'journal_entry']
    list_per_page = 50
    date_hierarchy = 'depreciation_date'
    
    fieldsets = (
        (_('Asset & Period'), {
            'fields': (
                ('asset',),
                ('depreciation_date',),
                ('period_start', 'period_end'),
            ),
            'classes': ['tab'],
        }),
        (_('Depreciation Details'), {
            'fields': (
                ('depreciation_amount',),
                ('accumulated_depreciation', 'book_value'),
            ),
            'classes': ['tab'],
        }),
        (_('Accounting'), {
            'fields': (
                ('journal_entry', 'is_posted'),
            ),
            'classes': ['tab'],
        }),
        (_('Notes'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('asset', 'asset__category', 'journal_entry')


@admin.register(AssetTransfer)
class AssetTransferAdmin(BranchFilteredAdmin):
    list_display = ['transfer_number', 'branch', 'transfer_date', 'asset', 'from_location', 'to_location', 'approved_by']
    list_filter = ['transfer_date', 'from_location', 'to_location', 'branch']
    search_fields = ['transfer_number', 'asset__asset_number', 'asset__asset_name']
    readonly_fields = ['transfer_number', 'created_at', 'updated_at']
    autocomplete_fields = ['asset', 'branch']
    list_per_page = 50
    date_hierarchy = 'transfer_date'
    
    fieldsets = (
        (_('Transfer Information'), {
            'fields': (
                ('transfer_number', 'transfer_date'),
                ('asset',),
            ),
            'classes': ['tab'],
        }),
        (_('From'), {
            'fields': (
                ('from_location', 'from_department'),
                ('from_assigned_to',),
            ),
            'classes': ['tab'],
        }),
        (_('To'), {
            'fields': (
                ('to_location', 'to_department'),
                ('to_assigned_to',),
            ),
            'classes': ['tab'],
        }),
        (_('Approval & Notes'), {
            'fields': (
                ('transfer_reason',),
                ('approved_by',),
                ('notes',),
            ),
            'classes': ['tab'],
        }),
        (_('Timestamps'), {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab', 'collapse'],
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('asset', 'asset__category')


@admin.register(AssetDisposal)
class AssetDisposalAdmin(BranchFilteredAdmin):
    list_display = ['disposal_number', 'branch', 'disposal_date', 'asset', 'disposal_type', 'disposal_value', 'gain_loss', 'is_posted']
    list_filter = ['disposal_type', 'is_posted', 'disposal_date', 'branch']
    search_fields = ['disposal_number', 'asset__asset_number', 'asset__asset_name', 'buyer_name']
    readonly_fields = ['disposal_number', 'gain_loss', 'created_at', 'updated_at']
    autocomplete_fields = ['asset', 'journal_entry', 'branch']
    list_per_page = 50
    date_hierarchy = 'disposal_date'
    
    fieldsets = (
        (_('Disposal Information'), {
            'fields': (
                ('disposal_number', 'disposal_date'),
                ('asset', 'disposal_type'),
            ),
            'classes': ['tab'],
        }),
        (_('Financial Details'), {
            'fields': (
                ('disposal_value', 'book_value_at_disposal'),
                ('gain_loss',),
            ),
            'classes': ['tab'],
            'description': _('Disposal value and gain/loss calculation'),
        }),
        (_('Buyer/Recipient Information'), {
            'fields': (
                ('buyer_name', 'buyer_contact'),
            ),
            'classes': ['tab'],
        }),
        (_('Accounting'), {
            'fields': (
                ('journal_entry', 'is_posted'),
            ),
            'classes': ['tab'],
        }),
        (_('Approval & Notes'), {
            'fields': (
                ('disposal_reason',),
                ('approved_by',),
                ('notes',),
            ),
            'classes': ['tab'],
        }),
        (_('Timestamps'), {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab', 'collapse'],
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('asset', 'asset__category', 'journal_entry')


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(BranchFilteredAdmin):
    list_display = ['maintenance_number', 'branch', 'maintenance_date', 'asset', 'maintenance_type', 'total_cost', 'downtime_hours', 'next_maintenance_date']
    list_filter = ['maintenance_type', 'maintenance_date', 'branch']
    search_fields = ['maintenance_number', 'asset__asset_number', 'asset__asset_name', 'service_provider']
    readonly_fields = ['maintenance_number', 'total_cost', 'created_at', 'updated_at']
    autocomplete_fields = ['asset', 'branch']
    list_per_page = 50
    date_hierarchy = 'maintenance_date'
    
    fieldsets = (
        (_('Maintenance Information'), {
            'fields': (
                ('maintenance_number', 'maintenance_date'),
                ('asset', 'maintenance_type'),
                ('description',),
            ),
            'classes': ['tab'],
        }),
        (_('Service Provider'), {
            'fields': (
                ('service_provider', 'technician_name'),
            ),
            'classes': ['tab'],
        }),
        (_('Cost Details'), {
            'fields': (
                ('labor_cost', 'parts_cost'),
                ('other_cost', 'total_cost'),
            ),
            'classes': ['tab'],
        }),
        (_('Downtime & Next Maintenance'), {
            'fields': (
                ('downtime_hours', 'next_maintenance_date'),
            ),
            'classes': ['tab'],
        }),
        (_('Notes'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
        }),
        (_('Timestamps'), {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab', 'collapse'],
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('asset', 'asset__category')


# ==================== BANK RECONCILIATION ====================

@admin.register(BankStatement)
class BankStatementAdmin(BranchFilteredAdmin):
    list_display = ['statement_number', 'branch', 'bank_account', 'statement_date', 'period_start', 'period_end', 'opening_balance', 'closing_balance']
    list_filter = ['statement_date', 'bank_account', 'branch']
    search_fields = ['statement_number', 'bank_account__account_name', 'file_name']
    readonly_fields = ['statement_number', 'import_date', 'created_at', 'updated_at']
    autocomplete_fields = ['bank_account']
    list_per_page = 50
    date_hierarchy = 'statement_date'
    
    fieldsets = (
        (_('Statement Information'), {
            'fields': (
                ('statement_number', 'statement_date'),
                ('bank_account',),
                ('period_start', 'period_end'),
            ),
            'classes': ['tab'],
        }),
        (_('Balances'), {
            'fields': (
                ('opening_balance', 'closing_balance'),
            ),
            'classes': ['tab'],
        }),
        (_('Import Details'), {
            'fields': (
                ('import_date', 'imported_by'),
                ('file_name',),
            ),
            'classes': ['tab'],
        }),
        (_('Notes'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
        }),
        (_('Timestamps'), {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab', 'collapse'],
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bank_account')


class UnreconciledTransactionInline(TabularInline):
    model = UnreconciledTransaction
    extra = 1
    fields = ['transaction_date', 'transaction_type', 'reference_number', 'description', 'amount', 'is_reconciled']
    autocomplete_fields = ['incoming_payment', 'outgoing_payment']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('incoming_payment', 'outgoing_payment')


@admin.register(BankReconciliation)
class BankReconciliationAdmin(BranchFilteredAdmin):
    list_display = ['reconciliation_number', 'branch', 'bank_statement', 'reconciliation_date', 'bank_statement_balance', 'book_balance', 'difference', 'status']
    list_filter = ['status', 'reconciliation_date', 'branch']
    search_fields = ['reconciliation_number', 'bank_statement__statement_number', 'bank_statement__bank_account__account_name']
    readonly_fields = ['reconciliation_number', 'difference', 'created_at', 'updated_at']
    autocomplete_fields = ['bank_statement']
    list_per_page = 50
    date_hierarchy = 'reconciliation_date'
    inlines = [UnreconciledTransactionInline]
    
    fieldsets = (
        (_('Reconciliation Information'), {
            'fields': (
                ('reconciliation_number', 'reconciliation_date'),
                ('bank_statement', 'status'),
            ),
            'classes': ['tab'],
        }),
        (_('Balances'), {
            'fields': (
                ('bank_statement_balance', 'book_balance'),
                ('difference',),
            ),
            'classes': ['tab'],
            'description': _('Bank and book balances comparison'),
        }),
        (_('Reconciliation Items'), {
            'fields': (
                ('outstanding_deposits', 'outstanding_cheques'),
                ('bank_charges', 'bank_interest'),
            ),
            'classes': ['tab'],
            'description': _('Outstanding items and adjustments'),
        }),
        (_('Approval'), {
            'fields': (
                ('reconciled_by', 'approved_by'),
            ),
            'classes': ['tab'],
        }),
        (_('Notes'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
        }),
        (_('Timestamps'), {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab', 'collapse'],
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bank_statement', 'bank_statement__bank_account')


@admin.register(UnreconciledTransaction)
class UnreconciledTransactionAdmin(ModelAdmin):
    list_display = ['bank_reconciliation', 'transaction_date', 'transaction_type', 'reference_number', 'amount', 'is_reconciled']
    list_filter = ['transaction_type', 'is_reconciled', 'transaction_date']
    search_fields = ['reference_number', 'description', 'bank_reconciliation__reconciliation_number']
    autocomplete_fields = ['bank_reconciliation', 'incoming_payment', 'outgoing_payment']
    list_per_page = 50
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        (_('Transaction Information'), {
            'fields': (
                ('bank_reconciliation',),
                ('transaction_date', 'transaction_type'),
                ('reference_number',),
                ('description', 'amount'),
            ),
            'classes': ['tab'],
        }),
        (_('System Links'), {
            'fields': (
                ('incoming_payment', 'outgoing_payment'),
            ),
            'classes': ['tab'],
            'description': _('Link to system payment transactions'),
        }),
        (_('Reconciliation Status'), {
            'fields': (
                ('is_reconciled', 'reconciled_date'),
            ),
            'classes': ['tab'],
        }),
        (_('Notes'), {
            'fields': (
                ('notes',),
            ),
            'classes': ['tab'],
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bank_reconciliation', 'bank_reconciliation__bank_statement', 'incoming_payment', 'outgoing_payment')


# ==================== SIMPLE EXPENSE SYSTEM ====================

from .models import ExpenseCategory, SimpleExpense


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(BranchFilteredAdmin):
    list_display = ['name', 'branch', 'default_account', 'is_active', 'created_at']
    list_filter = ['is_active', 'branch', 'default_account__account_type']
    search_fields = ['name', 'description', 'default_account__account_name']
    list_editable = ['is_active']
    autocomplete_fields = ['default_account']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('name',),
                ('default_account',),
                ('description',),
            ),
            'classes': ['tab'],
            'description': _('Expense category identification and default account'),
        }),
        (_('Status'), {
            'fields': (
                ('is_active',),
            ),
            'classes': ['tab'],
            'description': _('Category status'),
        }),
    )


@admin.register(SimpleExpense)
class SimpleExpenseAdmin(BranchFilteredAdmin):
    list_display = ['expense_number', 'branch', 'expense_date', 'category', 'amount', 'status', 'created_by', 'journal_entry_link', 'action_buttons']
    list_filter = ['status', 'category', 'expense_date', 'branch', 'created_by']
    search_fields = ['expense_number', 'description', 'notes', 'category__name']
    readonly_fields = ['expense_number', 'journal_entry', 'created_by']
    date_hierarchy = 'expense_date'
    autocomplete_fields = ['category']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                ('expense_number', 'expense_date'),
                ('category', 'amount'),
                ('status',),
            ),
            'classes': ['tab'],
            'description': _('Required expense information'),
        }),
        (_('Description'), {
            'fields': (
                ('description',),
                ('notes',),
            ),
            'classes': ['tab'],
            'description': _('Expense details'),
        }),
        (_('System Information'), {
            'fields': (
                ('created_by', 'journal_entry'),
            ),
            'classes': ['tab'],
            'description': _('System generated information'),
        }),
    )
    
    actions = ['post_expenses', 'cancel_expenses']
    
    @display(description=_('Journal Entry'))
    def journal_entry_link(self, obj):
        if obj.journal_entry:
            url = reverse('admin:erp_journalentry_change', args=[obj.journal_entry.id])
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.journal_entry.entry_number)
        return "-"
    
    @display(description=_('Actions'), label=True)
    def action_buttons(self, obj):
        if obj.status == 'posted' and obj.journal_entry:
            journal_url = reverse('admin:erp_journalentry_change', args=[obj.journal_entry.id])
            return format_html(
                '<a href="{}" target="_blank" style="background: #4F46E5; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 10px;">📋 View Journal</a>',
                journal_url
            )
        return "-"
    
    def get_changeform_initial_data(self, request):
        """Pre-fill user and branch from profile"""
        initial = super().get_changeform_initial_data(request)
        
        # Get defaults from user profile
        try:
            profile = request.user.profile
            if profile.branch:
                initial['branch'] = profile.branch.pk
        except:
            # Use first active warehouse
            first_warehouse = Warehouse.objects.filter(is_active=True).first()
            if first_warehouse:
                initial['branch'] = first_warehouse.pk
        
        return initial
    
    def save_model(self, request, obj, form, change):
        """Auto-fill created_by on first save"""
        if not change:  # New object
            obj.created_by = request.user
        
        super().save_model(request, obj, form, change)
    
    @admin.action(description=_('✅ Post selected expenses (Create Journal Entries)'))
    def post_expenses(self, request, queryset):
        """Post expenses and create journal entries"""
        count = 0
        errors = []
        
        for expense in queryset.filter(status='draft'):
            try:
                expense.status = 'posted'
                expense.save()  # This will trigger journal entry creation
                count += 1
            except Exception as e:
                errors.append(f"{expense.expense_number}: {str(e)}")
        
        if count:
            self.message_user(request, f'{count} expense(s) posted and journal entries created.')
        if errors:
            self.message_user(request, f'Errors: {", ".join(errors)}', level='error')
    
    @admin.action(description=_('❌ Cancel selected expenses'))
    def cancel_expenses(self, request, queryset):
        """Cancel expenses and reverse journal entries"""
        count = 0
        
        for expense in queryset.filter(status__in=['draft', 'posted']):
            expense.cancel_expense()
            count += 1
        
        self.message_user(request, f'{count} expense(s) cancelled.')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'category', 'created_by', 'journal_entry', 'branch'
        )


# ==================== SIMPLE EXPENSE ENTRY ADMIN ====================


# ==================== ADMIN SITE CONFIGURATION ====================
# Configure admin site for better empty state handling
admin.site.empty_value_display = "---"

# Ensure all admin classes have proper empty state handling
for model, admin_class in admin.site._registry.items():
    if hasattr(admin_class, 'empty_value_display'):
        admin_class.empty_value_display = "---"
    
    # Ensure list_display is set for better empty state
    if not hasattr(admin_class, 'list_display') or not admin_class.list_display:
        # Set a default list_display based on model fields
        model_fields = [f.name for f in model._meta.fields if f.name != 'id'][:5]
        if model_fields:
            admin_class.list_display = model_fields[:3]  # Show first 3 fields