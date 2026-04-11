"""
Copy/Create Views - For creating documents from other documents
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from ..utils import (
    copy_sales_quotation_to_order,
    copy_sales_order_to_delivery,
    copy_sales_order_to_invoice,
    copy_sales_order_to_return,
    copy_purchase_quotation_to_order,
    copy_purchase_order_to_receipt,
    copy_purchase_order_to_invoice,
    copy_purchase_order_to_return,
    copy_bom_to_production_order,
    copy_production_order_to_receipt,
)


@staff_member_required
def copy_sales_quotation_to_order_view(request, quotation_id):
    """Create Sales Order from Sales Quotation"""
    sales_order, error = copy_sales_quotation_to_order(quotation_id)
    
    if sales_order:
        messages.success(request, f'Sales Order {sales_order.order_number} created successfully from quotation!')
        return redirect('admin:erp_salesorder_change', sales_order.id)
    else:
        messages.error(request, f'Error creating sales order: {error}')
        return redirect('admin:erp_salesquotation_change', quotation_id)


@staff_member_required
def copy_sales_order_to_delivery_view(request, order_id):
    """Create Delivery from Sales Order"""
    delivery, error = copy_sales_order_to_delivery(order_id)
    
    if delivery:
        messages.success(request, f'Delivery {delivery.delivery_number} created successfully from sales order!')
        return redirect('admin:erp_delivery_change', delivery.id)
    else:
        messages.error(request, f'Error creating delivery: {error}')
        return redirect('admin:erp_salesorder_change', order_id)


@staff_member_required
def copy_sales_order_to_invoice_view(request, order_id):
    """Create Invoice from Sales Order"""
    invoice, error = copy_sales_order_to_invoice(order_id)
    
    if invoice:
        messages.success(request, f'Invoice {invoice.invoice_number} created successfully from sales order!')
        return redirect('admin:erp_invoice_change', invoice.id)
    else:
        messages.error(request, f'Error creating invoice: {error}')
        return redirect('admin:erp_salesorder_change', order_id)


@staff_member_required
def copy_sales_order_to_return_view(request, order_id):
    """Create Sales Return from Sales Order"""
    sales_return, error = copy_sales_order_to_return(order_id)
    
    if sales_return:
        messages.success(request, f'Sales Return {sales_return.return_number} created successfully from sales order!')
        return redirect('admin:erp_salesreturn_change', sales_return.id)
    else:
        messages.error(request, f'Error creating sales return: {error}')
        return redirect('admin:erp_salesorder_change', order_id)


@staff_member_required
def copy_purchase_quotation_to_order_view(request, quotation_id):
    """Create Purchase Order from Purchase Quotation"""
    purchase_order, error = copy_purchase_quotation_to_order(quotation_id)
    
    if purchase_order:
        messages.success(request, f'Purchase Order {purchase_order.order_number} created successfully from quotation!')
        return redirect('admin:erp_purchaseorder_change', purchase_order.id)
    else:
        messages.error(request, f'Error creating purchase order: {error}')
        return redirect('admin:erp_purchasequotation_change', quotation_id)


@staff_member_required
def copy_purchase_order_to_receipt_view(request, order_id):
    """Create Goods Receipt from Purchase Order"""
    goods_receipt, error = copy_purchase_order_to_receipt(order_id)
    
    if goods_receipt:
        messages.success(request, f'Goods Receipt {goods_receipt.receipt_number} created successfully from purchase order!')
        return redirect('admin:erp_goodsreceiptpo_change', goods_receipt.id)
    else:
        messages.error(request, f'Error creating goods receipt: {error}')
        return redirect('admin:erp_purchaseorder_change', order_id)


@staff_member_required
def copy_purchase_order_to_invoice_view(request, order_id):
    """Create Purchase Invoice from Purchase Order"""
    purchase_invoice, error = copy_purchase_order_to_invoice(order_id)
    
    if purchase_invoice:
        messages.success(request, f'Purchase Invoice {purchase_invoice.invoice_number} created successfully from purchase order!')
        return redirect('admin:erp_purchaseinvoice_change', purchase_invoice.id)
    else:
        messages.error(request, f'Error creating purchase invoice: {error}')
        return redirect('admin:erp_purchaseorder_change', order_id)


@staff_member_required
def copy_purchase_order_to_return_view(request, order_id):
    """Create Purchase Return from Purchase Order"""
    purchase_return, error = copy_purchase_order_to_return(order_id)
    
    if purchase_return:
        messages.success(request, f'Purchase Return {purchase_return.return_number} created successfully from purchase order!')
        return redirect('admin:erp_purchasereturn_change', purchase_return.id)
    else:
        messages.error(request, f'Error creating purchase return: {error}')
        return redirect('admin:erp_purchaseorder_change', order_id)


@staff_member_required
def copy_bom_to_production_order_view(request, bom_id):
    """Create Production Order from BOM"""
    production_order, error = copy_bom_to_production_order(bom_id)
    
    if production_order:
        messages.success(request, f'Production Order {production_order.order_number} created successfully from BOM!')
        return redirect('admin:erp_productionorder_change', production_order.id)
    else:
        messages.error(request, f'Error creating production order: {error}')
        return redirect('admin:erp_billofmaterials_change', bom_id)


@staff_member_required
def copy_production_order_to_receipt_view(request, order_id):
    """Create Production Receipt from Production Order"""
    production_receipt, error = copy_production_order_to_receipt(order_id)
    
    if production_receipt:
        messages.success(request, f'Production Receipt {production_receipt.receipt_number} created successfully from production order!')
        return redirect('admin:erp_productionreceipt_change', production_receipt.id)
    else:
        messages.error(request, f'Error creating production receipt: {error}')
        return redirect('admin:erp_productionorder_change', order_id)
