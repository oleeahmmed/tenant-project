"""
Complete Optimized Garments Admin Panel
With select_related, prefetch_related, queryset optimization
"""
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum, Prefetch

from .models import (
    Company, Factory, Size, Color, Season, GarmentType,
    Buyer, BuyerBrand, Merchandiser, Supplier,
    FabricType, Fabric, TrimType, Trim,
    Style, StyleImage, StyleFabric, StyleTrim, StyleCosting,
    BuyerOrder, OrderBreakdown,
    SewingLine, CuttingOrder, CuttingSizeBreakdown, Bundle,
    DefectType, Inspection, InspectionDefect,
    PackingList, Carton, CartonBreakdown,
    TNATemplate, TNATask, TNATemplateTask, OrderTNA, OrderTNATask,
    ComplianceType, FactoryCompliance, TestType, OrderTest,
    ProductionPlan, DailyProduction, FabricReceive, TrimReceive, Shipment,
    # Phase 6: Costing & Pricing Management
    CostingSheet, CostingComponent, PriceList, PriceListItem,
    QuotationCosting, OrderCosting, ProfitAnalysis, CostVariance,
    # Phase 7: Capacity Planning & Scheduling
    CapacityPlan, LineCapacity, ProductionSchedule, ScheduleConflict,
    ResourceAllocation, DowntimeTracking, EfficiencyTracking,
    # Phase 8: Quality Management System
    QualityStandard, InspectionPlan, InspectionCheckpoint, QualityParameter,
    MeasurementRecord, NonConformance, CorrectiveAction, QualityAudit, QualityMetrics,
    # Phase 9: Sample Management
    SampleType, SampleRequest, SampleDevelopment, SampleApproval, SampleComment, SampleCost,
    # Phase 10: Fabric & Trim Inventory
    FabricStock, FabricRoll, FabricIssue, FabricReturn,
    TrimStock, TrimIssue, TrimReturn, MaterialRequisition,
    # Phase 11: Subcontracting Management
    Subcontractor, SubcontractOrder, SubcontractDelivery, SubcontractPayment, SubcontractQuality,
)


# ==================== OPTIMIZED INLINES ====================

class BuyerBrandInline(TabularInline):
    model = BuyerBrand
    extra = 1
    fields = ['brand_name', 'brand_code', 'is_active']
    
    def get_queryset(self, request):
        return super().get_queryset(request).only('brand_name', 'brand_code', 'is_active', 'buyer')


class MerchandiserInline(TabularInline):
    model = Merchandiser
    extra = 1
    fields = ['name', 'email', 'phone', 'designation']


class StyleImageInline(TabularInline):
    model = StyleImage
    extra = 1
    fields = ['image', 'image_type', 'is_primary', 'sort_order']


class StyleFabricInline(TabularInline):
    model = StyleFabric
    extra = 1
    fields = ['fabric', 'consumption_per_piece', 'unit', 'placement']
    autocomplete_fields = ['fabric']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('fabric', 'fabric__fabric_type')


class StyleTrimInline(TabularInline):
    model = StyleTrim
    extra = 1
    fields = ['trim', 'quantity_per_piece', 'placement']
    autocomplete_fields = ['trim']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('trim', 'trim__trim_type')


class OrderBreakdownInline(TabularInline):
    model = OrderBreakdown
    extra = 0
    fields = ['color', 'size', 'quantity', 'unit_price', 'cutting_qty', 'sewing_qty', 'shipped_qty']
    autocomplete_fields = ['color', 'size']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('color', 'size')


class CuttingSizeBreakdownInline(TabularInline):
    model = CuttingSizeBreakdown
    extra = 1
    fields = ['size', 'quantity']
    autocomplete_fields = ['size']


class InspectionDefectInline(TabularInline):
    model = InspectionDefect
    extra = 1
    fields = ['defect_type', 'quantity', 'size', 'color', 'location']
    autocomplete_fields = ['defect_type', 'size', 'color']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('defect_type', 'size', 'color')


class CartonInline(TabularInline):
    model = Carton
    extra = 1
    fields = ['carton_number', 'carton_from', 'carton_to', 'length', 'width', 'height', 'gross_weight', 'total_pieces']


class CartonBreakdownInline(TabularInline):
    model = CartonBreakdown
    extra = 1
    fields = ['color', 'size', 'quantity']
    autocomplete_fields = ['color', 'size']


# ==================== OPTIMIZED FOUNDATION ADMINS ====================

@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    list_display = ['name', 'factory_type', 'city', 'total_workers', 'monthly_capacity', 'phone']
    list_filter = ['factory_type', 'city']
    search_fields = ['name', 'trade_license', 'phone', 'email']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).only(
            'name', 'factory_type', 'city', 'total_workers', 'monthly_capacity', 'phone'
        )


@admin.register(Factory)
class FactoryAdmin(ModelAdmin):
    list_display = ['factory_name', 'factory_code', 'company', 'city', 'number_of_lines', 'daily_capacity', 'is_active']
    list_filter = ['company', 'city', 'is_active']
    search_fields = ['factory_name', 'factory_code', 'manager']
    list_editable = ['is_active']
    list_select_related = ['company']
    autocomplete_fields = ['company']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


