"""
ERP Views Package
"""
# Dashboard views
from .dashboards import (
    DashboardView,
    SalesDashboardView,
    PurchaseDashboardView,
    POSDashboardView,
    UserPOSDashboardView,
    InventoryDashboardView,
    ManufacturingDashboardView,
    FinancialDashboardView,
)
from .print_views import (
    PrintSalesOrderView, PrintSalesQuotationView, PrintQuickSaleView,
    PrintDeliveryView, PrintInvoiceView, PrintSalesReturnView, PrintIncomingPaymentView,
    # Purchase print views
    PrintPurchaseQuotationView, PrintPurchaseOrderView, PrintGoodsReceiptView,
    PrintGoodsReceiptPOView, PrintPurchaseInvoiceView, PrintPurchaseReturnView,
    PrintOutgoingPaymentView,
    # Manufacturing print views
    PrintBOMView, PrintProductionOrderView, PrintProductionReceiptView, PrintProductionIssueView
)
# Guide views
from .guides import (
    StockMovementGuideView,
    ExpenseManagementGuideView,
    IncomeManagementGuideView,
    InventoryManagementGuideView,
    ProductionManagementGuideView,
    SalesManagementGuideView,
    BankingManagementGuideView,
)
from .api_views import (
    get_product_price,
    get_sales_order_details,
    get_purchase_order_details,
    get_sales_quotation_details,
    get_purchase_quotation_details,
    get_product_by_sku,
    get_customer_details,
    get_customer_by_phone,
)
from .copy_views import (
    copy_sales_quotation_to_order_view,
    copy_sales_order_to_delivery_view,
    copy_sales_order_to_invoice_view,
    copy_sales_order_to_return_view,
    copy_purchase_quotation_to_order_view,
    copy_purchase_order_to_receipt_view,
    copy_purchase_order_to_invoice_view,
    copy_purchase_order_to_return_view,
    copy_bom_to_production_order_view,
    copy_production_order_to_receipt_view,
)

__all__ = [
    'DashboardView',
    'PrintSalesOrderView',
    'PrintSalesQuotationView',
    'PrintDeliveryView',
    'PrintInvoiceView',
    'PrintSalesReturnView',
    'PrintIncomingPaymentView',
    'PrintQuickSaleView',
    # Purchase print views
    'PrintPurchaseQuotationView',
    'PrintPurchaseOrderView',
    'PrintGoodsReceiptView',
    'PrintGoodsReceiptPOView',
    'PrintPurchaseInvoiceView',
    'PrintPurchaseReturnView',
    'PrintOutgoingPaymentView',
    # Manufacturing print views
    'PrintBOMView',
    'PrintProductionOrderView',
    'PrintProductionReceiptView',
    'PrintProductionIssueView',
    'StockMovementGuideView',
    'ExpenseManagementGuideView',
    'get_product_price',
    'get_product_by_sku',
    'get_customer_details',
    'get_customer_by_phone',
    'get_sales_order_details',
    'get_purchase_order_details',
    'get_sales_quotation_details',
    'get_purchase_quotation_details',
    'copy_sales_quotation_to_order_view',
    'copy_sales_order_to_delivery_view',
    'copy_sales_order_to_invoice_view',
    'copy_sales_order_to_return_view',
    'copy_purchase_quotation_to_order_view',
    'copy_purchase_order_to_receipt_view',
    'copy_purchase_order_to_invoice_view',
    'copy_purchase_order_to_return_view',
    'copy_bom_to_production_order_view',
    'copy_production_order_to_receipt_view',
]
