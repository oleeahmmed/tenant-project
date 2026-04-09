from django.contrib import admin

from .models import (
    Category,
    Currency,
    Customer,
    ExchangeRate,
    PaymentMethod,
    PaymentTerm,
    Product,
    ProductVariant,
    SalesPerson,
    Supplier,
    TaxRate,
    TaxType,
    UnitOfMeasure,
    UomConversion,
    Warehouse,
)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "city", "is_active", "updated_at")
    list_filter = ("is_active", "tenant")
    search_fields = ("code", "name", "city")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "parent", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("code", "name")


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "decimal_places", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("code", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "tenant", "category", "default_uom", "default_unit_cost", "list_price", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("sku", "name")


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "product", "tenant", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("code", "name", "barcode", "product__sku")


@admin.register(UomConversion)
class UomConversionAdmin(admin.ModelAdmin):
    list_display = ("tenant", "from_uom", "to_uom", "factor")
    list_filter = ("tenant",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_code", "name", "tenant", "city", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("customer_code", "name", "email")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("supplier_code", "name", "tenant", "city", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("supplier_code", "name", "email")


@admin.register(SalesPerson)
class SalesPersonAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("code", "name")


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("code", "name")


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "symbol", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("code", "name")


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("tenant", "from_currency", "to_currency", "rate", "effective_date")
    list_filter = ("tenant", "effective_date")


@admin.register(TaxType)
class TaxTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("code", "name")


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ("tenant", "tax_type", "rate_percent", "effective_from")
    list_filter = ("tenant", "effective_from")


@admin.register(PaymentTerm)
class PaymentTermAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "days_until_due", "is_active")
    list_filter = ("is_active", "tenant")
    search_fields = ("code", "name")