@admin.register(Size)
class SizeAdmin(ModelAdmin):
    list_display = ['name', 'code', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['sort_order', 'is_active']
    ordering = ['sort_order']
    list_per_page = 100


@admin.register(Color)
class ColorAdmin(ModelAdmin):
    list_display = ['name', 'code', 'hex_code', 'color_preview', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']
    list_per_page = 100
    
    @display(description=_('Preview'))
    def color_preview(self, obj):
        if obj.hex_code:
            return format_html('<div style="width:30px;height:20px;background:{};border:1px solid #ccc;"></div>', obj.hex_code)
        return '-'


@admin.register(Season)
class SeasonAdmin(ModelAdmin):
    list_display = ['name', 'code', 'year', 'start_date', 'end_date', 'is_active']
    list_filter = ['year', 'is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']
    list_per_page = 50


@admin.register(GarmentType)
class GarmentTypeAdmin(ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']


# ==================== OPTIMIZED BUYER & SUPPLIER ====================

@admin.register(Buyer)
class BuyerAdmin(ModelAdmin):
    list_display = ['buyer_name', 'buyer_code', 'buyer_type', 'country', 'payment_terms', 'lc_required', 'is_active']
    list_filter = ['buyer_type', 'country', 'lc_required', 'is_active']
    search_fields = ['buyer_name', 'buyer_code', 'email']
    list_editable = ['is_active']
    inlines = [BuyerBrandInline, MerchandiserInline]
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            Prefetch('brands', queryset=BuyerBrand.objects.filter(is_active=True)),
            Prefetch('merchandisers', queryset=Merchandiser.objects.filter(is_active=True))
        )


@admin.register(BuyerBrand)
class BuyerBrandAdmin(ModelAdmin):
    list_display = ['brand_name', 'brand_code', 'buyer', 'is_active']
    list_filter = ['buyer', 'is_active']
    search_fields = ['brand_name', 'brand_code', 'buyer__buyer_name']
    list_editable = ['is_active']
    list_select_related = ['buyer']
    autocomplete_fields = ['buyer']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('buyer')


@admin.register(Merchandiser)
class MerchandiserAdmin(ModelAdmin):
    list_display = ['name', 'buyer', 'email', 'phone', 'is_active']
    list_filter = ['buyer', 'is_active']
    search_fields = ['name', 'email', 'phone', 'buyer__buyer_name']
    list_editable = ['is_active']
    list_select_related = ['buyer']
    autocomplete_fields = ['buyer']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('buyer')


@admin.register(Supplier)
class SupplierAdmin(ModelAdmin):
    list_display = ['supplier_name', 'supplier_code', 'supplier_type', 'country', 'payment_terms', 'is_active']
    list_filter = ['supplier_type', 'country', 'is_active']
    search_fields = ['supplier_name', 'supplier_code', 'email']
    list_editable = ['is_active']
    list_per_page = 50


# ==================== OPTIMIZED MATERIALS ====================

@admin.register(FabricType)
class FabricTypeAdmin(ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']


@admin.register(Fabric)
class FabricAdmin(ModelAdmin):
    list_display = ['fabric_name', 'fabric_code', 'fabric_type', 'supplier', 'composition', 'gsm', 'price_per_kg', 'is_active']
    list_filter = ['fabric_type', 'supplier', 'is_active']
    search_fields = ['fabric_name', 'fabric_code', 'composition']
    list_editable = ['is_active']
    list_select_related = ['fabric_type', 'supplier']
    autocomplete_fields = ['fabric_type', 'supplier']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('fabric_type', 'supplier')


@admin.register(TrimType)
class TrimTypeAdmin(ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']


@admin.register(Trim)
class TrimAdmin(ModelAdmin):
    list_display = ['trim_name', 'trim_code', 'trim_type', 'supplier', 'unit', 'unit_price', 'is_active']
    list_filter = ['trim_type', 'supplier', 'is_active']
    search_fields = ['trim_name', 'trim_code']
    list_editable = ['is_active']
    list_select_related = ['trim_type', 'supplier']
    autocomplete_fields = ['trim_type', 'supplier']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('trim_type', 'supplier')


# ==================== OPTIMIZED STYLE ====================

@admin.register(Style)
class StyleAdmin(ModelAdmin):
    list_display = ['style_number', 'style_name', 'buyer', 'brand', 'season', 'garment_type', 'status', 'is_active']
    list_filter = ['buyer', 'brand', 'season', 'garment_type', 'status', 'is_active']
    search_fields = ['style_number', 'style_name', 'buyer__buyer_name']
    list_editable = ['is_active']
    list_select_related = ['buyer', 'brand', 'season', 'garment_type']
    autocomplete_fields = ['buyer', 'brand', 'season', 'garment_type']
    filter_horizontal = ['size_range']
    inlines = [StyleImageInline, StyleFabricInline, StyleTrimInline]
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'buyer', 'brand', 'season', 'garment_type'
        ).prefetch_related('size_range')


@admin.register(StyleImage)
class StyleImageAdmin(ModelAdmin):
    list_display = ['style', 'image_type', 'is_primary', 'sort_order']
    list_filter = ['image_type', 'is_primary']
    search_fields = ['style__style_number']
    list_select_related = ['style']
    autocomplete_fields = ['style']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('style')


@admin.register(StyleFabric)
class StyleFabricAdmin(ModelAdmin):
    list_display = ['style', 'fabric', 'consumption_per_piece', 'unit', 'placement']
    list_filter = ['unit', 'fabric__fabric_type']
    search_fields = ['style__style_number', 'fabric__fabric_name']
    list_select_related = ['style', 'fabric', 'fabric__fabric_type']
    autocomplete_fields = ['style', 'fabric']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('style', 'fabric', 'fabric__fabric_type')


@admin.register(StyleTrim)
class StyleTrimAdmin(ModelAdmin):
    list_display = ['style', 'trim', 'quantity_per_piece', 'placement']
    list_filter = ['trim__trim_type']
    search_fields = ['style__style_number', 'trim__trim_name']
    list_select_related = ['style', 'trim', 'trim__trim_type']
    autocomplete_fields = ['style', 'trim']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('style', 'trim', 'trim__trim_type')


@admin.register(StyleCosting)
class StyleCostingAdmin(ModelAdmin):
    list_display = ['style', 'version', 'costing_date', 'fabric_cost', 'trim_cost', 'cm_cost', 'total_cost', 'fob_price', 'margin_percent', 'is_approved']
    list_filter = ['is_approved', 'costing_date']
    search_fields = ['style__style_number']
    list_editable = ['is_approved']
    list_select_related = ['style']
    autocomplete_fields = ['style']
    readonly_fields = ['total_cost', 'margin_percent']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('style')


# ==================== OPTIMIZED BUYER ORDER ====================

@admin.register(BuyerOrder)
class BuyerOrderAdmin(ModelAdmin):
    list_display = ['order_number', 'buyer_po', 'buyer', 'style', 'total_quantity', 'unit_price', 'total_value', 'ex_factory_date', 'status']
    list_filter = ['buyer', 'status', 'shipment_mode', 'buyer_po_date']
    search_fields = ['order_number', 'buyer_po', 'lc_number', 'buyer__buyer_name', 'style__style_number']
    list_select_related = ['buyer', 'style', 'merchandiser']
    autocomplete_fields = ['buyer', 'style', 'merchandiser']
    inlines = [OrderBreakdownInline]
    list_per_page = 50
    date_hierarchy = 'buyer_po_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'buyer', 'style', 'merchandiser'
        ).prefetch_related(
            Prefetch('breakdowns', queryset=OrderBreakdown.objects.select_related('color', 'size'))
        )


@admin.register(OrderBreakdown)
class OrderBreakdownAdmin(ModelAdmin):
    list_display = ['order', 'color', 'size', 'quantity', 'unit_price', 'line_total_display', 'cutting_qty', 'shipped_qty']
    list_filter = ['order__buyer', 'color', 'size']
    search_fields = ['order__order_number', 'order__buyer_po']
    list_select_related = ['order', 'order__buyer', 'color', 'size']
    autocomplete_fields = ['order', 'color', 'size']
    list_per_page = 100
    
    @display(description=_('Line Total'))
    def line_total_display(self, obj):
        return f"${obj.line_total:,.2f}"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__buyer', 'color', 'size')


# ==================== OPTIMIZED PRODUCTION ====================

@admin.register(SewingLine)
class SewingLineAdmin(ModelAdmin):
    list_display = ['line_number', 'line_name', 'factory', 'operators', 'machines', 'daily_capacity', 'line_chief', 'is_active']
    list_filter = ['factory', 'is_active']
    search_fields = ['line_number', 'line_name', 'line_chief']
    list_editable = ['is_active']
    list_select_related = ['factory']
    autocomplete_fields = ['factory']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('factory')


@admin.register(CuttingOrder)
class CuttingOrderAdmin(ModelAdmin):
    list_display = ['cutting_number', 'order', 'color', 'cutting_date', 'total_quantity', 'number_of_lays', 'status', 'cutter_name']
    list_filter = ['status', 'cutting_date', 'order__buyer']
    search_fields = ['cutting_number', 'order__order_number', 'fabric_lot']
    list_select_related = ['order', 'order__buyer', 'color']
    autocomplete_fields = ['order', 'color']
    inlines = [CuttingSizeBreakdownInline]
    list_per_page = 50
    date_hierarchy = 'cutting_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__buyer', 'color')


@admin.register(CuttingSizeBreakdown)
class CuttingSizeBreakdownAdmin(ModelAdmin):
    list_display = ['cutting', 'size', 'quantity']
    list_filter = ['size']
    search_fields = ['cutting__cutting_number']
    list_select_related = ['cutting', 'size']
    autocomplete_fields = ['cutting', 'size']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cutting', 'size')


@admin.register(Bundle)
class BundleAdmin(ModelAdmin):
    list_display = ['bundle_number', 'cutting', 'size', 'quantity', 'status', 'sewing_line', 'barcode']
    list_filter = ['status', 'sewing_line', 'size']
    search_fields = ['bundle_number', 'barcode', 'cutting__cutting_number']
    list_select_related = ['cutting', 'size', 'sewing_line']
    autocomplete_fields = ['cutting', 'size', 'sewing_line']
    list_per_page = 100
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cutting', 'size', 'sewing_line')


# ==================== OPTIMIZED QUALITY ====================

@admin.register(DefectType)
class DefectTypeAdmin(ModelAdmin):
    list_display = ['defect_name', 'defect_code', 'category', 'severity', 'points', 'is_active']
    list_filter = ['category', 'severity', 'is_active']
    search_fields = ['defect_name', 'defect_code']
    list_editable = ['is_active']
    list_per_page = 50


@admin.register(Inspection)
class InspectionAdmin(ModelAdmin):
    list_display = ['inspection_number', 'order', 'inspection_type', 'inspection_date', 'inspected_quantity', 'passed_quantity', 'failed_quantity', 'result']
    list_filter = ['inspection_type', 'result', 'inspection_date']
    search_fields = ['inspection_number', 'order__order_number', 'inspector_name']
    list_select_related = ['order', 'order__buyer']
    autocomplete_fields = ['order']
    inlines = [InspectionDefectInline]
    list_per_page = 50
    date_hierarchy = 'inspection_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__buyer')


