"""
ERP Reports Module - Sales Reports (Optimized)
"""

# Sales Quotation Reports
from .sales_quotation_reports import (
    SalesQuotationDetailReportView,
    SalesQuotationSummaryReportView,
    StartDetailReportTaskView,
    StartSummaryReportTaskView,
    CheckTaskStatusView,
)

# Sales Order Reports
from .sales_order_reports import (
    SalesOrderDetailReportView,
    SalesOrderSummaryReportView,
    StartSalesOrderDetailReportTaskView,
    StartSalesOrderSummaryReportTaskView,
)

# Point of Sales Reports
from .pos_reports import (
    QuickSaleDetailReportView,
    QuickSaleSummaryReportView,
    StartQuickSaleDetailReportTaskView,
    StartQuickSaleSummaryReportTaskView,
)

# Purchase Order Reports
from .purchase_order_reports import (
    PurchaseOrderDetailReportView,
    PurchaseOrderSummaryReportView,
    StartPurchaseOrderDetailReportTaskView,
    StartPurchaseOrderSummaryReportTaskView,
)

__all__ = [
    # Sales Quotation Reports
    'SalesQuotationDetailReportView',
    'SalesQuotationSummaryReportView',
    'StartDetailReportTaskView',
    'StartSummaryReportTaskView',
    'CheckTaskStatusView',
    # Sales Order Reports
    'SalesOrderDetailReportView',
    'SalesOrderSummaryReportView',
    'StartSalesOrderDetailReportTaskView',
    'StartSalesOrderSummaryReportTaskView',
    # Point of Sales Reports
    'QuickSaleDetailReportView',
    'QuickSaleSummaryReportView',
    'StartQuickSaleDetailReportTaskView',
    'StartQuickSaleSummaryReportTaskView',
    # Purchase Order Reports
    'PurchaseOrderDetailReportView',
    'PurchaseOrderSummaryReportView',
    'StartPurchaseOrderDetailReportTaskView',
    'StartPurchaseOrderSummaryReportTaskView',
]

# Purchase Invoice Reports
from .purchase_invoice_reports import (
    PurchaseInvoiceDetailReportView,
    PurchaseInvoiceSummaryReportView,
    StartPurchaseInvoiceDetailReportTaskView,
    StartPurchaseInvoiceSummaryReportTaskView,
)

__all__.extend([
    'PurchaseInvoiceDetailReportView',
    'PurchaseInvoiceSummaryReportView',
    'StartPurchaseInvoiceDetailReportTaskView',
    'StartPurchaseInvoiceSummaryReportTaskView',
])

# Sales Invoice Reports
from .sales_invoice_reports import (
    SalesInvoiceDetailReportView,
    SalesInvoiceSummaryReportView,
    StartSalesInvoiceDetailReportTaskView,
    StartSalesInvoiceSummaryReportTaskView,
)

__all__.extend([
    'SalesInvoiceDetailReportView',
    'SalesInvoiceSummaryReportView',
    'StartSalesInvoiceDetailReportTaskView',
    'StartSalesInvoiceSummaryReportTaskView',
])
