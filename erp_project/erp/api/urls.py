"""
ERP API URLs - All endpoints registered with DefaultRouter
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # Foundation & Setup
    CompanyViewSet, WarehouseViewSet, CategoryViewSet, ProductViewSet,
    CustomerViewSet, SupplierViewSet, SalesPersonViewSet, PaymentMethodViewSet,
    UnitOfMeasureViewSet, UOMConversionViewSet,
    # Financial Foundation
    CurrencyViewSet, ExchangeRateViewSet, TaxTypeViewSet, TaxRateViewSet,
    PaymentTermViewSet, PriceListViewSet, PriceListItemViewSet,
    BankAccountViewSet, AccountTypeViewSet, ChartOfAccountsViewSet,
    CostCenterViewSet, ProjectViewSet, FiscalYearViewSet,
    # Sales Process
    SalesQuotationViewSet, SalesQuotationItemViewSet,
    SalesOrderViewSet, SalesOrderItemViewSet,
    DeliveryViewSet, DeliveryItemViewSet,
    InvoiceViewSet, InvoiceItemViewSet,
    SalesReturnViewSet, SalesReturnItemViewSet,
    IncomingPaymentViewSet, IncomingPaymentInvoiceViewSet,
    # Purchase Process
    PurchaseQuotationViewSet, PurchaseQuotationItemViewSet,
    PurchaseOrderViewSet, PurchaseOrderItemViewSet,
    GoodsReceiptViewSet, GoodsReceiptItemViewSet,
    PurchaseInvoiceViewSet, PurchaseInvoiceItemViewSet,
    PurchaseReturnViewSet, PurchaseReturnItemViewSet,
    OutgoingPaymentViewSet, OutgoingPaymentInvoiceViewSet,
    # Manufacturing
    BillOfMaterialsViewSet, BOMComponentViewSet,
    ProductionOrderViewSet, ProductionOrderComponentViewSet,
    ProductionReceiptViewSet, ProductionReceiptItemViewSet,
    # Inventory Control
    StockAdjustmentViewSet, StockAdjustmentItemViewSet,
    GoodsIssueViewSet, GoodsIssueItemViewSet,
    InventoryTransferViewSet, InventoryTransferItemViewSet,
    ProductWarehouseStockViewSet, StockTransactionViewSet,
    # Accounting
    JournalEntryViewSet, JournalEntryLineViewSet, BudgetViewSet,
    # Discount Management
    DiscountTypeViewSet, DiscountRuleViewSet,
    # Approval Workflow
    ApprovalWorkflowViewSet, ApprovalLevelViewSet, ApprovalRequestViewSet,
    # Notifications
    NotificationTypeViewSet, NotificationViewSet,
    AlertRuleViewSet, NotificationSettingViewSet,
    # POS
    QuickSaleViewSet, QuickSaleItemViewSet, UserProfileViewSet,
)

router = DefaultRouter()

# ==================== FOUNDATION & SETUP ====================
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'salespersons', SalesPersonViewSet, basename='salesperson')
router.register(r'payment-methods', PaymentMethodViewSet, basename='paymentmethod')
router.register(r'units-of-measure', UnitOfMeasureViewSet, basename='unitofmeasure')
router.register(r'uom-conversions', UOMConversionViewSet, basename='uomconversion')

# ==================== FINANCIAL FOUNDATION ====================
router.register(r'currencies', CurrencyViewSet, basename='currency')
router.register(r'exchange-rates', ExchangeRateViewSet, basename='exchangerate')
router.register(r'tax-types', TaxTypeViewSet, basename='taxtype')
router.register(r'tax-rates', TaxRateViewSet, basename='taxrate')
router.register(r'payment-terms', PaymentTermViewSet, basename='paymentterm')
router.register(r'price-lists', PriceListViewSet, basename='pricelist')
router.register(r'price-list-items', PriceListItemViewSet, basename='pricelistitem')
router.register(r'bank-accounts', BankAccountViewSet, basename='bankaccount')
router.register(r'account-types', AccountTypeViewSet, basename='accounttype')
router.register(r'chart-of-accounts', ChartOfAccountsViewSet, basename='chartofaccounts')
router.register(r'cost-centers', CostCenterViewSet, basename='costcenter')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'fiscal-years', FiscalYearViewSet, basename='fiscalyear')

# ==================== SALES PROCESS ====================
router.register(r'sales-quotations', SalesQuotationViewSet, basename='salesquotation')
router.register(r'sales-quotation-items', SalesQuotationItemViewSet, basename='salesquotationitem')
router.register(r'sales-orders', SalesOrderViewSet, basename='salesorder')
router.register(r'sales-order-items', SalesOrderItemViewSet, basename='salesorderitem')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')
router.register(r'delivery-items', DeliveryItemViewSet, basename='deliveryitem')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-items', InvoiceItemViewSet, basename='invoiceitem')
router.register(r'sales-returns', SalesReturnViewSet, basename='salesreturn')
router.register(r'sales-return-items', SalesReturnItemViewSet, basename='salesreturnitem')
router.register(r'incoming-payments', IncomingPaymentViewSet, basename='incomingpayment')
router.register(r'incoming-payment-invoices', IncomingPaymentInvoiceViewSet, basename='incomingpaymentinvoice')

# ==================== PURCHASE PROCESS ====================
router.register(r'purchase-quotations', PurchaseQuotationViewSet, basename='purchasequotation')
router.register(r'purchase-quotation-items', PurchaseQuotationItemViewSet, basename='purchasequotationitem')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'purchase-order-items', PurchaseOrderItemViewSet, basename='purchaseorderitem')
router.register(r'goods-receipts', GoodsReceiptViewSet, basename='goodsreceipt')
router.register(r'goods-receipt-items', GoodsReceiptItemViewSet, basename='goodsreceiptitem')
router.register(r'purchase-invoices', PurchaseInvoiceViewSet, basename='purchaseinvoice')
router.register(r'purchase-invoice-items', PurchaseInvoiceItemViewSet, basename='purchaseinvoiceitem')
router.register(r'purchase-returns', PurchaseReturnViewSet, basename='purchasereturn')
router.register(r'purchase-return-items', PurchaseReturnItemViewSet, basename='purchasereturnitem')
router.register(r'outgoing-payments', OutgoingPaymentViewSet, basename='outgoingpayment')
router.register(r'outgoing-payment-invoices', OutgoingPaymentInvoiceViewSet, basename='outgoingpaymentinvoice')

# ==================== MANUFACTURING ====================
router.register(r'bill-of-materials', BillOfMaterialsViewSet, basename='billofmaterials')
router.register(r'bom-components', BOMComponentViewSet, basename='bomcomponent')
router.register(r'production-orders', ProductionOrderViewSet, basename='productionorder')
router.register(r'production-order-components', ProductionOrderComponentViewSet, basename='productionordercomponent')
router.register(r'production-receipts', ProductionReceiptViewSet, basename='productionreceipt')
router.register(r'production-receipt-items', ProductionReceiptItemViewSet, basename='productionreceiptitem')

# ==================== INVENTORY CONTROL ====================
router.register(r'stock-adjustments', StockAdjustmentViewSet, basename='stockadjustment')
router.register(r'stock-adjustment-items', StockAdjustmentItemViewSet, basename='stockadjustmentitem')
router.register(r'goods-issues', GoodsIssueViewSet, basename='goodsissue')
router.register(r'goods-issue-items', GoodsIssueItemViewSet, basename='goodsissueitem')
router.register(r'inventory-transfers', InventoryTransferViewSet, basename='inventorytransfer')
router.register(r'inventory-transfer-items', InventoryTransferItemViewSet, basename='inventorytransferitem')
router.register(r'warehouse-stock', ProductWarehouseStockViewSet, basename='warehousestock')
router.register(r'stock-transactions', StockTransactionViewSet, basename='stocktransaction')

# ==================== ACCOUNTING ====================
router.register(r'journal-entries', JournalEntryViewSet, basename='journalentry')
router.register(r'journal-entry-lines', JournalEntryLineViewSet, basename='journalentryline')
router.register(r'budgets', BudgetViewSet, basename='budget')

# ==================== DISCOUNT MANAGEMENT ====================
router.register(r'discount-types', DiscountTypeViewSet, basename='discounttype')
router.register(r'discount-rules', DiscountRuleViewSet, basename='discountrule')

# ==================== APPROVAL WORKFLOW ====================
router.register(r'approval-workflows', ApprovalWorkflowViewSet, basename='approvalworkflow')
router.register(r'approval-levels', ApprovalLevelViewSet, basename='approvallevel')
router.register(r'approval-requests', ApprovalRequestViewSet, basename='approvalrequest')

# ==================== NOTIFICATIONS ====================
router.register(r'notification-types', NotificationTypeViewSet, basename='notificationtype')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'alert-rules', AlertRuleViewSet, basename='alertrule')
router.register(r'notification-settings', NotificationSettingViewSet, basename='notificationsetting')

# ==================== POS (QUICK SALE) ====================
router.register(r'quick-sales', QuickSaleViewSet, basename='quicksale')
router.register(r'quick-sale-items', QuickSaleItemViewSet, basename='quicksaleitem')
router.register(r'user-profiles', UserProfileViewSet, basename='userprofile')

urlpatterns = [
    path('', include(router.urls)),
]
