"""
POS Utility Functions
Stock management for QuickSale without signals
"""
from decimal import Decimal
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


def update_pos_stock(quick_sale):
    """
    Update stock when QuickSale is completed
    Called from QuickSale.save() method
    
    Args:
        quick_sale: QuickSale instance
    
    Returns:
        tuple: (success: bool, message: str)
    """
    from erp.models import StockTransaction, ProductWarehouseStock
    
    try:
        # Get warehouse from branch
        warehouse = quick_sale.branch
        if not warehouse:
            from erp.models import Warehouse
            warehouse = Warehouse.objects.filter(is_active=True).first()
        
        if not warehouse:
            return False, "No warehouse found"
        
        reference = f"POS:{quick_sale.sale_number}"
        
        # Check if already processed
        if StockTransaction.objects.filter(reference=reference).exists():
            return True, "Already processed"
        
        # Process each item
        items_processed = 0
        for item in quick_sale.items.all():
            if item.quantity <= 0:
                continue
            
            # Create stock transaction
            transaction_obj = StockTransaction.objects.create(
                product=item.product,
                warehouse=warehouse,
                transaction_type='out',
                quantity=item.quantity,
                reference=reference,
                notes=f"POS Sale to {quick_sale.customer_name or 'Walk-in Customer'}"
            )
            
            # Update warehouse stock
            stock, _ = ProductWarehouseStock.objects.get_or_create(
                product=item.product,
                warehouse=warehouse,
                defaults={'quantity': Decimal('0.00')}
            )
            
            # Decrease stock
            stock.quantity -= item.quantity
            
            # Prevent negative stock
            if stock.quantity < 0:
                stock.quantity = Decimal('0.00')
            
            stock.save()
            
            # Update balance in transaction
            StockTransaction.objects.filter(pk=transaction_obj.pk).update(
                balance_after=stock.quantity
            )
            
            items_processed += 1
        
        logger.info(f"POS stock updated: {reference}, {items_processed} items processed")
        return True, f"Stock updated for {items_processed} items"
        
    except Exception as e:
        logger.error(f"Error updating POS stock: {str(e)}")
        return False, str(e)


def reverse_pos_stock(quick_sale):
    """
    Reverse stock when QuickSale is cancelled/refunded
    Called from QuickSale.save() method
    
    Args:
        quick_sale: QuickSale instance
    
    Returns:
        tuple: (success: bool, message: str)
    """
    from erp.models import StockTransaction, ProductWarehouseStock
    
    try:
        reference = f"POS:{quick_sale.sale_number}"
        
        # Get all transactions for this sale
        transactions = StockTransaction.objects.filter(reference=reference)
        
        if not transactions.exists():
            return True, "No transactions to reverse"
        
        # Reverse each transaction
        items_reversed = 0
        for trans in transactions:
            # Get stock
            stock = ProductWarehouseStock.objects.filter(
                product=trans.product,
                warehouse=trans.warehouse
            ).first()
            
            if stock:
                # Reverse: add back the quantity
                stock.quantity += trans.quantity
                stock.save()
                items_reversed += 1
        
        # Delete transactions
        transactions.delete()
        
        logger.info(f"POS stock reversed: {reference}, {items_reversed} items reversed")
        return True, f"Stock reversed for {items_reversed} items"
        
    except Exception as e:
        logger.error(f"Error reversing POS stock: {str(e)}")
        return False, str(e)


def process_pos_refund(quick_sale):
    """
    Process stock IN when QuickSale is refunded
    Called from QuickSale.save() method
    
    Args:
        quick_sale: QuickSale instance
    
    Returns:
        tuple: (success: bool, message: str)
    """
    from erp.models import StockTransaction, ProductWarehouseStock
    
    try:
        # First reverse the original OUT transactions
        reverse_pos_stock(quick_sale)
        
        # Get warehouse
        warehouse = quick_sale.branch
        if not warehouse:
            from erp.models import Warehouse
            warehouse = Warehouse.objects.filter(is_active=True).first()
        
        if not warehouse:
            return False, "No warehouse found"
        
        reference = f"POS:{quick_sale.sale_number}:REFUND"
        
        # Check if already processed
        if StockTransaction.objects.filter(reference=reference).exists():
            return True, "Refund already processed"
        
        # Process each item as stock IN
        items_processed = 0
        for item in quick_sale.items.all():
            if item.quantity <= 0:
                continue
            
            # Create stock transaction (IN)
            transaction_obj = StockTransaction.objects.create(
                product=item.product,
                warehouse=warehouse,
                transaction_type='in',
                quantity=item.quantity,
                reference=reference,
                notes=f"POS Sale Refund from {quick_sale.customer_name or 'Walk-in Customer'}"
            )
            
            # Update warehouse stock
            stock, _ = ProductWarehouseStock.objects.get_or_create(
                product=item.product,
                warehouse=warehouse,
                defaults={'quantity': Decimal('0.00')}
            )
            
            # Increase stock
            stock.quantity += item.quantity
            stock.save()
            
            # Update balance in transaction
            StockTransaction.objects.filter(pk=transaction_obj.pk).update(
                balance_after=stock.quantity
            )
            
            items_processed += 1
        
        logger.info(f"POS refund processed: {reference}, {items_processed} items processed")
        return True, f"Refund processed for {items_processed} items"
        
    except Exception as e:
        logger.error(f"Error processing POS refund: {str(e)}")
        return False, str(e)
