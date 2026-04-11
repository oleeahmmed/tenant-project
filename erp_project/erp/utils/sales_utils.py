"""
Sales Module Utility Functions
"""
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
import logging

from erp.models import (
    SalesQuotation, SalesOrder, Delivery, Invoice, SalesReturn, 
    SalesOrderItem, DeliveryItem, InvoiceItem, SalesReturnItem
)

logger = logging.getLogger(__name__)


@transaction.atomic
def copy_sales_quotation_to_order(sales_quotation_id):
    """
    Create a sales order from a sales quotation
    Copies all items from the quotation
    Only ONE sales order can be created from a quotation
    """
    try:
        sales_quotation = SalesQuotation.objects.prefetch_related('items__product').get(id=sales_quotation_id)
        
        # Check if order already exists for this quotation
        existing_order = SalesOrder.objects.filter(sales_quotation=sales_quotation).first()
        if existing_order:
            return None, f"Sales Order '{existing_order.order_number}' already exists for this quotation"
        
        # Check if quotation has items
        items = sales_quotation.items.all()
        if not items.exists():
            return None, "Sales Quotation has no items to copy"
        
        # Create sales order
        sales_order = SalesOrder.objects.create(
            sales_quotation=sales_quotation,
            customer=sales_quotation.customer,
            salesperson=sales_quotation.salesperson,
            status='draft',
            job_reference=sales_quotation.job_reference,
            shipping_method=sales_quotation.shipping_method,
            delivery_terms=sales_quotation.delivery_terms,
            payment_terms=sales_quotation.payment_terms,
            discount_amount=sales_quotation.discount_amount,
            tax_amount=sales_quotation.tax_amount,
            tax_rate=sales_quotation.tax_rate,
        )
        
        # Copy items
        items_created = 0
        for sq_item in items:
            try:
                SalesOrderItem.objects.create(
                    sales_order=sales_order,
                    product=sq_item.product,
                    quantity=sq_item.quantity,
                    unit_price=sq_item.unit_price,
                )
                items_created += 1
            except Exception as item_error:
                logger.error(f"Error copying item {sq_item.id}: {str(item_error)}")
                raise
        
        logger.info(f"Copied {items_created} items from quotation {sales_quotation.quotation_number} to order {sales_order.order_number}")
        
        # Update quotation status to converted
        sales_quotation.status = 'converted'
        sales_quotation.save(update_fields=['status'])
        
        # Calculate totals
        sales_order.calculate_totals()
        
        return sales_order, None
    except SalesQuotation.DoesNotExist:
        return None, "Sales Quotation not found"
    except Exception as e:
        logger.error(f"Error in copy_sales_quotation_to_order: {str(e)}")
        return None, str(e)


@transaction.atomic
def copy_sales_order_to_delivery(sales_order_id):
    """
    Create a delivery from a sales order
    Copies all items with remaining quantities
    """
    try:
        sales_order = SalesOrder.objects.prefetch_related('items__product').get(id=sales_order_id)
        
        # Check if order has items
        items = sales_order.items.all()
        if not items.exists():
            return None, "Sales Order has no items to copy"
        
        # Create delivery
        delivery = Delivery.objects.create(
            sales_order=sales_order,
            customer=sales_order.customer,
            salesperson=sales_order.salesperson,
            status='pending',
            delivery_address=sales_order.customer.address if sales_order.customer.address else '',
        )
        
        # Copy items with remaining quantities
        items_created = 0
        for so_item in items:
            remaining = so_item.remaining_to_deliver
            if remaining > 0:
                try:
                    DeliveryItem.objects.create(
                        delivery=delivery,
                        product=so_item.product,
                        quantity=remaining,
                        unit_price=so_item.unit_price,
                    )
                    items_created += 1
                except Exception as item_error:
                    logger.error(f"Error copying delivery item {so_item.id}: {str(item_error)}")
                    raise
        
        if items_created == 0:
            return None, "No items with remaining quantities to deliver"
        
        logger.info(f"Copied {items_created} items from order {sales_order.order_number} to delivery {delivery.delivery_number}")
        
        return delivery, None
    except SalesOrder.DoesNotExist:
        return None, "Sales Order not found"
    except Exception as e:
        logger.error(f"Error in copy_sales_order_to_delivery: {str(e)}")
        return None, str(e)


