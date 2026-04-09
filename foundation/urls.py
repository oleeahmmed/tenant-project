from django.urls import path

from . import views

app_name = "foundation"

urlpatterns = [
    path("", views.FoundationDashboardView.as_view(), name="foundation_dashboard"),
    path("warehouses/", views.WarehouseListView.as_view(), name="warehouse_list"),
    path("warehouses/add/", views.WarehouseCreateView.as_view(), name="warehouse_create"),
    path(
        "warehouses/<int:pk>/edit/",
        views.WarehouseUpdateView.as_view(),
        name="warehouse_edit",
    ),
    path(
        "warehouses/<int:pk>/delete/",
        views.WarehouseDeleteView.as_view(),
        name="warehouse_delete",
    ),
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/add/", views.CategoryCreateView.as_view(), name="category_create"),
    path(
        "categories/<int:pk>/edit/",
        views.CategoryUpdateView.as_view(),
        name="category_edit",
    ),
    path(
        "categories/<int:pk>/delete/",
        views.CategoryDeleteView.as_view(),
        name="category_delete",
    ),
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/add/", views.ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("products/<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product_edit"),
    path(
        "products/<int:pk>/delete/",
        views.ProductDeleteView.as_view(),
        name="product_delete",
    ),
    path("units-of-measure/", views.UomListView.as_view(), name="uom_list"),
    path("units-of-measure/add/", views.UomCreateView.as_view(), name="uom_create"),
    path("units-of-measure/<int:pk>/edit/", views.UomUpdateView.as_view(), name="uom_edit"),
    path(
        "units-of-measure/<int:pk>/delete/",
        views.UomDeleteView.as_view(),
        name="uom_delete",
    ),
    path("uom-conversions/", views.UomConversionListView.as_view(), name="uom_conversion_list"),
    path(
        "uom-conversions/add/",
        views.UomConversionCreateView.as_view(),
        name="uom_conversion_create",
    ),
    path(
        "uom-conversions/<int:pk>/edit/",
        views.UomConversionUpdateView.as_view(),
        name="uom_conversion_edit",
    ),
    path(
        "uom-conversions/<int:pk>/delete/",
        views.UomConversionDeleteView.as_view(),
        name="uom_conversion_delete",
    ),
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/add/", views.CustomerCreateView.as_view(), name="customer_create"),
    path(
        "customers/<int:pk>/edit/",
        views.CustomerUpdateView.as_view(),
        name="customer_edit",
    ),
    path(
        "customers/<int:pk>/delete/",
        views.CustomerDeleteView.as_view(),
        name="customer_delete",
    ),
    path("suppliers/", views.SupplierListView.as_view(), name="supplier_list"),
    path("suppliers/add/", views.SupplierCreateView.as_view(), name="supplier_create"),
    path(
        "suppliers/<int:pk>/edit/",
        views.SupplierUpdateView.as_view(),
        name="supplier_edit",
    ),
    path(
        "suppliers/<int:pk>/delete/",
        views.SupplierDeleteView.as_view(),
        name="supplier_delete",
    ),
    path("sales-persons/", views.SalesPersonListView.as_view(), name="sales_person_list"),
    path(
        "sales-persons/add/",
        views.SalesPersonCreateView.as_view(),
        name="sales_person_create",
    ),
    path(
        "sales-persons/<int:pk>/edit/",
        views.SalesPersonUpdateView.as_view(),
        name="sales_person_edit",
    ),
    path(
        "sales-persons/<int:pk>/delete/",
        views.SalesPersonDeleteView.as_view(),
        name="sales_person_delete",
    ),
    path(
        "payment-methods/",
        views.PaymentMethodListView.as_view(),
        name="payment_method_list",
    ),
    path(
        "payment-methods/add/",
        views.PaymentMethodCreateView.as_view(),
        name="payment_method_create",
    ),
    path(
        "payment-methods/<int:pk>/edit/",
        views.PaymentMethodUpdateView.as_view(),
        name="payment_method_edit",
    ),
    path(
        "payment-methods/<int:pk>/delete/",
        views.PaymentMethodDeleteView.as_view(),
        name="payment_method_delete",
    ),
    path("currencies/", views.CurrencyListView.as_view(), name="currency_list"),
    path("currencies/add/", views.CurrencyCreateView.as_view(), name="currency_create"),
    path(
        "currencies/<int:pk>/edit/",
        views.CurrencyUpdateView.as_view(),
        name="currency_edit",
    ),
    path(
        "currencies/<int:pk>/delete/",
        views.CurrencyDeleteView.as_view(),
        name="currency_delete",
    ),
    path("exchange-rates/", views.ExchangeRateListView.as_view(), name="exchange_rate_list"),
    path(
        "exchange-rates/add/",
        views.ExchangeRateCreateView.as_view(),
        name="exchange_rate_create",
    ),
    path(
        "exchange-rates/<int:pk>/edit/",
        views.ExchangeRateUpdateView.as_view(),
        name="exchange_rate_edit",
    ),
    path(
        "exchange-rates/<int:pk>/delete/",
        views.ExchangeRateDeleteView.as_view(),
        name="exchange_rate_delete",
    ),
    path("tax-types/", views.TaxTypeListView.as_view(), name="tax_type_list"),
    path("tax-types/add/", views.TaxTypeCreateView.as_view(), name="tax_type_create"),
    path(
        "tax-types/<int:pk>/edit/",
        views.TaxTypeUpdateView.as_view(),
        name="tax_type_edit",
    ),
    path(
        "tax-types/<int:pk>/delete/",
        views.TaxTypeDeleteView.as_view(),
        name="tax_type_delete",
    ),
    path("tax-rates/", views.TaxRateListView.as_view(), name="tax_rate_list"),
    path("tax-rates/add/", views.TaxRateCreateView.as_view(), name="tax_rate_create"),
    path(
        "tax-rates/<int:pk>/edit/",
        views.TaxRateUpdateView.as_view(),
        name="tax_rate_edit",
    ),
    path(
        "tax-rates/<int:pk>/delete/",
        views.TaxRateDeleteView.as_view(),
        name="tax_rate_delete",
    ),
    path("payment-terms/", views.PaymentTermListView.as_view(), name="payment_term_list"),
    path(
        "payment-terms/add/",
        views.PaymentTermCreateView.as_view(),
        name="payment_term_create",
    ),
    path(
        "payment-terms/<int:pk>/edit/",
        views.PaymentTermUpdateView.as_view(),
        name="payment_term_edit",
    ),
    path(
        "payment-terms/<int:pk>/delete/",
        views.PaymentTermDeleteView.as_view(),
        name="payment_term_delete",
    ),
]