@admin.register(InspectionDefect)
class InspectionDefectAdmin(ModelAdmin):
    list_display = ['inspection', 'defect_type', 'quantity', 'size', 'color', 'location']
    list_filter = ['defect_type__category', 'defect_type__severity']
    search_fields = ['inspection__inspection_number']
    list_select_related = ['inspection', 'defect_type', 'size', 'color']
    autocomplete_fields = ['inspection', 'defect_type', 'size', 'color']
    list_per_page = 100
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('inspection', 'defect_type', 'size', 'color')


# ==================== OPTIMIZED PACKING ====================

@admin.register(PackingList)
class PackingListAdmin(ModelAdmin):
    list_display = ['packing_number', 'order', 'packing_date', 'invoice_number', 'total_cartons', 'total_quantity', 'gross_weight', 'cbm', 'status']
    list_filter = ['status', 'packing_date']
    search_fields = ['packing_number', 'order__order_number', 'invoice_number', 'container_number']
    list_select_related = ['order', 'order__buyer']
    autocomplete_fields = ['order']
    inlines = [CartonInline]
    list_per_page = 50
    date_hierarchy = 'packing_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__buyer')


@admin.register(Carton)
class CartonAdmin(ModelAdmin):
    list_display = ['packing', 'carton_number', 'carton_from', 'carton_to', 'length', 'width', 'height', 'gross_weight', 'total_pieces', 'cbm_display']
    list_filter = ['packing']
    search_fields = ['packing__packing_number']
    list_select_related = ['packing']
    autocomplete_fields = ['packing']
    inlines = [CartonBreakdownInline]
    list_per_page = 100
    
    @display(description=_('CBM'))
    def cbm_display(self, obj):
        return f"{obj.cbm:.3f}"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('packing')


@admin.register(CartonBreakdown)
class CartonBreakdownAdmin(ModelAdmin):
    list_display = ['carton', 'color', 'size', 'quantity']
    list_filter = ['color', 'size']
    search_fields = ['carton__packing__packing_number']
    list_select_related = ['carton', 'carton__packing', 'color', 'size']
    autocomplete_fields = ['carton', 'color', 'size']
    list_per_page = 100
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('carton', 'carton__packing', 'color', 'size')


# ==================== PHASE 2: TNA ADMINS ====================

class TNATemplateTaskInline(TabularInline):
    model = TNATemplateTask
    extra = 1
    fields = ['task', 'sequence', 'lead_time_days', 'dependency']
    autocomplete_fields = ['task', 'dependency']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task', 'dependency')


class OrderTNATaskInline(TabularInline):
    model = OrderTNATask
    extra = 0
    fields = ['task', 'plan_start_date', 'plan_end_date', 'actual_start_date', 'actual_end_date', 'status', 'responsible_person']
    autocomplete_fields = ['task']
    readonly_fields = ['delay_days']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task')


@admin.register(TNATemplate)
class TNATemplateAdmin(ModelAdmin):
    list_display = ['template_name', 'garment_type', 'is_active']
    list_filter = ['garment_type', 'is_active']
    search_fields = ['template_name']
    list_editable = ['is_active']
    autocomplete_fields = ['garment_type']
    inlines = [TNATemplateTaskInline]
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('garment_type')


@admin.register(TNATask)
class TNATaskAdmin(ModelAdmin):
    list_display = ['task_name', 'task_code', 'department', 'standard_lead_time', 'is_critical', 'sort_order', 'is_active']
    list_filter = ['department', 'is_critical', 'is_active']
    search_fields = ['task_name', 'task_code']
    list_editable = ['sort_order', 'is_active']
    ordering = ['sort_order']
    list_per_page = 100


@admin.register(TNATemplateTask)
class TNATemplateTaskAdmin(ModelAdmin):
    list_display = ['template', 'task', 'sequence', 'lead_time_days', 'dependency']
    list_filter = ['template']
    search_fields = ['template__template_name', 'task__task_name']
    list_select_related = ['template', 'task', 'dependency']
    autocomplete_fields = ['template', 'task', 'dependency']
    list_per_page = 100
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('template', 'task', 'dependency')


@admin.register(OrderTNA)
class OrderTNAAdmin(ModelAdmin):
    list_display = ['order', 'template', 'start_date', 'is_active']
    list_filter = ['template', 'is_active', 'start_date']
    search_fields = ['order__order_number']
    list_select_related = ['order', 'template']
    autocomplete_fields = ['order', 'template']
    inlines = [OrderTNATaskInline]
    list_per_page = 50
    date_hierarchy = 'start_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'template')


