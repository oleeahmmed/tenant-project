"""
URL configuration for erp app
"""
from django.urls import path, include

# Dashboard views
from .views.dashboards import (
    DashboardView,
    SalesDashboardView,
    PurchaseDashboardView,
    POSDashboardView,
    InventoryDashboardView,
    ManufacturingDashboardView,
)

# Modern POS views
from .views.pos_views import (
    ModernPOSView,
    POSCreateSaleView,
    POSSearchProductView,
    POSGetProductView,
    POSSessionView,
    POSReturnView,
)

# Other views
from .views import (
    PrintSalesOrderView, PrintSalesQuotationView, PrintDeliveryView,
    PrintInvoiceView, PrintSalesReturnView, PrintIncomingPaymentView,
    PrintQuickSaleView,
    # Purchase print views
    PrintPurchaseQuotationView, PrintPurchaseOrderView, PrintGoodsReceiptView,
    PrintGoodsReceiptPOView, PrintPurchaseInvoiceView, PrintPurchaseReturnView,
    PrintOutgoingPaymentView,
    # Manufacturing print views
    PrintBOMView, PrintProductionOrderView, PrintProductionReceiptView, PrintProductionIssueView,
    get_product_price, get_product_by_sku, get_sales_order_details, get_purchase_order_details,
    get_sales_quotation_details, get_purchase_quotation_details,
    get_customer_details, get_customer_by_phone,
    # Copy/Create views
    copy_sales_quotation_to_order_view, copy_sales_order_to_delivery_view,
    copy_sales_order_to_invoice_view, copy_sales_order_to_return_view,
    copy_purchase_quotation_to_order_view, copy_purchase_order_to_receipt_view,
    copy_purchase_order_to_invoice_view, copy_purchase_order_to_return_view,
    copy_bom_to_production_order_view, copy_production_order_to_receipt_view
)

# API Views for autocomplete - removed duplicates, using consolidated autocomplete_views.py

# Guide views
from .views.guides import (
    StockMovementGuideView,
    ExpenseManagementGuideView,
    IncomeManagementGuideView,
    InventoryManagementGuideView,
    ProductionManagementGuideView,
    SalesManagementGuideView,
    BankingManagementGuideView,
    QualityServiceManagementGuideView,
)

# Sales Reports - Optimized with Background Tasks
from .views.reports import (
    # Sales Quotation Reports
    SalesQuotationDetailReportView,
    SalesQuotationSummaryReportView,
    StartDetailReportTaskView,
    StartSummaryReportTaskView,
    CheckTaskStatusView,
    # Sales Order Reports
    SalesOrderDetailReportView,
    SalesOrderSummaryReportView,
    StartSalesOrderDetailReportTaskView,
    StartSalesOrderSummaryReportTaskView,
    # Point of Sales Reports
    QuickSaleDetailReportView,
    QuickSaleSummaryReportView,
    StartQuickSaleDetailReportTaskView,
    StartQuickSaleSummaryReportTaskView,
    # Purchase Order Reports
    PurchaseOrderDetailReportView,
    PurchaseOrderSummaryReportView,
    StartPurchaseOrderDetailReportTaskView,
    StartPurchaseOrderSummaryReportTaskView,
    # Purchase Invoice Reports
    PurchaseInvoiceDetailReportView,
    PurchaseInvoiceSummaryReportView,
    StartPurchaseInvoiceDetailReportTaskView,
    StartPurchaseInvoiceSummaryReportTaskView,
    # Sales Invoice Reports
    SalesInvoiceDetailReportView,
    SalesInvoiceSummaryReportView,
    StartSalesInvoiceDetailReportTaskView,
    StartSalesInvoiceSummaryReportTaskView,
)

# Financial Reports - Optimized with Background Tasks
from .views.reports.financial_reports import (
    # Trial Balance
    TrialBalanceReportView,
    StartTrialBalanceReportTaskView,
    CheckTrialBalanceTaskStatusView,
    # Profit & Loss
    ProfitLossReportView,
    StartProfitLossReportTaskView,
    CheckProfitLossTaskStatusView,
    # Balance Sheet
    BalanceSheetReportView,
    StartBalanceSheetReportTaskView,
    CheckBalanceSheetTaskStatusView,
    # General Ledger
    GeneralLedgerReportView,
    StartGeneralLedgerReportTaskView,
    CheckGeneralLedgerTaskStatusView,
    # Account Statement
    AccountStatementReportView,
    StartAccountStatementReportTaskView,
    CheckAccountStatementTaskStatusView,
    # Common Task Status
    FinancialReportTaskStatusView,
)

