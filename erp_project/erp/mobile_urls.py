"""
ERP Mobile App URLs
"""
from django.urls import path
from erp.mobile_views.auth_views import ERPMobileLoginView, ERPMobileLogoutView
from erp.mobile_views.dashboard_views import ERPMobileDashboardView, ERPMobileMoreView
from erp.mobile_views.product_views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)
from erp.mobile_views.sales_views import (
    SalesOrderListView,
    SalesOrderDetailView,
    SalesOrderCreateView,
    SalesOrderUpdateView,
    SalesOrderDeleteView,
)
from erp.mobile_views.purchase_views import (
    PurchaseOrderListView,
    PurchaseOrderDetailView,
    PurchaseOrderCreateView,
    PurchaseOrderUpdateView,
    PurchaseOrderDeleteView,
)
from erp.mobile_views.expense_views import ExpenseListView, ExpenseDetailView
from erp.mobile_views.warehouse_views import WarehouseListView, WarehouseDetailView

# No app_name here - URLs will be accessed as erp:erp-mobile-*

urlpatterns = [
    # Auth
    path('', ERPMobileLoginView.as_view(), name='erp-mobile-login'),
    path('logout/', ERPMobileLogoutView.as_view(), name='erp-mobile-logout'),
    # Dashboard
    path('dashboard/', ERPMobileDashboardView.as_view(), name='erp-mobile-dashboard'),
    path('more/', ERPMobileMoreView.as_view(), name='erp-mobile-more'),
    # Products
    path('products/', ProductListView.as_view(), name='erp-mobile-products'),
    path('products/create/', ProductCreateView.as_view(), name='erp-mobile-product-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='erp-mobile-product-detail'),
    path(
        'products/<int:pk>/edit/',
        ProductUpdateView.as_view(),
        name='erp-mobile-product-edit',
    ),
    path(
        'products/<int:pk>/delete/',
        ProductDeleteView.as_view(),
        name='erp-mobile-product-delete',
    ),
    # Sales
    path('sales/', SalesOrderListView.as_view(), name='erp-mobile-sales'),
    path('sales/create/', SalesOrderCreateView.as_view(), name='erp-mobile-sales-create'),
    path(
        'sales/<int:pk>/', SalesOrderDetailView.as_view(), name='erp-mobile-sales-detail'
    ),
    path(
        'sales/<int:pk>/edit/',
        SalesOrderUpdateView.as_view(),
        name='erp-mobile-sales-edit',
    ),
    path(
        'sales/<int:pk>/delete/',
        SalesOrderDeleteView.as_view(),
        name='erp-mobile-sales-delete',
    ),
    # Orders (alias for sales)
    path('orders/', SalesOrderListView.as_view(), name='erp-mobile-orders'),
    path('orders/<int:pk>/', SalesOrderDetailView.as_view(), name='erp-mobile-order-detail'),
    # Purchases
    path('purchases/', PurchaseOrderListView.as_view(), name='erp-mobile-purchases'),
    path(
        'purchases/create/',
        PurchaseOrderCreateView.as_view(),
        name='erp-mobile-purchase-create',
    ),
    path(
        'purchases/<int:pk>/',
        PurchaseOrderDetailView.as_view(),
        name='erp-mobile-purchase-detail',
    ),
    path(
        'purchases/<int:pk>/edit/',
        PurchaseOrderUpdateView.as_view(),
        name='erp-mobile-purchase-edit',
    ),
    path(
        'purchases/<int:pk>/delete/',
        PurchaseOrderDeleteView.as_view(),
        name='erp-mobile-purchase-delete',
    ),
    # Expenses
    path('expenses/', ExpenseListView.as_view(), name='erp-mobile-expenses'),
    path(
        'expenses/<int:pk>/',
        ExpenseDetailView.as_view(),
        name='erp-mobile-expense-detail',
    ),
    # Warehouses
    path('warehouses/', WarehouseListView.as_view(), name='erp-mobile-warehouses'),
    path(
        'warehouses/<int:pk>/',
        WarehouseDetailView.as_view(),
        name='erp-mobile-warehouse-detail',
    ),
]
