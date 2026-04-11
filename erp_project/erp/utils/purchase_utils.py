"""
Purchase Module Utility Functions
"""
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
import logging

from erp.models import (
    PurchaseQuotation, PurchaseOrder, PurchaseOrderItem,
    GoodsReceiptPO, GoodsReceiptPOItem,
    PurchaseInvoice, PurchaseInvoiceItem,
    PurchaseReturn, PurchaseReturnItem
)

logger = logging.getLogger(__name__)


@transaction.atomic
def copy_purchase_quotation_to_order(purchase_quotation_id):
    """
    Create a purchase order from a purchase quotation
    Copies all items from the quotation
    Only ONE purchase order can be created from a quotation
    """
    try:
        purchase_quotation = PurchaseQuotation.objects.prefetch_related('items__product').get(id=purchase_quotation_id)
        
        # Check if order already exists for this quotation
        existing_order = PurchaseOrder.objects.filter(purchase_quotation=purchase_quotation).first()
        if existing_order:
            return None, f"Purchase Order '{existing_order.order_number}' already exists for this quotation"
        
        # Check if quotation has items
        items = purchase_quotation.items.all()
        if not items.exists():
            return None, "Purchase Quotation has no items to copy"
        
        # Create purchase order
        purchase_order = PurchaseOrder.objects.create(
            purchase_quotation=purchase_quotation,
            supplier=purchase_quotation.supplier,
            status='draft',
            discount_amount=purchase_quotation.discount_amount,
            tax_amount=purchase_quotation.tax_amount,
        )
        
        # Copy items
        items_created = 0
        for pq_item in items:
            try:
                PurchaseOrderItem.objects.create(
                    purchase_order=purchase_order,
                    product=pq_item.product,
                    quantity=pq_item.quantity,
                    unit_price=pq_item.unit_price,
                )
                items_created += 1
            except Exception as item_error:
                logger.error(f"Error copying item {pq_item.id}: {str(item_error)}")
                raise
        
        logger.info(f"Copied {items_created} items from quotation {purchase_quotation.quotation_number} to order {purchase_order.order_number}")
        
        # Update quotation status to converted
        purchase_quotation.status = 'converted'
        purchase_quotation.save(update_fields=['status'])
        
        # Calculate totals
        purchase_order.calculate_totals()
        
        return purchase_order, None
    except PurchaseQuotation.DoesNotExist:
        return None, "Purchase Quotation not found"
    except Exception as e:
        logger.error(f"Error in copy_purchase_quotation_to_order: {str(e)}")
        return None, str(e)


@transaction.atomic
def copy_purchase_order_to_receipt(purchase_order_id):
    """
    Create a goods receipt from a purchase order
    Copies all items with remaining quantities
    Only ONE goods receipt can be created from a purchase order
    """
    try:
        purchase_order = PurchaseOrder.objects.prefetch_related('items__product').get(id=purchase_order_id)
        
        # Check if goods receipt already exists for this purchase order
        existing_receipt = GoodsReceiptPO.objects.filter(purchase_order=purchase_order).first()
        if existing_receipt:
            return None, f"Goods Receipt '{existing_receipt.receipt_number}' already exists for this purchase order"
        
        # Check if order has items
        items = purchase_order.items.all()
        if not items.exists():
            return None, "Purchase Order has no items to copy"
        
        # Create goods receipt PO
        goods_receipt = GoodsReceiptPO.objects.create(
            purchase_order=purchase_order,
            supplier=purchase_order.supplier,
            warehouse=purchase_order.warehouse if hasattr(purchase_order, 'warehouse') and purchase_order.warehouse else None,
            status='pending',
        )
        
        # Copy items with remaining quantities
        items_created = 0
        for po_item in items:
            try:
                GoodsReceiptPOItem.objects.create(
                    goods_receipt_po=goods_receipt,
                    product=po_item.product,
                    ordered_quantity=po_item.quantity,
                    received_quantity=po_item.quantity,  # Default to full quantity
                    unit_price=po_item.unit_price,
                )
                items_created += 1
            except Exception as item_error:
                logger.error(f"Error copying receipt item {po_item.id}: {str(item_error)}")
                raise
        
        logger.info(f"Copied {items_created} items from order {purchase_order.order_number} to receipt {goods_receipt.receipt_number}")
        
        # Update purchase order status to received (optional)
        # purchase_order.status = 'received'
        # purchase_order.save(update_fields=['status'])
        
        return goods_receipt, None
    except PurchaseOrder.DoesNotExist:
        return None, "Purchase Order not found"
    except Exception as e:
        logger.error(f"Error in copy_purchase_order_to_receipt: {str(e)}")
        return None, str(e)