@transaction.atomic
def copy_sales_order_to_invoice(sales_order_id):
    """
    Create an invoice from a sales order
    Copies all items with remaining quantities
    """
    try:
        sales_order = SalesOrder.objects.prefetch_related('items__product').get(id=sales_order_id)
        
        # Check if order has items
        items = sales_order.items.all()
        if not items.exists():
            return None, "Sales Order has no items to copy"
        
        # Create invoice
        invoice = Invoice.objects.create(
            sales_order=sales_order,
            customer=sales_order.customer,
            salesperson=sales_order.salesperson,
            invoice_date=sales_order.order_date,
            due_date=sales_order.due_date if sales_order.due_date else sales_order.order_date,
            status='draft',
            discount_amount=sales_order.discount_amount,
            tax_amount=sales_order.tax_amount,
        )
        
        # Copy items with remaining quantities
        items_created = 0
        for so_item in items:
            remaining = so_item.remaining_to_invoice
            if remaining > 0:
                try:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product=so_item.product,
                        quantity=remaining,
                        unit_price=so_item.unit_price,
                    )
                    items_created += 1
                except Exception as item_error:
                    logger.error(f"Error copying invoice item {so_item.id}: {str(item_error)}")
                    raise
        
        if items_created == 0:
            return None, "No items with remaining quantities to invoice"
        
        logger.info(f"Copied {items_created} items from order {sales_order.order_number} to invoice {invoice.invoice_number}")
        
        # Calculate totals
        invoice.calculate_totals()
        
        return invoice, None
    except SalesOrder.DoesNotExist:
        return None, "Sales Order not found"
    except Exception as e:
        logger.error(f"Error in copy_sales_order_to_invoice: {str(e)}")
        return None, str(e)


@transaction.atomic
def copy_sales_order_to_return(sales_order_id):
    """
    Create a sales return from a sales order
    Copies all items that have been delivered (and not yet returned)
    """
    try:
        sales_order = SalesOrder.objects.prefetch_related('items__product').get(id=sales_order_id)
        
        # Check if order has items
        items = sales_order.items.all()
        if not items.exists():
            return None, "Sales Order has no items to copy"
        
        # Check if any items have been delivered
        has_delivered_items = False
        for so_item in items:
            if so_item.delivered_quantity > 0:
                has_delivered_items = True
                break
        
        if not has_delivered_items:
            return None, "No items have been delivered yet. Please create a Delivery first and mark it as 'Delivered' before creating a return."
        
        # Create sales return
        sales_return = SalesReturn.objects.create(
            sales_order=sales_order,
            customer=sales_order.customer,
            salesperson=sales_order.salesperson,
            status='pending',
        )
        
        # Copy items that have been delivered (and not yet fully returned)
        items_created = 0
        for so_item in items:
            delivered = so_item.delivered_quantity
            returned = so_item.returned_quantity
            available_to_return = delivered - returned
            
            if available_to_return > 0:
                try:
                    SalesReturnItem.objects.create(
                        sales_return=sales_return,
                        product=so_item.product,
                        quantity=available_to_return,
                        unit_price=so_item.unit_price,
                    )
                    items_created += 1
                except Exception as item_error:
                    logger.error(f"Error copying return item {so_item.id}: {str(item_error)}")
                    raise
        
        if items_created == 0:
            # Delete the empty return
            sales_return.delete()
            return None, "All delivered items have already been returned."
        
        logger.info(f"Copied {items_created} items from order {sales_order.order_number} to return {sales_return.return_number}")
        
        # Calculate totals
        sales_return.calculate_totals()
        
        return sales_return, None
    except SalesOrder.DoesNotExist:
        return None, "Sales Order not found"
    except Exception as e:
        logger.error(f"Error in copy_sales_order_to_return: {str(e)}")
        return None, str(e)
