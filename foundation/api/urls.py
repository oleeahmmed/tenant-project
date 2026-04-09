from django.urls import path

from . import views

app_name = "foundation_api"

urlpatterns = [
    path("autocomplete/products/", views.ProductAutocompleteView.as_view(), name="autocomplete_products"),
    path("autocomplete/warehouses/", views.WarehouseAutocompleteView.as_view(), name="autocomplete_warehouses"),
    path("autocomplete/categories/", views.CategoryAutocompleteView.as_view(), name="autocomplete_categories"),
    path("autocomplete/customers/", views.CustomerAutocompleteView.as_view(), name="autocomplete_customers"),
    path("autocomplete/suppliers/", views.SupplierAutocompleteView.as_view(), name="autocomplete_suppliers"),
    path("autocomplete/units-of-measure/", views.UnitOfMeasureAutocompleteView.as_view(), name="autocomplete_uoms"),
    path("autocomplete/currencies/", views.CurrencyAutocompleteView.as_view(), name="autocomplete_currencies"),
    path("autocomplete/payment-methods/", views.PaymentMethodAutocompleteView.as_view(), name="autocomplete_payment_methods"),
    path("autocomplete/sales-persons/", views.SalesPersonAutocompleteView.as_view(), name="autocomplete_sales_persons"),
    path("autocomplete/tax-types/", views.TaxTypeAutocompleteView.as_view(), name="autocomplete_tax_types"),
    path("autocomplete/product-variants/", views.ProductVariantAutocompleteView.as_view(), name="autocomplete_product_variants"),
]