# Autocomplete views for filters
from .views.reports.autocomplete_views import (
    CustomerAutocompleteView,
    SalespersonAutocompleteView,
    ProductAutocompleteView,
    CashierAutocompleteView,
    SupplierAutocompleteView,
    AccountTypeAutocompleteView,
    AccountAutocompleteView,
    WarehouseAutocompleteView,
    CategoryAutocompleteView,
    PaymentMethodAutocompleteView,
    TaxRateAutocompleteView,
    CurrencyAutocompleteView,
)

# Dashboard views and their background task views
from .views.dashboards.user_pos_dashboard import UserPOSDashboardView

from .views.dashboards.sales_dashboard import (
    SalesDashboardView,
    StartDashboardDataTaskView,
    CheckDashboardTaskStatusView,
)

from .views.dashboards.purchase_dashboard import (
    PurchaseDashboardView,
    StartPurchaseDashboardDataTaskView,
    CheckPurchaseDashboardTaskStatusView,
)

from .views.dashboards.pos_dashboard import (
    POSDashboardView,
    StartPOSDashboardDataTaskView,
    CheckPOSDashboardTaskStatusView,
)

from .views.dashboards.inventory_dashboard import (
    InventoryDashboardView,
    StartInventoryDashboardDataTaskView,
    CheckInventoryDashboardTaskStatusView,
)

from .views.dashboards.manufacturing_dashboard import (
    ManufacturingDashboardView,
    StartManufacturingDashboardDataTaskView,
    CheckManufacturingDashboardTaskStatusView,
)

from .views.dashboards.financial_dashboard import (
    FinancialDashboardView,
    StartFinancialDashboardDataTaskView,
    CheckFinancialDashboardTaskStatusView,
)

# Expense views
from .views.expense_views import (
    simple_expense_entry,
    expense_list,
)

# Frontend views
from .views.frontend_views import (
    CategoryListView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDeleteView,
    CategoryDetailView,
    WarehouseListView,
    WarehouseCreateView,
    WarehouseUpdateView,
    WarehouseDeleteView,
    WarehouseDetailView,
    ProductListView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    ProductDetailView,
    CompanyListView,
    CompanyCreateView,
    CompanyUpdateView,
    CompanyDeleteView,
    CompanyDetailView,
    CustomerListView,
    CustomerCreateView,
    CustomerUpdateView,
    CustomerDeleteView,
    CustomerDetailView,
    SupplierListView,
    SupplierCreateView,
    SupplierUpdateView,
    SupplierDeleteView,
    SupplierDetailView,
    SalesPersonListView,
    SalesPersonCreateView,
    SalesPersonUpdateView,
    SalesPersonDeleteView,
    SalesPersonDetailView,
    PaymentMethodListView,
    PaymentMethodCreateView,
    PaymentMethodUpdateView,
    PaymentMethodDeleteView,
    PaymentMethodDetailView,
    UnitOfMeasureListView,
    UnitOfMeasureCreateView,
    UnitOfMeasureUpdateView,
    UnitOfMeasureDeleteView,
    UnitOfMeasureDetailView,
)

# POS Frontend views
from .views.pos_frontend_views import (
    QuickSaleListView,
    QuickSaleDetailView,
    QuickSaleDeleteView,
    pos_entry_view,
    pos_create_sale,
    pos_search_product,
    pos_get_product,
    pos_session_management,
)

# Sales Order Frontend views
from .views.sales_order_views import (
    SalesOrderListView,
    SalesOrderDetailView,
    SalesOrderDeleteView,
    salesorder_create,
    salesorder_update,
)

# Purchase Order Frontend views
from .views.purchase_order_views import (
    PurchaseOrderListView,
    PurchaseOrderDetailView,
    PurchaseOrderDeleteView,
    purchaseorder_create,
    purchaseorder_update,
)

