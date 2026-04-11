"""
Print Views - For printing documents
"""
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

from ..models import (
    SalesOrder, SalesQuotation, QuickSale, Company,
    Delivery, Invoice, SalesReturn, IncomingPayment,
    # Purchase models
    PurchaseQuotation, PurchaseOrder, GoodsReceipt, GoodsReceiptPO,
    PurchaseInvoice, PurchaseReturn, OutgoingPayment
)


class PrintSalesOrderView(View):
    """Print Sales Order View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, order_id, *args, **kwargs):
        order = SalesOrder.objects.prefetch_related('items__product').select_related('customer').get(id=order_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'order': order,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_sales_order.html', context)


class PrintSalesQuotationView(View):
    """Print Sales Quotation View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, quotation_id, *args, **kwargs):
        quotation = SalesQuotation.objects.prefetch_related('items__product').select_related('customer', 'salesperson').get(id=quotation_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'quotation': quotation,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_sales_quotation.html', context)


class PrintDeliveryView(View):
    """Print Delivery Note View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, delivery_id, *args, **kwargs):
        delivery = Delivery.objects.prefetch_related('items__product').select_related(
            'customer', 'salesperson', 'sales_order', 'warehouse'
        ).get(id=delivery_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'delivery': delivery,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_delivery.html', context)


class PrintInvoiceView(View):
    """Print Invoice View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, invoice_id, *args, **kwargs):
        invoice = Invoice.objects.prefetch_related('items__product').select_related(
            'customer', 'salesperson', 'sales_order'
        ).get(id=invoice_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'invoice': invoice,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_invoice.html', context)


class PrintSalesReturnView(View):
    """Print Sales Return View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, return_id, *args, **kwargs):
        sales_return = SalesReturn.objects.prefetch_related('items__product').select_related(
            'customer', 'salesperson', 'sales_order', 'warehouse'
        ).get(id=return_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'sales_return': sales_return,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_sales_return.html', context)


class PrintQuickSaleView(View):
    """Print Quick Sale Receipt View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, sale_id, *args, **kwargs):
        sale = QuickSale.objects.prefetch_related('items__product').select_related('customer', 'branch', 'user').get(id=sale_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'sale': sale,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_quick_sale.html', context)


class PrintIncomingPaymentView(View):
    """Print Incoming Payment Receipt View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, payment_id, *args, **kwargs):
        payment = IncomingPayment.objects.prefetch_related('invoices__invoice').select_related(
            'customer', 'bank_account'
        ).get(id=payment_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'payment': payment,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_incoming_payment.html', context)


# ==================== PURCHASE MODULE PRINT VIEWS ====================

class PrintPurchaseQuotationView(View):
    """Print Purchase Quotation View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, quotation_id, *args, **kwargs):
        quotation = PurchaseQuotation.objects.prefetch_related('items__product').select_related('supplier').get(id=quotation_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'quotation': quotation,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_purchase_quotation.html', context)


class PrintPurchaseOrderView(View):
    """Print Purchase Order View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, order_id, *args, **kwargs):
        order = PurchaseOrder.objects.prefetch_related('items__product').select_related('supplier').get(id=order_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'order': order,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_purchase_order.html', context)


class PrintGoodsReceiptView(View):
    """Print Goods Receipt (General) View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, receipt_id, *args, **kwargs):
        receipt = GoodsReceipt.objects.prefetch_related('items__product').select_related('warehouse').get(id=receipt_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'receipt': receipt,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_goods_receipt.html', context)


class PrintGoodsReceiptPOView(View):
    """Print Goods Receipt PO View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, receipt_id, *args, **kwargs):
        receipt = GoodsReceiptPO.objects.prefetch_related('items__product').select_related(
            'supplier', 'warehouse', 'purchase_order'
        ).get(id=receipt_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'receipt': receipt,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_goods_receipt_po.html', context)


class PrintPurchaseInvoiceView(View):
    """Print Purchase Invoice View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, invoice_id, *args, **kwargs):
        invoice = PurchaseInvoice.objects.prefetch_related('items__product').select_related(
            'supplier', 'purchase_order'
        ).get(id=invoice_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'invoice': invoice,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_purchase_invoice.html', context)


class PrintPurchaseReturnView(View):
    """Print Purchase Return View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, return_id, *args, **kwargs):
        purchase_return = PurchaseReturn.objects.prefetch_related('items__product').select_related(
            'supplier', 'purchase_order', 'warehouse'
        ).get(id=return_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'purchase_return': purchase_return,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_purchase_return.html', context)


class PrintOutgoingPaymentView(View):
    """Print Outgoing Payment Receipt View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, payment_id, *args, **kwargs):
        payment = OutgoingPayment.objects.prefetch_related('invoices__purchase_invoice').select_related(
            'supplier', 'bank_account'
        ).get(id=payment_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'payment': payment,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_outgoing_payment.html', context)


# ==================== MANUFACTURING MODULE PRINT VIEWS ====================

from ..models import BillOfMaterials, ProductionOrder, ProductionReceipt, ProductionIssue


class PrintBOMView(View):
    """Print Bill of Materials View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, bom_id, *args, **kwargs):
        bom = BillOfMaterials.objects.prefetch_related('components__product').select_related('product').get(id=bom_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'bom': bom,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_bom.html', context)


class PrintProductionOrderView(View):
    """Print Production Order View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, order_id, *args, **kwargs):
        order = ProductionOrder.objects.prefetch_related('components__product').select_related(
            'product', 'bom', 'warehouse', 'sales_order'
        ).get(id=order_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'order': order,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_production_order.html', context)


class PrintProductionReceiptView(View):
    """Print Production Receipt View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, receipt_id, *args, **kwargs):
        receipt = ProductionReceipt.objects.prefetch_related('items__product').select_related(
            'production_order', 'warehouse'
        ).get(id=receipt_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'receipt': receipt,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_production_receipt.html', context)


class PrintProductionIssueView(View):
    """Print Production Issue View"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, issue_id, *args, **kwargs):
        issue = ProductionIssue.objects.prefetch_related('items__product').select_related(
            'production_order', 'warehouse'
        ).get(id=issue_id)
        
        try:
            company = Company.objects.first()
        except:
            company = None
        
        context = {
            'issue': issue,
            'company': company,
        }
        
        return render(request, 'admin/erp/prints/print_production_issue.html', context)