@admin.register(OrderTNATask)
class OrderTNATaskAdmin(ModelAdmin):
    list_display = ['order_tna', 'task', 'plan_start_date', 'plan_end_date', 'actual_end_date', 'status', 'delay_days', 'responsible_person']
    list_filter = ['status', 'task__department', 'task__is_critical']
    search_fields = ['order_tna__order__order_number', 'task__task_name', 'responsible_person']
    list_select_related = ['order_tna', 'order_tna__order', 'task']
    autocomplete_fields = ['order_tna', 'task']
    readonly_fields = ['delay_days']
    list_per_page = 100
    date_hierarchy = 'plan_end_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order_tna', 'order_tna__order', 'task')


# ==================== PHASE 3: COMPLIANCE ADMINS ====================

class FactoryComplianceInline(TabularInline):
    model = FactoryCompliance
    extra = 1
    fields = ['compliance_type', 'certificate_number', 'issue_date', 'expiry_date', 'status']
    autocomplete_fields = ['compliance_type']


@admin.register(ComplianceType)
class ComplianceTypeAdmin(ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']
    list_per_page = 50


@admin.register(FactoryCompliance)
class FactoryComplianceAdmin(ModelAdmin):
    list_display = ['factory', 'compliance_type', 'certificate_number', 'issue_date', 'expiry_date', 'status', 'expiry_warning']
    list_filter = ['factory', 'compliance_type', 'status', 'expiry_date']
    search_fields = ['factory__factory_name', 'certificate_number', 'issuing_authority']
    list_select_related = ['factory', 'compliance_type']
    autocomplete_fields = ['factory', 'compliance_type']
    list_per_page = 50
    date_hierarchy = 'expiry_date'
    
    @display(description=_('Expiry Warning'), boolean=True)
    def expiry_warning(self, obj):
        return obj.is_expiring_soon
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('factory', 'compliance_type')


@admin.register(TestType)
class TestTypeAdmin(ModelAdmin):
    list_display = ['test_name', 'test_code', 'category', 'standard_cost', 'standard_lead_time', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['test_name', 'test_code']
    list_editable = ['is_active']
    list_per_page = 50


@admin.register(OrderTest)
class OrderTestAdmin(ModelAdmin):
    list_display = ['test_number', 'order', 'test_type', 'lab_name', 'submission_date', 'expected_result_date', 'actual_result_date', 'result', 'test_cost']
    list_filter = ['result', 'test_type__category', 'lab_name', 'submission_date']
    search_fields = ['test_number', 'order__order_number', 'lab_name']
    list_select_related = ['order', 'order__buyer', 'test_type']
    autocomplete_fields = ['order', 'test_type']
    list_per_page = 50
    date_hierarchy = 'submission_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__buyer', 'test_type')


# ==================== PHASE 4: ADVANCED ADMINS ====================

@admin.register(ProductionPlan)
class ProductionPlanAdmin(ModelAdmin):
    list_display = ['plan_number', 'factory', 'sewing_line', 'order', 'style', 'planned_quantity', 'start_date', 'end_date', 'smv', 'target_efficiency', 'status']
    list_filter = ['factory', 'sewing_line', 'status', 'start_date']
    search_fields = ['plan_number', 'order__order_number', 'style__style_number']
    list_select_related = ['factory', 'sewing_line', 'order', 'style']
    autocomplete_fields = ['factory', 'sewing_line', 'order', 'style']
    list_per_page = 50
    date_hierarchy = 'start_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('factory', 'sewing_line', 'order', 'style')


@admin.register(DailyProduction)
class DailyProductionAdmin(ModelAdmin):
    list_display = ['production_date', 'sewing_line', 'order', 'target_quantity', 'produced_quantity', 'rejected_quantity', 'efficiency_percent', 'achievement_display']
    list_filter = ['sewing_line', 'production_date']
    search_fields = ['order__order_number', 'sewing_line__line_number']
    list_select_related = ['production_plan', 'sewing_line', 'order']
    autocomplete_fields = ['production_plan', 'sewing_line', 'order']
    readonly_fields = ['efficiency_percent']
    list_per_page = 100
    date_hierarchy = 'production_date'
    
    @display(description=_('Achievement%'))
    def achievement_display(self, obj):
        return f"{obj.achievement_percent:.2f}%"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('production_plan', 'sewing_line', 'order')


@admin.register(FabricReceive)
class FabricReceiveAdmin(ModelAdmin):
    list_display = ['receive_number', 'receive_date', 'order', 'fabric', 'supplier', 'color', 'lot_number', 'roll_count', 'received_quantity', 'unit']
    list_filter = ['supplier', 'fabric__fabric_type', 'receive_date']
    search_fields = ['receive_number', 'order__order_number', 'lot_number', 'challan_number']
    list_select_related = ['order', 'fabric', 'fabric__fabric_type', 'supplier', 'color']
    autocomplete_fields = ['order', 'fabric', 'supplier', 'color']
    list_per_page = 50
    date_hierarchy = 'receive_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'fabric', 'fabric__fabric_type', 'supplier', 'color')


@admin.register(TrimReceive)
class TrimReceiveAdmin(ModelAdmin):
    list_display = ['receive_number', 'receive_date', 'order', 'trim', 'supplier', 'color', 'lot_number', 'received_quantity']
    list_filter = ['supplier', 'trim__trim_type', 'receive_date']
    search_fields = ['receive_number', 'order__order_number', 'lot_number', 'challan_number']
    list_select_related = ['order', 'trim', 'trim__trim_type', 'supplier', 'color']
    autocomplete_fields = ['order', 'trim', 'supplier', 'color']
    list_per_page = 50
    date_hierarchy = 'receive_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'trim', 'trim__trim_type', 'supplier', 'color')


@admin.register(Shipment)
class ShipmentAdmin(ModelAdmin):
    list_display = ['shipment_number', 'shipment_date', 'order', 'invoice_number', 'invoice_value', 'shipped_quantity', 'shipment_mode', 'container_number', 'bl_number', 'etd', 'eta', 'status']
    list_filter = ['shipment_mode', 'status', 'shipment_date', 'port_of_loading']
    search_fields = ['shipment_number', 'order__order_number', 'invoice_number', 'container_number', 'bl_number']
    list_select_related = ['order', 'order__buyer']
    autocomplete_fields = ['order']
    list_per_page = 50
    date_hierarchy = 'shipment_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__buyer')


# ==================== PHASE 6: COSTING & PRICING MANAGEMENT ====================

class CostingComponentInline(admin.TabularInline):
    model = CostingComponent
    extra = 1
    fields = ['component_type', 'description', 'quantity', 'unit', 'unit_cost', 'total_cost', 'wastage_percent', 'final_cost']
    readonly_fields = ['total_cost', 'final_cost']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('costing_sheet')