app_name = 'erp'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('sales-dashboard/', SalesDashboardView.as_view(), name='sales-dashboard'),
    path('api/sales-dashboard/start/', StartDashboardDataTaskView.as_view(), name='start-sales-dashboard-task'),
    path('api/sales-dashboard/status/<str:task_id>/', CheckDashboardTaskStatusView.as_view(), name='check-sales-dashboard-status'),
    path('purchase-dashboard/', PurchaseDashboardView.as_view(), name='purchase-dashboard'),
    path('api/purchase-dashboard/start/', StartPurchaseDashboardDataTaskView.as_view(), name='start-purchase-dashboard-task'),
    path('api/purchase-dashboard/status/<str:task_id>/', CheckPurchaseDashboardTaskStatusView.as_view(), name='check-purchase-dashboard-status'),
    path('pos-dashboard/', POSDashboardView.as_view(), name='pos-dashboard'),
    path('api/pos-dashboard/start/', StartPOSDashboardDataTaskView.as_view(), name='start-pos-dashboard-task'),
    path('api/pos-dashboard/status/<str:task_id>/', CheckPOSDashboardTaskStatusView.as_view(), name='check-pos-dashboard-status'),
    
    # User-Specific POS Dashboard
    path('user-pos-dashboard/', UserPOSDashboardView.as_view(), name='user-pos-dashboard'),
    
    # Modern POS Interface
    path('pos/', ModernPOSView.as_view(), name='modern-pos'),
    path('pos/edit/<int:sale_id>/', ModernPOSView.as_view(), name='modern-pos-edit'),
    path('api/pos/create-sale/', POSCreateSaleView.as_view(), name='pos-create-sale'),
    path('api/pos/search-product/', POSSearchProductView.as_view(), name='pos-search-product'),
    path('api/pos/product/<int:product_id>/', POSGetProductView.as_view(), name='pos-get-product'),
    path('api/pos/session/', POSSessionView.as_view(), name='pos-session'),
    path('api/pos/return/', POSReturnView.as_view(), name='pos-return'),
    
    path('inventory-dashboard/', InventoryDashboardView.as_view(), name='inventory-dashboard'),
    path('api/inventory-dashboard/start/', StartInventoryDashboardDataTaskView.as_view(), name='start-inventory-dashboard-task'),
    path('api/inventory-dashboard/status/<str:task_id>/', CheckInventoryDashboardTaskStatusView.as_view(), name='check-inventory-dashboard-status'),
    path('manufacturing-dashboard/', ManufacturingDashboardView.as_view(), name='manufacturing-dashboard'),
    path('api/manufacturing-dashboard/start/', StartManufacturingDashboardDataTaskView.as_view(), name='start-manufacturing-dashboard-task'),
    path('api/manufacturing-dashboard/status/<str:task_id>/', CheckManufacturingDashboardTaskStatusView.as_view(), name='check-manufacturing-dashboard-status'),
    path('financial-dashboard/', FinancialDashboardView.as_view(), name='financial-dashboard'),
    path('api/financial-dashboard/start/', StartFinancialDashboardDataTaskView.as_view(), name='start-financial-dashboard-task'),
    path('api/financial-dashboard/status/<str:task_id>/', CheckFinancialDashboardTaskStatusView.as_view(), name='check-financial-dashboard-status'),
    
    # Guide URLs
    path('stock-movement-guide/', StockMovementGuideView.as_view(), name='stock-movement-guide'),
    path('expense-management-guide/', ExpenseManagementGuideView.as_view(), name='expense-management-guide'),
    path('income-management-guide/', IncomeManagementGuideView.as_view(), name='income-management-guide'),
    path('inventory-management-guide/', InventoryManagementGuideView.as_view(), name='inventory-management-guide'),
    path('production-management-guide/', ProductionManagementGuideView.as_view(), name='production-management-guide'),
    path('sales-management-guide/', SalesManagementGuideView.as_view(), name='sales-management-guide'),
    path('banking-management-guide/', BankingManagementGuideView.as_view(), name='banking-management-guide'),
    path('quality-service-management-guide/', QualityServiceManagementGuideView.as_view(), name='quality-service-management-guide'),
    
    # Print URLs - Sales
    path('sales-order/<int:order_id>/print/', PrintSalesOrderView.as_view(), name='print-sales-order'),
    path('sales-quotation/<int:quotation_id>/print/', PrintSalesQuotationView.as_view(), name='print-sales-quotation'),
    path('delivery/<int:delivery_id>/print/', PrintDeliveryView.as_view(), name='print-delivery'),
    path('invoice/<int:invoice_id>/print/', PrintInvoiceView.as_view(), name='print-invoice'),
    path('sales-return/<int:return_id>/print/', PrintSalesReturnView.as_view(), name='print-sales-return'),
    path('incoming-payment/<int:payment_id>/print/', PrintIncomingPaymentView.as_view(), name='print-incoming-payment'),
    path('quick-sale/<int:sale_id>/print/', PrintQuickSaleView.as_view(), name='print-quick-sale'),
    
    # Print URLs - Purchase
    path('purchase-quotation/<int:quotation_id>/print/', PrintPurchaseQuotationView.as_view(), name='print-purchase-quotation'),
    path('purchase-order/<int:order_id>/print/', PrintPurchaseOrderView.as_view(), name='print-purchase-order'),
    path('goods-receipt/<int:receipt_id>/print/', PrintGoodsReceiptView.as_view(), name='print-goods-receipt'),
    path('goods-receipt-po/<int:receipt_id>/print/', PrintGoodsReceiptPOView.as_view(), name='print-goods-receipt-po'),
    path('purchase-invoice/<int:invoice_id>/print/', PrintPurchaseInvoiceView.as_view(), name='print-purchase-invoice'),
    path('purchase-return/<int:return_id>/print/', PrintPurchaseReturnView.as_view(), name='print-purchase-return'),
    path('outgoing-payment/<int:payment_id>/print/', PrintOutgoingPaymentView.as_view(), name='print-outgoing-payment'),
    
    # Print URLs - Manufacturing
    path('bom/<int:bom_id>/print/', PrintBOMView.as_view(), name='print-bom'),
    path('production-order/<int:order_id>/print/', PrintProductionOrderView.as_view(), name='print-production-order'),
    path('production-receipt/<int:receipt_id>/print/', PrintProductionReceiptView.as_view(), name='print-production-receipt'),
    path('production-issue/<int:issue_id>/print/', PrintProductionIssueView.as_view(), name='print-production-issue'),
    
    # API Endpoints
    path('api/product/<int:product_id>/price/', get_product_price, name='get-product-price'),
    path('api/product/by-sku/', get_product_by_sku, name='get-product-by-sku'),
    path('api/customers/<int:customer_id>/', get_customer_details, name='get-customer-details'),
    path('api/customers/by-phone/', get_customer_by_phone, name='get-customer-by-phone'),
    path('api/sales-order/<int:sales_order_id>/details/', get_sales_order_details, name='get-sales-order-details'),
    path('api/purchase-order/<int:purchase_order_id>/details/', get_purchase_order_details, name='get-purchase-order-details'),
    path('api/sales-quotation/<int:sales_quotation_id>/details/', get_sales_quotation_details, name='get-sales-quotation-details'),
    path('api/purchase-quotation/<int:purchase_quotation_id>/details/', get_purchase_quotation_details, name='get-purchase-quotation-details'),
    
    # Copy/Create Actions - Sales Module
    path('sales-quotation/<int:quotation_id>/create-order/', copy_sales_quotation_to_order_view, name='copy-sales-quotation-to-order'),
    path('sales-order/<int:order_id>/create-delivery/', copy_sales_order_to_delivery_view, name='copy-sales-order-to-delivery'),
    path('sales-order/<int:order_id>/create-invoice/', copy_sales_order_to_invoice_view, name='copy-sales-order-to-invoice'),
    path('sales-order/<int:order_id>/create-return/', copy_sales_order_to_return_view, name='copy-sales-order-to-return'),
    
    # Copy/Create Actions - Purchase Module
    path('purchase-quotation/<int:quotation_id>/create-order/', copy_purchase_quotation_to_order_view, name='copy-purchase-quotation-to-order'),
    path('purchase-order/<int:order_id>/create-receipt/', copy_purchase_order_to_receipt_view, name='copy-purchase-order-to-receipt'),
    path('purchase-order/<int:order_id>/create-invoice/', copy_purchase_order_to_invoice_view, name='copy-purchase-order-to-invoice'),
    path('purchase-order/<int:order_id>/create-return/', copy_purchase_order_to_return_view, name='copy-purchase-order-to-return'),
    
    # Copy/Create Actions - Production Module
    path('bom/<int:bom_id>/create-production-order/', copy_bom_to_production_order_view, name='copy-bom-to-production-order'),
    path('production-order/<int:order_id>/create-receipt/', copy_production_order_to_receipt_view, name='copy-production-order-to-receipt'),
    
    # ==================== AUTOCOMPLETE APIs ====================
    # Fast autocomplete for report filters and admin forms - all consolidated in autocomplete_views.py
    path('api/autocomplete/customers/', CustomerAutocompleteView.as_view(), name='autocomplete-customers'),
    path('api/autocomplete/salespersons/', SalespersonAutocompleteView.as_view(), name='autocomplete-salespersons'),
    path('api/autocomplete/products/', ProductAutocompleteView.as_view(), name='autocomplete-products'),
    path('api/autocomplete/cashiers/', CashierAutocompleteView.as_view(), name='autocomplete-cashiers'),
    path('api/autocomplete/suppliers/', SupplierAutocompleteView.as_view(), name='autocomplete-suppliers'),
    path('api/autocomplete/account-types/', AccountTypeAutocompleteView.as_view(), name='autocomplete-account-types'),
    path('api/autocomplete/accounts/', AccountAutocompleteView.as_view(), name='autocomplete-accounts'),
    path('api/autocomplete/warehouses/', WarehouseAutocompleteView.as_view(), name='autocomplete-warehouses'),
    path('api/autocomplete/categories/', CategoryAutocompleteView.as_view(), name='autocomplete-categories'),
    path('api/autocomplete/payment-methods/', PaymentMethodAutocompleteView.as_view(), name='autocomplete-payment-methods'),
    path('api/autocomplete/tax-rates/', TaxRateAutocompleteView.as_view(), name='autocomplete-tax-rates'),
    path('api/autocomplete/currencies/', CurrencyAutocompleteView.as_view(), name='autocomplete-currencies'),
    
    # ==================== SALES QUOTATION REPORTS (OPTIMIZED) ====================
    # Sales Quotation Reports with Background Tasks & Caching
    path('reports/sales/quotations/detail/', SalesQuotationDetailReportView.as_view(), name='sales-quotation-detail-report'),
    path('reports/sales/quotations/summary/', SalesQuotationSummaryReportView.as_view(), name='sales-quotation-summary-report'),
    
    # Background Task API Endpoints
    path('api/reports/sales-quotation/detail/start/', StartDetailReportTaskView.as_view(), name='start-detail-report-task'),
    path('api/reports/sales-quotation/summary/start/', StartSummaryReportTaskView.as_view(), name='start-summary-report-task'),
    path('api/reports/task-status/<str:task_id>/', CheckTaskStatusView.as_view(), name='check-task-status'),
    
    # ==================== SALES ORDER REPORTS (OPTIMIZED) ====================
    # Sales Order Reports with Background Tasks & Caching
    path('reports/sales/orders/detail/', SalesOrderDetailReportView.as_view(), name='sales-order-detail-report'),
    path('reports/sales/orders/summary/', SalesOrderSummaryReportView.as_view(), name='sales-order-summary-report'),
    
    # Background Task API Endpoints
    path('api/reports/sales-order/detail/start/', StartSalesOrderDetailReportTaskView.as_view(), name='start-sales-order-detail-report-task'),
    path('api/reports/sales-order/summary/start/', StartSalesOrderSummaryReportTaskView.as_view(), name='start-sales-order-summary-report-task'),
    
    # ==================== POINT OF SALES REPORTS (OPTIMIZED) ====================
    # POS Reports with Background Tasks & Caching
    path('reports/pos/detail/', QuickSaleDetailReportView.as_view(), name='pos-detail-report'),
    path('reports/pos/summary/', QuickSaleSummaryReportView.as_view(), name='pos-summary-report'),
    
    # Background Task API Endpoints
    path('api/reports/pos/detail/start/', StartQuickSaleDetailReportTaskView.as_view(), name='start-pos-detail-report-task'),
    path('api/reports/pos/summary/start/', StartQuickSaleSummaryReportTaskView.as_view(), name='start-pos-summary-report-task'),
    
    # ==================== PURCHASE ORDER REPORTS (OPTIMIZED) ====================
    # Purchase Order Reports with Background Tasks & Caching
    path('reports/purchase/orders/detail/', PurchaseOrderDetailReportView.as_view(), name='purchase-order-detail-report'),
    path('reports/purchase/orders/summary/', PurchaseOrderSummaryReportView.as_view(), name='purchase-order-summary-report'),
    
    # Background Task API Endpoints
    path('api/reports/purchase-order/detail/start/', StartPurchaseOrderDetailReportTaskView.as_view(), name='start-purchase-order-detail-report-task'),
    path('api/reports/purchase-order/summary/start/', StartPurchaseOrderSummaryReportTaskView.as_view(), name='start-purchase-order-summary-report-task'),
    
    # ==================== PURCHASE INVOICE REPORTS (OPTIMIZED) ====================
    # Purchase Invoice Reports with Background Tasks & Caching
    path('reports/purchase/invoices/detail/', PurchaseInvoiceDetailReportView.as_view(), name='purchase-invoice-detail-report'),
    path('reports/purchase/invoices/summary/', PurchaseInvoiceSummaryReportView.as_view(), name='purchase-invoice-summary-report'),
    
    # Background Task API Endpoints
    path('api/reports/purchase-invoice/detail/start/', StartPurchaseInvoiceDetailReportTaskView.as_view(), name='start-purchase-invoice-detail-report-task'),
    path('api/reports/purchase-invoice/summary/start/', StartPurchaseInvoiceSummaryReportTaskView.as_view(), name='start-purchase-invoice-summary-report-task'),
    
    # ==================== SALES INVOICE REPORTS (OPTIMIZED) ====================
    # Sales Invoice Reports with Background Tasks & Caching
    path('reports/sales/invoices/detail/', SalesInvoiceDetailReportView.as_view(), name='sales-invoice-detail-report'),
    path('reports/sales/invoices/summary/', SalesInvoiceSummaryReportView.as_view(), name='sales-invoice-summary-report'),
    
    # Background Task API Endpoints
    path('api/reports/sales-invoice/detail/start/', StartSalesInvoiceDetailReportTaskView.as_view(), name='start-sales-invoice-detail-report-task'),
    path('api/reports/sales-invoice/summary/start/', StartSalesInvoiceSummaryReportTaskView.as_view(), name='start-sales-invoice-summary-report-task'),
    
    # ==================== FINANCIAL REPORTS (OPTIMIZED) ====================
    # Trial Balance
    path('reports/financial/trial-balance/', TrialBalanceReportView.as_view(), name='trial-balance-report'),
    path('api/reports/financial/trial-balance/start/', StartTrialBalanceReportTaskView.as_view(), name='trial-balance-start'),
    path('api/reports/financial/trial-balance/status/<str:task_id>/', CheckTrialBalanceTaskStatusView.as_view(), name='trial-balance-status'),
    
    # Profit & Loss Statement
    path('reports/financial/profit-loss/', ProfitLossReportView.as_view(), name='profit-loss-report'),
    path('api/reports/financial/profit-loss/start/', StartProfitLossReportTaskView.as_view(), name='profit-loss-start'),
    path('api/reports/financial/profit-loss/status/<str:task_id>/', CheckProfitLossTaskStatusView.as_view(), name='profit-loss-status'),
    
    # Balance Sheet
    path('reports/financial/balance-sheet/', BalanceSheetReportView.as_view(), name='balance-sheet-report'),
    path('api/reports/financial/balance-sheet/start/', StartBalanceSheetReportTaskView.as_view(), name='balance-sheet-start'),
    path('api/reports/financial/balance-sheet/status/<str:task_id>/', CheckBalanceSheetTaskStatusView.as_view(), name='balance-sheet-status'),
    
    # General Ledger
    path('reports/financial/general-ledger/', GeneralLedgerReportView.as_view(), name='general-ledger-report'),
    path('api/reports/financial/general-ledger/start/', StartGeneralLedgerReportTaskView.as_view(), name='general-ledger-start'),
    path('api/reports/financial/general-ledger/status/<str:task_id>/', CheckGeneralLedgerTaskStatusView.as_view(), name='general-ledger-status'),
    
    # Account Statement
    path('reports/financial/account-statement/', AccountStatementReportView.as_view(), name='account-statement-report'),
    path('api/reports/financial/account-statement/start/', StartAccountStatementReportTaskView.as_view(), name='account-statement-start'),
    path('api/reports/financial/account-statement/status/<str:task_id>/', CheckAccountStatementTaskStatusView.as_view(), name='account-statement-status'),
    
    # Common Financial Report Task Status (for backward compatibility)
    path('api/reports/financial/task-status/<str:task_id>/', FinancialReportTaskStatusView.as_view(), name='financial-task-status'),
    
    # ==================== EXPENSE MANAGEMENT ====================
    # Simple Expense Entry System
    path('expense/entry/', simple_expense_entry, name='simple-expense-entry'),
    path('expense/list/', expense_list, name='expense-list'),
    
    # ==================== CATEGORY MANAGEMENT (FRONTEND) ====================
    # Category CRUD Operations - Class-Based Views
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category_detail'),
    path('categories/<int:pk>/update/', CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
    
    # ==================== WAREHOUSE MANAGEMENT (FRONTEND) ====================
    # Warehouse CRUD Operations - Class-Based Views
    path('warehouses/', WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/create/', WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/', WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouses/<int:pk>/update/', WarehouseUpdateView.as_view(), name='warehouse_update'),
    path('warehouses/<int:pk>/delete/', WarehouseDeleteView.as_view(), name='warehouse_delete'),
    
    # ==================== PRODUCT MANAGEMENT (FRONTEND) ====================
    # Product CRUD Operations - Class-Based Views
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/create/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/update/', ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    
    # ==================== COMPANY MANAGEMENT (FRONTEND) ====================
    # Company CRUD Operations - Class-Based Views
    path('companies/', CompanyListView.as_view(), name='company_list'),
    path('companies/create/', CompanyCreateView.as_view(), name='company_create'),
    path('companies/<int:pk>/', CompanyDetailView.as_view(), name='company_detail'),
    path('companies/<int:pk>/update/', CompanyUpdateView.as_view(), name='company_update'),
    path('companies/<int:pk>/delete/', CompanyDeleteView.as_view(), name='company_delete'),
    
    # ==================== CUSTOMER MANAGEMENT (FRONTEND) ====================
    # Customer CRUD Operations - Class-Based Views
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/update/', CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer_delete'),
    
    # ==================== SUPPLIER MANAGEMENT (FRONTEND) ====================
    # Supplier CRUD Operations - Class-Based Views
    path('suppliers/', SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/', SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:pk>/update/', SupplierUpdateView.as_view(), name='supplier_update'),
    path('suppliers/<int:pk>/delete/', SupplierDeleteView.as_view(), name='supplier_delete'),
    
    # ==================== SALESPERSON MANAGEMENT (FRONTEND) ====================
    # SalesPerson CRUD Operations - Class-Based Views
    path('salespersons/', SalesPersonListView.as_view(), name='salesperson_list'),
    path('salespersons/create/', SalesPersonCreateView.as_view(), name='salesperson_create'),
    path('salespersons/<int:pk>/', SalesPersonDetailView.as_view(), name='salesperson_detail'),
    path('salespersons/<int:pk>/update/', SalesPersonUpdateView.as_view(), name='salesperson_update'),
    path('salespersons/<int:pk>/delete/', SalesPersonDeleteView.as_view(), name='salesperson_delete'),
    
    # ==================== PAYMENT METHOD MANAGEMENT (FRONTEND) ====================
    # PaymentMethod CRUD Operations - Class-Based Views
    path('payment-methods/', PaymentMethodListView.as_view(), name='paymentmethod_list'),
    path('payment-methods/create/', PaymentMethodCreateView.as_view(), name='paymentmethod_create'),
    path('payment-methods/<int:pk>/', PaymentMethodDetailView.as_view(), name='paymentmethod_detail'),
    path('payment-methods/<int:pk>/update/', PaymentMethodUpdateView.as_view(), name='paymentmethod_update'),
    path('payment-methods/<int:pk>/delete/', PaymentMethodDeleteView.as_view(), name='paymentmethod_delete'),
    
    # ==================== UNIT OF MEASURE MANAGEMENT (FRONTEND) ====================
    # UnitOfMeasure CRUD Operations - Class-Based Views
    path('units-of-measure/', UnitOfMeasureListView.as_view(), name='unitofmeasure_list'),
    path('units-of-measure/create/', UnitOfMeasureCreateView.as_view(), name='unitofmeasure_create'),
    path('units-of-measure/<int:pk>/', UnitOfMeasureDetailView.as_view(), name='unitofmeasure_detail'),
    path('units-of-measure/<int:pk>/update/', UnitOfMeasureUpdateView.as_view(), name='unitofmeasure_update'),
    path('units-of-measure/<int:pk>/delete/', UnitOfMeasureDeleteView.as_view(), name='unitofmeasure_delete'),
    
    # ==================== POS / QUICK SALE MANAGEMENT (FRONTEND) ====================
    # QuickSale CRUD Operations - Professional POS System
    path('pos/sales/', QuickSaleListView.as_view(), name='quicksale_list'),
    path('pos/sales/<int:pk>/', QuickSaleDetailView.as_view(), name='quicksale_detail'),
    path('pos/sales/<int:pk>/delete/', QuickSaleDeleteView.as_view(), name='quicksale_delete'),
    path('pos/entry/', pos_entry_view, name='pos_entry'),
    
    # POS API Endpoints
    path('api/pos/create-sale/', pos_create_sale, name='pos-create-sale'),
    path('api/pos/search-product/', pos_search_product, name='pos-search-product'),
    path('api/pos/product/<int:product_id>/', pos_get_product, name='pos-get-product'),
    path('api/pos/session/', pos_session_management, name='pos-session'),
    
    # ==================== SALES ORDER MANAGEMENT (FRONTEND) ====================
    # SalesOrder CRUD Operations with Formset
    path('sales-orders/', SalesOrderListView.as_view(), name='salesorder_list'),
    path('sales-orders/create/', salesorder_create, name='salesorder_create'),
    path('sales-orders/<int:pk>/', SalesOrderDetailView.as_view(), name='salesorder_detail'),
    path('sales-orders/<int:pk>/update/', salesorder_update, name='salesorder_update'),
    path('sales-orders/<int:pk>/delete/', SalesOrderDeleteView.as_view(), name='salesorder_delete'),
    
    # ==================== PURCHASE ORDER MANAGEMENT (FRONTEND) ====================
    # PurchaseOrder CRUD Operations with Formset
    path('purchase-orders/', PurchaseOrderListView.as_view(), name='purchaseorder_list'),
    path('purchase-orders/create/', purchaseorder_create, name='purchaseorder_create'),
    path('purchase-orders/<int:pk>/', PurchaseOrderDetailView.as_view(), name='purchaseorder_detail'),
    path('purchase-orders/<int:pk>/update/', purchaseorder_update, name='purchaseorder_update'),
    path('purchase-orders/<int:pk>/delete/', PurchaseOrderDeleteView.as_view(), name='purchaseorder_delete'),
    
    # POS API Endpoints
    path('api/pos/create-sale/', pos_create_sale, name='pos-create-sale'),
    path('api/pos/search-product/', pos_search_product, name='pos-search-product'),
    path('api/pos/product/<int:product_id>/', pos_get_product, name='pos-get-product'),
    path('api/pos/session/', pos_session_management, name='pos-session'),
    
    # ==================== MOBILE APP ====================
    # ERP Mobile Application
    path('mobile/', include('erp.mobile_urls')),
]