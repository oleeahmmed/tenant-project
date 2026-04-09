from django.contrib import admin

from .models import (
    GoodsIssue,
    GoodsIssueItem,
    InventoryTransfer,
    InventoryTransferItem,
    StockAdjustment,
    StockAdjustmentItem,
    StockTransaction,
    WarehouseStock,
)


class StockAdjustmentItemInline(admin.TabularInline):
    model = StockAdjustmentItem
    extra = 0
    readonly_fields = ("system_quantity", "quantity_difference", "value_difference", "line_total")


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ("adjustment_number", "tenant", "adjustment_date", "warehouse_code", "status", "total_amount")
    list_filter = ("status", "tenant")
    inlines = [StockAdjustmentItemInline]


class GoodsIssueItemInline(admin.TabularInline):
    model = GoodsIssueItem
    extra = 0


@admin.register(GoodsIssue)
class GoodsIssueAdmin(admin.ModelAdmin):
    list_display = ("issue_number", "tenant", "issue_date", "warehouse", "status", "stock_posted")
    list_filter = ("status", "tenant")
    inlines = [GoodsIssueItemInline]


class InventoryTransferItemInline(admin.TabularInline):
    model = InventoryTransferItem
    extra = 0


@admin.register(InventoryTransfer)
class InventoryTransferAdmin(admin.ModelAdmin):
    list_display = ("transfer_number", "tenant", "transfer_date", "from_warehouse", "to_warehouse", "status")
    list_filter = ("status", "tenant")
    inlines = [InventoryTransferItemInline]


@admin.register(WarehouseStock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = ("tenant", "product", "warehouse", "quantity", "min_quantity", "max_quantity")


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "tenant", "transaction_type", "product", "warehouse", "qty_signed", "reference")
    list_filter = ("transaction_type", "tenant")