@admin.register(CostingSheet)
class CostingSheetAdmin(ModelAdmin):
    list_display = ['costing_number', 'style', 'buyer', 'season', 'version', 'costing_date', 'total_cost', 'final_price', 'margin_percent', 'status', 'approved_date']
    list_filter = ['status', 'buyer', 'season', 'costing_date', 'approved_date']
    search_fields = ['costing_number', 'style__style_number', 'buyer__buyer_name']
    list_select_related = ['style', 'buyer', 'season']
    autocomplete_fields = ['style', 'buyer', 'season']
    readonly_fields = ['total_cost', 'margin_amount', 'margin_percent', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'costing_date'
    inlines = [CostingComponentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('costing_number', 'style', 'buyer', 'season', 'version', 'costing_date')
        }),
        ('Cost Breakdown', {
            'fields': (
                ('fabric_cost', 'trim_cost'),
                ('embellishment_cost', 'cm_cost'),
                ('testing_cost', 'commercial_cost'),
                ('other_cost', 'total_cost')
            )
        }),
        ('Pricing', {
            'fields': (
                ('target_price', 'quoted_price', 'final_price'),
                ('margin_amount', 'margin_percent')
            )
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approved_date', 'remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('style', 'buyer', 'season').prefetch_related('components')


@admin.register(CostingComponent)
class CostingComponentAdmin(ModelAdmin):
    list_display = ['costing_sheet', 'component_type', 'description', 'quantity', 'unit', 'unit_cost', 'total_cost', 'wastage_percent', 'final_cost']
    list_filter = ['component_type', 'unit']
    search_fields = ['costing_sheet__costing_number', 'description']
    list_select_related = ['costing_sheet', 'costing_sheet__style']
    autocomplete_fields = ['costing_sheet']
    readonly_fields = ['total_cost', 'final_cost', 'created_at', 'updated_at']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('costing_sheet', 'costing_sheet__style')


class PriceListItemInline(admin.TabularInline):
    model = PriceListItem
    extra = 1
    fields = ['style', 'unit_price', 'min_quantity', 'max_quantity', 'discount_percent', 'final_price']
    readonly_fields = ['final_price']
    autocomplete_fields = ['style']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('price_list', 'style')


@admin.register(PriceList)
class PriceListAdmin(ModelAdmin):
    list_display = ['price_list_name', 'price_list_code', 'buyer', 'season', 'currency', 'valid_from', 'valid_to', 'is_active']
    list_filter = ['buyer', 'season', 'currency', 'is_active', 'valid_from']
    search_fields = ['price_list_name', 'price_list_code', 'buyer__buyer_name']
    list_select_related = ['buyer', 'season']
    autocomplete_fields = ['buyer', 'season']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'valid_from'
    inlines = [PriceListItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('price_list_name', 'price_list_code', 'buyer', 'season', 'currency')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_to', 'is_active')
        }),
        ('Additional', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('buyer', 'season').prefetch_related('items')


@admin.register(PriceListItem)
class PriceListItemAdmin(ModelAdmin):
    list_display = ['price_list', 'style', 'unit_price', 'min_quantity', 'max_quantity', 'discount_percent', 'final_price']
    list_filter = ['price_list__buyer', 'price_list__season']
    search_fields = ['price_list__price_list_name', 'style__style_number']
    list_select_related = ['price_list', 'price_list__buyer', 'style']
    autocomplete_fields = ['price_list', 'style']
    readonly_fields = ['final_price', 'created_at', 'updated_at']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('price_list', 'price_list__buyer', 'style')


@admin.register(QuotationCosting)
class QuotationCostingAdmin(ModelAdmin):
    list_display = ['quotation_number', 'buyer', 'style', 'quotation_date', 'quantity', 'quoted_price', 'total_value', 'margin_percent', 'status']
    list_filter = ['status', 'buyer', 'quotation_date']
    search_fields = ['quotation_number', 'buyer__buyer_name', 'style__style_number']
    list_select_related = ['buyer', 'style', 'costing_sheet']
    autocomplete_fields = ['buyer', 'style', 'costing_sheet']
    readonly_fields = ['total_cost', 'total_value', 'margin_per_piece', 'margin_percent', 'total_margin', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'quotation_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('quotation_number', 'buyer', 'style', 'costing_sheet', 'quotation_date', 'quantity')
        }),
        ('Costing', {
            'fields': (
                ('total_cost', 'quoted_price', 'total_value'),
                ('margin_per_piece', 'margin_percent', 'total_margin')
            )
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('buyer', 'style', 'costing_sheet')


@admin.register(OrderCosting)
class OrderCostingAdmin(ModelAdmin):
    list_display = ['order', 'budgeted_total', 'actual_total', 'order_value', 'budgeted_profit', 'actual_profit', 'profit_variance', 'last_updated']
    list_filter = ['order__buyer', 'last_updated']
    search_fields = ['order__order_number', 'order__buyer__buyer_name']
    list_select_related = ['order', 'order__buyer', 'costing_sheet']
    autocomplete_fields = ['order', 'costing_sheet']
    readonly_fields = ['budgeted_total', 'actual_total', 'budgeted_profit', 'actual_profit', 'profit_variance', 'last_updated', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'last_updated'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'costing_sheet')
        }),
        ('Budgeted Costs', {
            'fields': (
                ('budgeted_fabric', 'budgeted_trim'),
                ('budgeted_cm', 'budgeted_other'),
                'budgeted_total'
            )
        }),
        ('Actual Costs', {
            'fields': (
                ('actual_fabric', 'actual_trim'),
                ('actual_cm', 'actual_other'),
                'actual_total'
            )
        }),
        ('Profit Analysis', {
            'fields': (
                'order_value',
                ('budgeted_profit', 'actual_profit', 'profit_variance')
            )
        }),
        ('Timestamps', {
            'fields': ('last_updated', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__buyer', 'costing_sheet')


@admin.register(ProfitAnalysis)
class ProfitAnalysisAdmin(ModelAdmin):
    list_display = ['analysis_date', 'analysis_type', 'buyer', 'season', 'total_revenue', 'total_cost', 'gross_profit', 'gross_margin_percent', 'quantity', 'profit_per_piece']
    list_filter = ['analysis_type', 'buyer', 'season', 'analysis_date']
    search_fields = ['order__order_number', 'style__style_number', 'buyer__buyer_name']
    list_select_related = ['order', 'style', 'buyer', 'season']
    autocomplete_fields = ['order', 'style', 'buyer', 'season']
    readonly_fields = ['gross_profit', 'gross_margin_percent', 'profit_per_piece', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'analysis_date'
    
    fieldsets = (
        ('Analysis Information', {
            'fields': ('analysis_date', 'analysis_type')
        }),
        ('References', {
            'fields': ('order', 'style', 'buyer', 'season')
        }),
        ('Metrics', {
            'fields': (
                ('total_revenue', 'total_cost'),
                ('gross_profit', 'gross_margin_percent'),
                ('quantity', 'profit_per_piece')
            )
        }),
        ('Additional', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'style', 'buyer', 'season')


@admin.register(CostVariance)
class CostVarianceAdmin(ModelAdmin):
    list_display = ['order', 'variance_date', 'cost_category', 'budgeted_amount', 'actual_amount', 'variance_amount', 'variance_percent', 'variance_type']
    list_filter = ['cost_category', 'variance_type', 'variance_date', 'order__buyer']
    search_fields = ['order__order_number', 'order__buyer__buyer_name']
    list_select_related = ['order', 'order__buyer']
    autocomplete_fields = ['order']
    readonly_fields = ['variance_amount', 'variance_percent', 'variance_type', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'variance_date'
    
    fieldsets = (
        ('Variance Information', {
            'fields': ('order', 'variance_date', 'cost_category')
        }),
        ('Amounts', {
            'fields': (
                ('budgeted_amount', 'actual_amount'),
                ('variance_amount', 'variance_percent', 'variance_type')
            )
        }),
        ('Analysis', {
            'fields': ('reason', 'action_taken')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__buyer')


# ==================== PHASE 7: CAPACITY PLANNING & SCHEDULING ====================

class LineCapacityInline(admin.TabularInline):
    model = LineCapacity
    extra = 1
    fields = ['sewing_line', 'working_days', 'working_hours_per_day', 'operators', 'capacity_minutes', 'planned_minutes', 'utilization_percent']
    readonly_fields = ['capacity_minutes', 'utilization_percent']
    autocomplete_fields = ['sewing_line']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sewing_line', 'capacity_plan')


@admin.register(CapacityPlan)
class CapacityPlanAdmin(ModelAdmin):
    list_display = ['plan_number', 'factory', 'plan_month', 'total_working_days', 'total_operators', 'capacity_minutes', 'planned_minutes', 'utilization_percent', 'status']
    list_filter = ['factory', 'status', 'plan_month']
    search_fields = ['plan_number', 'factory__factory_name']
    list_select_related = ['factory']
    autocomplete_fields = ['factory']
    readonly_fields = ['capacity_minutes', 'utilization_percent', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'plan_month'
    inlines = [LineCapacityInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('factory').prefetch_related('line_capacities')


@admin.register(LineCapacity)
class LineCapacityAdmin(ModelAdmin):
    list_display = ['capacity_plan', 'sewing_line', 'working_days', 'operators', 'capacity_minutes', 'planned_minutes', 'utilization_percent', 'target_efficiency', 'actual_efficiency']
    list_filter = ['capacity_plan__factory', 'sewing_line']
    search_fields = ['capacity_plan__plan_number', 'sewing_line__line_number']
    list_select_related = ['capacity_plan', 'capacity_plan__factory', 'sewing_line']
    autocomplete_fields = ['capacity_plan', 'sewing_line']
    readonly_fields = ['capacity_minutes', 'utilization_percent', 'created_at', 'updated_at']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('capacity_plan', 'capacity_plan__factory', 'sewing_line')


@admin.register(ProductionSchedule)
class ProductionScheduleAdmin(ModelAdmin):
    list_display = ['schedule_number', 'sewing_line', 'order', 'style', 'scheduled_date', 'start_time', 'end_time', 'planned_quantity', 'actual_quantity', 'status', 'priority']
    list_filter = ['status', 'sewing_line', 'scheduled_date']
    search_fields = ['schedule_number', 'order__order_number', 'style__style_number']
    list_select_related = ['capacity_plan', 'sewing_line', 'order', 'style']
    autocomplete_fields = ['capacity_plan', 'sewing_line', 'order', 'style']
    readonly_fields = ['required_minutes', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'scheduled_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('capacity_plan', 'sewing_line', 'order', 'style')


@admin.register(ScheduleConflict)
class ScheduleConflictAdmin(ModelAdmin):
    list_display = ['conflict_date', 'sewing_line', 'conflict_type', 'severity', 'status', 'resolved_by', 'resolved_date']
    list_filter = ['conflict_type', 'severity', 'status', 'conflict_date']
    search_fields = ['sewing_line__line_number', 'description']
    list_select_related = ['sewing_line', 'schedule1', 'schedule2']
    autocomplete_fields = ['sewing_line', 'schedule1', 'schedule2']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'conflict_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sewing_line', 'schedule1', 'schedule2')


@admin.register(ResourceAllocation)
class ResourceAllocationAdmin(ModelAdmin):
    list_display = ['allocation_number', 'production_schedule', 'resource_type', 'resource_name', 'quantity', 'allocated_from', 'allocated_to', 'status']
    list_filter = ['resource_type', 'status', 'allocated_from']
    search_fields = ['allocation_number', 'resource_name', 'production_schedule__schedule_number']
    list_select_related = ['production_schedule']
    autocomplete_fields = ['production_schedule']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('production_schedule')


@admin.register(DowntimeTracking)
class DowntimeTrackingAdmin(ModelAdmin):
    list_display = ['downtime_number', 'downtime_date', 'sewing_line', 'downtime_type', 'start_time', 'end_time', 'duration_minutes', 'status', 'reported_by']
    list_filter = ['downtime_type', 'status', 'downtime_date', 'sewing_line']
    search_fields = ['downtime_number', 'sewing_line__line_number', 'reason']
    list_select_related = ['sewing_line']
    autocomplete_fields = ['sewing_line']
    readonly_fields = ['duration_minutes', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'downtime_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sewing_line')


@admin.register(EfficiencyTracking)
class EfficiencyTrackingAdmin(ModelAdmin):
    list_display = ['tracking_date', 'sewing_line', 'operators_present', 'target_quantity', 'produced_quantity', 'efficiency_percent', 'achievement_percent', 'downtime_minutes']
    list_filter = ['sewing_line', 'tracking_date']
    search_fields = ['sewing_line__line_number']
    list_select_related = ['sewing_line', 'production_schedule']
    autocomplete_fields = ['sewing_line', 'production_schedule']
    readonly_fields = ['available_minutes', 'earned_minutes', 'efficiency_percent', 'achievement_percent', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'tracking_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sewing_line', 'production_schedule')


# ==================== PHASE 8: QUALITY MANAGEMENT SYSTEM ====================

@admin.register(QualityStandard)
class QualityStandardAdmin(ModelAdmin):
    list_display = ['standard_name', 'standard_code', 'standard_type', 'aql_level', 'is_active']
    list_filter = ['standard_type', 'is_active']
    search_fields = ['standard_name', 'standard_code']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request)


class InspectionCheckpointInline(admin.TabularInline):
    model = InspectionCheckpoint
    extra = 1
    fields = ['checkpoint_name', 'checkpoint_type', 'acceptance_criteria', 'is_critical', 'sort_order']


@admin.register(InspectionPlan)
class InspectionPlanAdmin(ModelAdmin):
    list_display = ['plan_number', 'style', 'quality_standard', 'inspection_stage', 'sample_size', 'acceptance_level', 'is_active']
    list_filter = ['inspection_stage', 'quality_standard', 'is_active']
    search_fields = ['plan_number', 'style__style_number']
    list_select_related = ['style', 'quality_standard']
    autocomplete_fields = ['style', 'quality_standard']
    list_per_page = 50
    inlines = [InspectionCheckpointInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('style', 'quality_standard').prefetch_related('checkpoints')


@admin.register(InspectionCheckpoint)
class InspectionCheckpointAdmin(ModelAdmin):
    list_display = ['inspection_plan', 'checkpoint_name', 'checkpoint_type', 'is_critical', 'sort_order']
    list_filter = ['checkpoint_type', 'is_critical']
    search_fields = ['checkpoint_name', 'inspection_plan__plan_number']
    list_select_related = ['inspection_plan']
    autocomplete_fields = ['inspection_plan']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('inspection_plan')


@admin.register(QualityParameter)
class QualityParameterAdmin(ModelAdmin):
    list_display = ['parameter_name', 'parameter_code', 'unit', 'min_value', 'max_value', 'target_value', 'tolerance', 'is_active']
    list_filter = ['is_active', 'unit']
    search_fields = ['parameter_name', 'parameter_code']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(MeasurementRecord)
class MeasurementRecordAdmin(ModelAdmin):
    list_display = ['record_number', 'inspection', 'quality_parameter', 'measured_value', 'is_within_tolerance', 'measured_by', 'measured_date']
    list_filter = ['is_within_tolerance', 'measured_date', 'quality_parameter']
    search_fields = ['record_number', 'inspection__inspection_number']
    list_select_related = ['inspection', 'quality_parameter']
    autocomplete_fields = ['inspection', 'quality_parameter']
    readonly_fields = ['is_within_tolerance']
    list_per_page = 50
    date_hierarchy = 'measured_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('inspection', 'quality_parameter')


@admin.register(NonConformance)
class NonConformanceAdmin(ModelAdmin):
    list_display = ['ncr_number', 'ncr_date', 'order', 'defect_type', 'quantity_affected', 'severity', 'status', 'reported_by']
    list_filter = ['severity', 'status', 'ncr_date']
    search_fields = ['ncr_number', 'order__order_number']
    list_select_related = ['order', 'inspection', 'defect_type']
    autocomplete_fields = ['order', 'inspection', 'defect_type']
    list_per_page = 50
    date_hierarchy = 'ncr_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'inspection', 'defect_type')


@admin.register(CorrectiveAction)
class CorrectiveActionAdmin(ModelAdmin):
    list_display = ['capa_number', 'non_conformance', 'action_type', 'responsible_person', 'target_date', 'completion_date', 'status']
    list_filter = ['action_type', 'status', 'target_date']
    search_fields = ['capa_number', 'responsible_person', 'non_conformance__ncr_number']
    list_select_related = ['non_conformance']
    autocomplete_fields = ['non_conformance']
    list_per_page = 50
    date_hierarchy = 'target_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('non_conformance')


@admin.register(QualityAudit)
class QualityAuditAdmin(ModelAdmin):
    list_display = ['audit_number', 'audit_date', 'audit_type', 'factory', 'auditor_name', 'score', 'result', 'next_audit_date']
    list_filter = ['audit_type', 'result', 'audit_date']
    search_fields = ['audit_number', 'auditor_name', 'factory__factory_name']
    list_select_related = ['factory']
    autocomplete_fields = ['factory']
    list_per_page = 50
    date_hierarchy = 'audit_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('factory')


@admin.register(QualityMetrics)
class QualityMetricsAdmin(ModelAdmin):
    list_display = ['metric_date', 'factory', 'total_inspected', 'total_passed', 'total_failed', 'pass_rate', 'defect_rate', 'rework_quantity', 'rejection_quantity']
    list_filter = ['factory', 'metric_date']
    search_fields = ['factory__factory_name']
    list_select_related = ['factory']
    autocomplete_fields = ['factory']
    readonly_fields = ['pass_rate', 'defect_rate']
    list_per_page = 50
    date_hierarchy = 'metric_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('factory')


# ==================== PHASE 9: SAMPLE MANAGEMENT ====================

@admin.register(SampleType)
class SampleTypeAdmin(ModelAdmin):
    list_display = ['type_name', 'type_code', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['type_name', 'type_code']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(SampleRequest)
class SampleRequestAdmin(ModelAdmin):
    list_display = ['request_number', 'request_date', 'buyer', 'style', 'sample_type', 'quantity', 'required_date', 'status']
    list_filter = ['status', 'buyer', 'sample_type', 'request_date']
    search_fields = ['request_number', 'style__style_number', 'buyer__buyer_name']
    list_select_related = ['buyer', 'merchandiser', 'style', 'sample_type']
    autocomplete_fields = ['buyer', 'merchandiser', 'style', 'sample_type']
    list_per_page = 50
    date_hierarchy = 'request_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('buyer', 'merchandiser', 'style', 'sample_type')


class SampleCommentInline(admin.TabularInline):
    model = SampleComment
    extra = 1
    fields = ['comment_date', 'commented_by', 'comment_text', 'is_internal']
    readonly_fields = ['comment_date']


@admin.register(SampleDevelopment)
class SampleDevelopmentAdmin(ModelAdmin):
    list_display = ['development_number', 'sample_request', 'start_date', 'target_completion', 'actual_completion', 'assigned_to', 'status']
    list_filter = ['status', 'assigned_to', 'start_date']
    search_fields = ['development_number', 'sample_request__request_number', 'assigned_to']
    list_select_related = ['sample_request', 'sample_request__buyer', 'sample_request__style']
    autocomplete_fields = ['sample_request']
    list_per_page = 50
    date_hierarchy = 'start_date'
    inlines = [SampleCommentInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sample_request', 'sample_request__buyer', 'sample_request__style').prefetch_related('comments', 'approvals')


@admin.register(SampleApproval)
class SampleApprovalAdmin(ModelAdmin):
    list_display = ['approval_number', 'sample_development', 'submission_date', 'approval_date', 'approved_by', 'result']
    list_filter = ['result', 'submission_date']
    search_fields = ['approval_number', 'sample_development__development_number', 'approved_by']
    list_select_related = ['sample_development']
    autocomplete_fields = ['sample_development']
    list_per_page = 50
    date_hierarchy = 'submission_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sample_development')


@admin.register(SampleComment)
class SampleCommentAdmin(ModelAdmin):
    list_display = ['sample_development', 'comment_date', 'commented_by', 'is_internal']
    list_filter = ['is_internal', 'comment_date', 'commented_by']
    search_fields = ['sample_development__development_number', 'commented_by', 'comment_text']
    list_select_related = ['sample_development']
    autocomplete_fields = ['sample_development']
    list_per_page = 50
    date_hierarchy = 'comment_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sample_development')


@admin.register(SampleCost)
class SampleCostAdmin(ModelAdmin):
    list_display = ['sample_development', 'fabric_cost', 'trim_cost', 'labor_cost', 'other_cost', 'total_cost']
    search_fields = ['sample_development__development_number']
    list_select_related = ['sample_development']
    autocomplete_fields = ['sample_development']
    readonly_fields = ['total_cost', 'created_at', 'updated_at']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sample_development')


# ==================== PHASE 10: FABRIC & TRIM INVENTORY ====================

@admin.register(FabricStock)
class FabricStockAdmin(ModelAdmin):
    list_display = ['fabric', 'color', 'warehouse', 'opening_stock', 'received_quantity', 'issued_quantity', 'returned_quantity', 'current_stock', 'unit']
    list_filter = ['warehouse', 'fabric__fabric_type']
    search_fields = ['fabric__fabric_name', 'color__name', 'warehouse']
    list_select_related = ['fabric', 'fabric__fabric_type', 'color']
    autocomplete_fields = ['fabric', 'color']
    readonly_fields = ['current_stock', 'created_at', 'updated_at']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('fabric', 'fabric__fabric_type', 'color')


@admin.register(FabricRoll)
class FabricRollAdmin(ModelAdmin):
    list_display = ['roll_number', 'fabric_receive', 'roll_length', 'roll_weight', 'status', 'location']
    list_filter = ['status', 'fabric_receive__fabric']
    search_fields = ['roll_number', 'fabric_receive__receive_number']
    list_select_related = ['fabric_receive', 'fabric_receive__fabric']
    autocomplete_fields = ['fabric_receive']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('fabric_receive', 'fabric_receive__fabric')


@admin.register(FabricIssue)
class FabricIssueAdmin(ModelAdmin):
    list_display = ['issue_number', 'issue_date', 'cutting_order', 'fabric', 'color', 'issued_quantity', 'unit', 'issued_by']
    list_filter = ['issue_date', 'fabric', 'color']
    search_fields = ['issue_number', 'cutting_order__cutting_number', 'fabric__fabric_name']
    list_select_related = ['cutting_order', 'fabric', 'color']
    autocomplete_fields = ['cutting_order', 'fabric', 'color']
    list_per_page = 50
    date_hierarchy = 'issue_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cutting_order', 'fabric', 'color')


@admin.register(FabricReturn)
class FabricReturnAdmin(ModelAdmin):
    list_display = ['return_number', 'return_date', 'fabric_issue', 'returned_quantity', 'returned_by']
    list_filter = ['return_date']
    search_fields = ['return_number', 'fabric_issue__issue_number']
    list_select_related = ['fabric_issue', 'fabric_issue__fabric']
    autocomplete_fields = ['fabric_issue']
    list_per_page = 50
    date_hierarchy = 'return_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('fabric_issue', 'fabric_issue__fabric')


@admin.register(TrimStock)
class TrimStockAdmin(ModelAdmin):
    list_display = ['trim', 'color', 'warehouse', 'opening_stock', 'received_quantity', 'issued_quantity', 'returned_quantity', 'current_stock']
    list_filter = ['warehouse', 'trim__trim_type']
    search_fields = ['trim__trim_name', 'warehouse']
    list_select_related = ['trim', 'trim__trim_type', 'color']
    autocomplete_fields = ['trim', 'color']
    readonly_fields = ['current_stock', 'created_at', 'updated_at']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('trim', 'trim__trim_type', 'color')


@admin.register(TrimIssue)
class TrimIssueAdmin(ModelAdmin):
    list_display = ['issue_number', 'issue_date', 'order', 'trim', 'color', 'issued_quantity', 'issued_by']
    list_filter = ['issue_date', 'trim']
    search_fields = ['issue_number', 'order__order_number', 'trim__trim_name']
    list_select_related = ['order', 'trim', 'color']
    autocomplete_fields = ['order', 'trim', 'color']
    list_per_page = 50
    date_hierarchy = 'issue_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'trim', 'color')


@admin.register(TrimReturn)
class TrimReturnAdmin(ModelAdmin):
    list_display = ['return_number', 'return_date', 'trim_issue', 'returned_quantity', 'returned_by']
    list_filter = ['return_date']
    search_fields = ['return_number', 'trim_issue__issue_number']
    list_select_related = ['trim_issue', 'trim_issue__trim']
    autocomplete_fields = ['trim_issue']
    list_per_page = 50
    date_hierarchy = 'return_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('trim_issue', 'trim_issue__trim')


@admin.register(MaterialRequisition)
class MaterialRequisitionAdmin(ModelAdmin):
    list_display = ['requisition_number', 'requisition_date', 'order', 'requisition_type', 'required_date', 'requested_by', 'status', 'approved_by']
    list_filter = ['requisition_type', 'status', 'requisition_date']
    search_fields = ['requisition_number', 'order__order_number', 'requested_by']
    list_select_related = ['order']
    autocomplete_fields = ['order']
    list_per_page = 50
    date_hierarchy = 'requisition_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')


# ==================== PHASE 11: SUBCONTRACTING MANAGEMENT ====================

@admin.register(Subcontractor)
class SubcontractorAdmin(ModelAdmin):
    list_display = ['subcontractor_name', 'subcontractor_code', 'contact_person', 'phone', 'email', 'capacity_per_month', 'is_active']
    list_filter = ['is_active']
    search_fields = ['subcontractor_name', 'subcontractor_code', 'contact_person']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(SubcontractOrder)
class SubcontractOrderAdmin(ModelAdmin):
    list_display = ['subcontract_number', 'subcontract_date', 'subcontractor', 'order', 'operation_type', 'quantity', 'rate_per_piece', 'total_amount', 'delivery_date', 'status']
    list_filter = ['status', 'subcontractor', 'subcontract_date']
    search_fields = ['subcontract_number', 'subcontractor__subcontractor_name', 'order__order_number']
    list_select_related = ['subcontractor', 'order']
    autocomplete_fields = ['subcontractor', 'order']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'subcontract_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subcontractor', 'order')


@admin.register(SubcontractDelivery)
class SubcontractDeliveryAdmin(ModelAdmin):
    list_display = ['delivery_number', 'delivery_date', 'subcontract_order', 'delivered_quantity', 'accepted_quantity', 'rejected_quantity', 'received_by']
    list_filter = ['delivery_date', 'subcontract_order__subcontractor']
    search_fields = ['delivery_number', 'subcontract_order__subcontract_number']
    list_select_related = ['subcontract_order', 'subcontract_order__subcontractor']
    autocomplete_fields = ['subcontract_order']
    list_per_page = 50
    date_hierarchy = 'delivery_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subcontract_order', 'subcontract_order__subcontractor')


@admin.register(SubcontractPayment)
class SubcontractPaymentAdmin(ModelAdmin):
    list_display = ['payment_number', 'payment_date', 'subcontractor', 'subcontract_order', 'payment_amount', 'payment_method', 'reference_number']
    list_filter = ['payment_method', 'payment_date', 'subcontractor']
    search_fields = ['payment_number', 'subcontractor__subcontractor_name', 'reference_number']
    list_select_related = ['subcontractor', 'subcontract_order']
    autocomplete_fields = ['subcontractor', 'subcontract_order']
    list_per_page = 50
    date_hierarchy = 'payment_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subcontractor', 'subcontract_order')


@admin.register(SubcontractQuality)
class SubcontractQualityAdmin(ModelAdmin):
    list_display = ['subcontract_delivery', 'check_date', 'checked_quantity', 'defect_quantity', 'defect_rate', 'quality_rating']
    list_filter = ['quality_rating', 'check_date']
    search_fields = ['subcontract_delivery__delivery_number']
    list_select_related = ['subcontract_delivery', 'subcontract_delivery__subcontract_order']
    autocomplete_fields = ['subcontract_delivery']
    readonly_fields = ['defect_rate', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'check_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subcontract_delivery', 'subcontract_delivery__subcontract_order')
