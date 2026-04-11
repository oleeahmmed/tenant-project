"""
POS Signals - QuickSale Stock Transaction Management
DISABLED: Stock management moved to QuickSale.save() method using utility functions

এই signals গুলো এখন আর ব্যবহার হচ্ছে না।
Stock management এখন QuickSale model এর save() method এ করা হচ্ছে।
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from decimal import Decimal


# ==================== SIGNALS DISABLED ====================
# Stock management moved to QuickSale.save() method
# See: erp/models.py - QuickSale.save()
# Uses: erp/utils/pos_utils.py functions

# Keeping this file for reference only
# All signal receivers are commented out below

"""
# ==================== HELPER FUNCTIONS ====================

def create_pos_stock_transaction(product, warehouse, transaction_type, quantity, reference, notes=''):
    # POS stock transaction তৈরি করে এবং warehouse stock update করে
    from erp.models import StockTransaction, ProductWarehouseStock
    
    if not product or not warehouse:
        return None
    
    if quantity <= 0:
        return None
    
    # Transaction তৈরি
    transaction = StockTransaction.objects.create(
        product=product,
        warehouse=warehouse,
        transaction_type=transaction_type,
        quantity=abs(quantity),
        reference=reference,
        notes=notes
    )
    
    # Warehouse stock update
    stock, _ = ProductWarehouseStock.objects.get_or_create(
        product=product,
        warehouse=warehouse,
        defaults={'quantity': Decimal('0.00')}
    )
    
    if transaction_type == 'out':
        stock.quantity -= abs(quantity)
    elif transaction_type == 'in':
        stock.quantity += abs(quantity)
    
    # Stock negative হতে পারবে না
    if stock.quantity < 0:
        stock.quantity = Decimal('0.00')
    
    stock.save()
    
    # Transaction এ balance update
    StockTransaction.objects.filter(pk=transaction.pk).update(balance_after=stock.quantity)
    
    return transaction


def is_pos_transaction_processed(reference):
    # Check if POS transaction already exists for this reference
    from erp.models import StockTransaction
    return StockTransaction.objects.filter(reference=reference).exists()


def delete_pos_transactions(reference):
    # Delete all POS transactions with this reference and reverse stock
    from erp.models import StockTransaction, ProductWarehouseStock
    
    transactions = StockTransaction.objects.filter(reference=reference)
    
    for trans in transactions:
        # Reverse the stock change
        stock = ProductWarehouseStock.objects.filter(
            product=trans.product,
            warehouse=trans.warehouse
        ).first()
        
        if stock:
            if trans.transaction_type == 'out':
                stock.quantity += trans.quantity  # Reverse: add back
            elif trans.transaction_type == 'in':
                stock.quantity -= trans.quantity  # Reverse: subtract
            
            if stock.quantity < 0:
                stock.quantity = Decimal('0.00')
            stock.save()
    
    transactions.delete()


# ==================== QUICK SALE (POS) SIGNALS ====================
# Status: completed → Stock OUT
# Status: refunded → Stock IN (return)
# Status: cancelled → Reverse

@receiver(pre_save, sender='erp.QuickSale')
def pos_quick_sale_pre_save(sender, instance, **kwargs):
    # Save old status before update
    instance._old_status = None
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='erp.QuickSale')
def pos_quick_sale_post_save(sender, instance, created, **kwargs):
    # POS QuickSale stock movement handler
    
    # Triggers:
    # - completed: Stock OUT (products sold)
    # - refunded: Stock IN (products returned)
    # - cancelled/draft: Reverse transactions
    
    from django.db import transaction as db_transaction
    
    old_status = getattr(instance, '_old_status', None)
    reference = f"POS:{instance.sale_number}"
    
    # ==================== SALE COMPLETED ====================
    def process_sale_completion():
        # Process stock OUT when sale is completed
        if not is_pos_transaction_processed(reference):
            # Use branch as warehouse (QuickSale uses 'branch' not 'warehouse')
            warehouse = instance.branch
            
            if not warehouse:
                # Fallback to first active warehouse
                from erp.models import Warehouse
                warehouse = Warehouse.objects.filter(is_active=True).first()
            
            if warehouse:
                for item in instance.items.all():
                    create_pos_stock_transaction(
                        product=item.product,
                        warehouse=warehouse,
                        transaction_type='out',
                        quantity=item.quantity,
                        reference=reference,
                        notes=f"POS Sale to {instance.customer_name or 'Walk-in Customer'}"
                    )
    
    # ==================== SALE REFUNDED ====================
    def process_sale_refund():
        # Process stock IN when sale is refunded (return)
        # First delete old OUT transactions
        delete_pos_transactions(reference)
        
        # Then create IN transactions for return
        warehouse = instance.branch
        
        if not warehouse:
            from erp.models import Warehouse
            warehouse = Warehouse.objects.filter(is_active=True).first()
        
        if warehouse:
            for item in instance.items.all():
                create_pos_stock_transaction(
                    product=item.product,
                    warehouse=warehouse,
                    transaction_type='in',
                    quantity=item.quantity,
                    reference=f"{reference}:REFUND",
                    notes=f"POS Sale Refund from {instance.customer_name or 'Walk-in Customer'}"
                )
    
    # ==================== STATUS CHANGE LOGIC ====================
    
    # NEW SALE: Created directly with status='completed'
    if created and instance.status == 'completed':
        db_transaction.on_commit(process_sale_completion)
    
    # EXISTING SALE: Status changed to completed (draft/cancelled → completed)
    elif not created and instance.status == 'completed' and old_status != 'completed':
        db_transaction.on_commit(process_sale_completion)
    
    # Sale refunded (completed → refunded)
    elif instance.status == 'refunded' and old_status == 'completed':
        db_transaction.on_commit(process_sale_refund)
    
    # Sale cancelled or reverted to draft (completed → draft/cancelled)
    elif old_status == 'completed' and instance.status in ['draft', 'cancelled']:
        delete_pos_transactions(reference)
    
    # Refund cancelled (refunded → any other status)
    elif old_status == 'refunded' and instance.status != 'refunded':
        delete_pos_transactions(f"{reference}:REFUND")
"""