@transaction.atomic
def copy_purchase_order_to_invoice(purchase_order_id):
    """
    Create a purchase invoice from a purchase order
    Copies all items with remaining quantities
    """
    try:
        purchase_order = PurchaseOrder.objects.prefetch_related('items__product').get(id=purchase_order_id)
        
        # Check if order has items
        items = purchase_order.items.all()
        if not items.exists():
            return None, "Purchase Order has no items to copy"
        
        # Create purchase invoice
        purchase_invoice = PurchaseInvoice.objects.create(
            purchase_order=purchase_order,
            supplier=purchase_order.supplier,
            invoice_date=purchase_order.order_date,
            due_date=purchase_order.order_date + timedelta(days=30),
            status='draft',
            discount_amount=purchase_order.discount_amount,
            tax_amount=purchase_order.tax_amount,
        )
        
        # Copy items
        items_created = 0
        for po_item in items:
            try:
                PurchaseInvoiceItem.objects.create(
                    purchase_invoice=purchase_invoice,
                    product=po_item.product,
                    quantity=po_item.quantity,
                    unit_price=po_item.unit_price,
                )
                items_created += 1
            except Exception as item_error:
                logger.error(f"Error copying invoice item {po_item.id}: {str(item_error)}")
                raise
        
        logger.info(f"Copied {items_created} items from order {purchase_order.order_number} to invoice {purchase_invoice.invoice_number}")
        
        # Calculate totals
        purchase_invoice.calculate_totals()
        
        return purchase_invoice, None
    except PurchaseOrder.DoesNotExist:
        return None, "Purchase Order not found"
    except Exception as e:
        logger.error(f"Error in copy_purchase_order_to_invoice: {str(e)}")
        return None, str(e)


@transaction.atomic
def copy_purchase_order_to_return(purchase_order_id):
    """
    Create a purchase return from a purchase order
    Copies all items that have been received
    """
    try:
        purchase_order = PurchaseOrder.objects.prefetch_related('items__product').get(id=purchase_order_id)
        
        # Check if order has items
        items = purchase_order.items.all()
        if not items.exists():
            return None, "Purchase Order has no items to copy"
        
        # Create purchase return
        purchase_return = PurchaseReturn.objects.create(
            purchase_order=purchase_order,
            supplier=purchase_order.supplier,
            status='pending',
        )
        
        # Copy items that have been received
        items_created = 0
        for po_item in items:
            received = po_item.received_quantity
            returned = po_item.returned_quantity
            available_to_return = received - returned
            
            if available_to_return > 0:
                try:
                    PurchaseReturnItem.objects.create(
                        purchase_return=purchase_return,
                        product=po_item.product,
                        quantity=available_to_return,
                        unit_price=po_item.unit_price,
                    )
                    items_created += 1
                except Exception as item_error:
                    logger.error(f"Error copying return item {po_item.id}: {str(item_error)}")
                    raise
        
        if items_created == 0:
            return None, "No received items available to return"
        
        logger.info(f"Copied {items_created} items from order {purchase_order.order_number} to return {purchase_return.return_number}")
        
        # Calculate totals
        purchase_return.calculate_totals()
        
        return purchase_return, None
    except PurchaseOrder.DoesNotExist:
        return None, "Purchase Order not found"
    except Exception as e:
        logger.error(f"Error in copy_purchase_order_to_return: {str(e)}")
        return None, str(e)
