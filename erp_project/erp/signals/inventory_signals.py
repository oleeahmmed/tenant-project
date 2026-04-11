"""
ERP Inventory Signals - Stock Transaction Management

এই signals গুলো automatically stock transactions তৈরি করে যখন:
- Delivery → delivered হলে Stock OUT
- GoodsReceipt → received হলে Stock IN  
- SalesReturn → completed হলে Stock IN
- PurchaseReturn → completed হলে Stock OUT
- GoodsIssue → issued হলে Stock OUT
- InventoryTransfer → completed হলে Stock OUT + IN
- ProductionReceipt → completed হলে Finished IN + Components OUT
- QuickSale → completed হলে Stock OUT
- StockAdjustment → approved হলে Stock +/-
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from decimal import Decimal


# ==================== HELPER FUNCTIONS ====================

def create_stock_transaction(product, warehouse, transaction_type, quantity, reference, notes=''):
    """Stock transaction তৈরি করে এবং warehouse stock update করে"""
    from erp.models import StockTransaction, ProductWarehouseStock
    
    if not product or not warehouse:
        return None
    
    # Adjustment ছাড়া অন্য সব ক্ষেত্রে quantity > 0 হতে হবে
    if quantity <= 0 and transaction_type != 'adjustment':
        return None
    
    # Transaction তৈরি
    transaction = StockTransaction.objects.create(
        product=product,
        warehouse=warehouse,
        transaction_type=transaction_type,
        quantity=abs(quantity) if transaction_type != 'adjustment' else quantity,
        reference=reference,
        notes=notes
    )
    
    # Warehouse stock update
    stock, _ = ProductWarehouseStock.objects.get_or_create(
        product=product,
        warehouse=warehouse,
        defaults={'quantity': Decimal('0.00')}
    )
    
    if transaction_type in ['in', 'transfer_in']:
        stock.quantity += abs(quantity)
    elif transaction_type in ['out', 'transfer_out']:
        stock.quantity -= abs(quantity)
    elif transaction_type == 'adjustment':
        stock.quantity += quantity  # Can be positive or negative
    
    # Stock negative হতে পারবে না
    if stock.quantity < 0:
        stock.quantity = Decimal('0.00')
    
    stock.save()
    
    # Transaction এ balance update
    StockTransaction.objects.filter(pk=transaction.pk).update(balance_after=stock.quantity)
    
    return transaction


def is_already_processed(reference):
    """Check if transaction already exists for this reference"""
    from erp.models import StockTransaction
    return StockTransaction.objects.filter(reference=reference).exists()


def delete_transactions_by_reference(reference):
    """Delete all transactions with this reference and reverse stock"""
    from erp.models import StockTransaction, ProductWarehouseStock
    
    transactions = StockTransaction.objects.filter(reference=reference)
    
    for trans in transactions:
        # Reverse the stock change
        stock = ProductWarehouseStock.objects.filter(
            product=trans.product,
            warehouse=trans.warehouse
        ).first()
        
        if stock:
            if trans.transaction_type in ['in', 'transfer_in']:
                stock.quantity -= trans.quantity
            elif trans.transaction_type in ['out', 'transfer_out']:
                stock.quantity += trans.quantity
            elif trans.transaction_type == 'adjustment':
                stock.quantity -= trans.quantity
            
            if stock.quantity < 0:
                stock.quantity = Decimal('0.00')
            stock.save()
    
    transactions.delete()


# ==================== DELIVERY SIGNALS ====================
# Status: delivered → Stock OUT

@receiver(pre_save, sender='erp.Delivery')
def delivery_pre_save(sender, instance, **kwargs):
    instance._old_status = None
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='erp.Delivery')
def delivery_post_save(sender, instance, **kwargs):
    from django.db import transaction as db_transaction
    
    old_status = getattr(instance, '_old_status', None)
    reference = f"DL:{instance.delivery_number}"
    
    def process_delivery():
        if not is_already_processed(reference):
            for item in instance.items.all():
                create_stock_transaction(
                    product=item.product,
                    warehouse=instance.warehouse,
                    transaction_type='out',
                    quantity=item.quantity,
                    reference=reference,
                    notes=f"Delivery to {instance.customer.name}"
                )
            sender.objects.filter(pk=instance.pk).update(stock_updated=True)
    
    if instance.status == 'delivered' and old_status != 'delivered':
        db_transaction.on_commit(process_delivery)
    
    elif old_status == 'delivered' and instance.status != 'delivered':
        delete_transactions_by_reference(reference)
        sender.objects.filter(pk=instance.pk).update(stock_updated=False)


# ==================== GOODS RECEIPT SIGNALS (General) ====================
# Status: received → Stock IN

@receiver(pre_save, sender='erp.GoodsReceipt')
def goods_receipt_pre_save(sender, instance, **kwargs):
    instance._old_status = None
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='erp.GoodsReceipt')
def goods_receipt_post_save(sender, instance, **kwargs):
    from django.db import transaction as db_transaction
    
    old_status = getattr(instance, '_old_status', None)
    reference = f"GRN:{instance.receipt_number}"
    
    def process_receipt():
        if not is_already_processed(reference):
            for item in instance.items.all():
                create_stock_transaction(
                    product=item.product,
                    warehouse=instance.warehouse,
                    transaction_type='in',
                    quantity=item.quantity,
                    reference=reference,
                    notes=f"{instance.get_receipt_type_display()}"
                )
            sender.objects.filter(pk=instance.pk).update(stock_updated=True)
    
    if instance.status == 'received' and old_status != 'received':
        db_transaction.on_commit(process_receipt)
    
    elif old_status == 'received' and instance.status != 'received':
        delete_transactions_by_reference(reference)
        sender.objects.filter(pk=instance.pk).update(stock_updated=False)


# ==================== GOODS RECEIPT PO SIGNALS (From Purchase Order) ====================
# Status: received/completed → Stock IN (accepted_quantity)

@receiver(pre_save, sender='erp.GoodsReceiptPO')
def goods_receipt_po_pre_save(sender, instance, **kwargs):
    instance._old_status = None
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='erp.GoodsReceiptPO')
def goods_receipt_po_post_save(sender, instance, **kwargs):
    from django.db import transaction as db_transaction
    
    old_status = getattr(instance, '_old_status', None)
    reference = f"GRPO:{instance.receipt_number}"
    
    trigger_statuses = ['received', 'inspected', 'completed']
    
    def process_receipt():
        if not is_already_processed(reference):
            for item in instance.items.all():
                if item.accepted_quantity > 0:
                    create_stock_transaction(
                        product=item.product,
                        warehouse=instance.warehouse,
                        transaction_type='in',
                        quantity=item.accepted_quantity,
                        reference=reference,
                        notes=f"PO Receipt from {instance.supplier.name}"
                    )
            sender.objects.filter(pk=instance.pk).update(stock_updated=True)
    
    if instance.status in trigger_statuses and old_status not in trigger_statuses:
        db_transaction.on_commit(process_receipt)
    
    elif old_status in trigger_statuses and instance.status not in trigger_statuses:
        delete_transactions_by_reference(reference)
        sender.objects.filter(pk=instance.pk).update(stock_updated=False)


# ==================== SALES RETURN SIGNALS ====================
# Status: completed → Stock IN (customer থেকে goods ফেরত)

@receiver(pre_save, sender='erp.SalesReturn')
def sales_return_pre_save(sender, instance, **kwargs):
    instance._old_status = None
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='erp.SalesReturn')
def sales_return_post_save(sender, instance, **kwargs):
    from django.db import transaction as db_transaction
    
    old_status = getattr(instance, '_old_status', None)
    reference = f"SR:{instance.return_number}"
    
    def process_return():
        if not is_already_processed(reference):
            for item in instance.items.all():
                create_stock_transaction(
                    product=item.product,
                    warehouse=instance.warehouse,
                    transaction_type='in',
                    quantity=item.quantity,
                    reference=reference,
                    notes=f"Return from {instance.customer.name}"
                )
            sender.objects.filter(pk=instance.pk).update(stock_updated=True)
    
    if instance.status == 'completed' and old_status != 'completed':
        db_transaction.on_commit(process_return)
    
    elif old_status == 'completed' and instance.status != 'completed':
        delete_transactions_by_reference(reference)
        sender.objects.filter(pk=instance.pk).update(stock_updated=False)


# ==================== PURCHASE RETURN SIGNALS ====================
# Status: completed → Stock OUT (supplier কে goods ফেরত)

@receiver(pre_save, sender='erp.PurchaseReturn')
def purchase_return_pre_save(sender, instance, **kwargs):
    instance._old_status = None
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='erp.PurchaseReturn')
def purchase_return_post_save(sender, instance, **kwargs):
    from django.db import transaction as db_transaction
    
    old_status = getattr(instance, '_old_status', None)
    reference = f"PR:{instance.return_number}"
    
    def process_return():
        if not is_already_processed(reference):
            for item in instance.items.all():
                create_stock_transaction(
                    product=item.product,
                    warehouse=instance.warehouse,
                    transaction_type='out',
                    quantity=item.quantity,
                    reference=reference,
                    notes=f"Return to {instance.supplier.name}"
                )
            sender.objects.filter(pk=instance.pk).update(stock_updated=True)
    
    if instance.status == 'completed' and old_status != 'completed':
        db_transaction.on_commit(process_return)
    
    elif old_status == 'completed' and instance.status != 'completed':
        delete_transactions_by_reference(reference)
        sender.objects.filter(pk=instance.pk).update(stock_updated=False)


# ==================== GOODS ISSUE SIGNALS ====================
# Status: issued → Stock OUT

@receiver(pre_save, sender='erp.GoodsIssue')
def goods_issue_pre_save(sender, instance, **kwargs):
    instance._old_status = None
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='erp.GoodsIssue')
def goods_issue_post_save(sender, instance, **kwargs):
    from django.db import transaction as db_transaction
    
    old_status = getattr(instance, '_old_status', None)
    reference = f"GI:{instance.issue_number}"
    
    def process_issue():
        if not is_already_processed(reference):
            for item in instance.items.all():
                create_stock_transaction(
                    product=item.product,
                    warehouse=instance.warehouse,
                    transaction_type='out',
                    quantity=item.quantity,
                    reference=reference,
                    notes=f"{instance.get_issue_type_display()}"
                )
            sender.objects.filter(pk=instance.pk).update(stock_updated=True)
    
    if instance.status == 'issued' and old_status != 'issued':
        db_transaction.on_commit(process_issue)
    
    elif old_status == 'issued' and instance.status != 'issued':
        delete_transactions_by_reference(reference)
        sender.objects.filter(pk=instance.pk).update(stock_updated=False)



# ==================== INVENTORY TRANSFER SIGNALS ====================
# Status: completed → Stock OUT from source + Stock IN to destination

@receiver(pre_save, sender='erp.InventoryTransfer')
def inventory_transfer_pre_save(sender, instance, **kwargs):
    instance._old_status = None
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='erp.InventoryTransfer')
def inventory_transfer_post_save(sender, instance, created, **kwargs):
    from django.db import transaction as db_transaction
    
    old_status = getattr(instance, '_old_status', None)
    reference = f"IT:{instance.transfer_number}"
    
    def process_transfer():
        if not is_already_processed(reference):
            for item in instance.items.all():
                create_stock_transaction(
                    product=item.product,
                    warehouse=instance.from_warehouse,
                    transaction_type='transfer_out',
                    quantity=item.quantity,
                    reference=reference,
                    notes=f"Transfer to {instance.to_warehouse.name}"
                )
                create_stock_transaction(
                    product=item.product,
                    warehouse=instance.to_warehouse,
                    transaction_type='transfer_in',
                    quantity=item.quantity,
                    reference=reference,
                    notes=f"Transfer from {instance.from_warehouse.name}"
                )
    
    if instance.status == 'completed' and old_status != 'completed':
        db_transaction.on_commit(process_transfer)
    
    elif old_status == 'completed' and instance.status != 'completed':
        delete_transactions_by_reference(reference)


# ==================== PRODUCTION RECEIPT SIGNALS ====================
# Status: completed → Finished Products IN (NO components OUT - already issued)

@receiver(pre_save, sender='erp.ProductionReceipt')
def production_receipt_pre_save(sender, instance, **kwargs):
    instance._old_status = None
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='erp.ProductionReceipt')
def production_receipt_post_save(sender, instance, **kwargs):
    from django.db import transaction as db_transaction
    
    old_status = getattr(instance, '_old_status', None)
    reference = f"PRR:{instance.receipt_number}"
    
    def process_production():
        if not is_already_processed(reference):
            # Process finished goods items (NO components OUT)
            for item in instance.items.all():
                if item.received_quantity > 0:
                    create_stock_transaction(
                        product=item.product,
                        warehouse=instance.warehouse,
                        transaction_type='in',
                        quantity=item.received_quantity,
                        reference=reference,
                        notes=f"Production receipt: {item.product.name}"
                    )
                    
                    # Update production order quantity produced
                    po = instance.production_order
                    po.quantity_produced += item.received_quantity
                    po.save(update_fields=['quantity_produced'])
    
    if instance.status == 'completed' and old_status != 'completed':
        db_transaction.on_commit(process_production)
    
    elif old_status == 'completed' and instance.status != 'completed':
        # Reverse production quantities
        for item in instance.items.all():
            po = instance.production_order
            po.quantity_produced -= item.received_quantity
            if po.quantity_produced < 0:
                po.quantity_produced = Decimal('0.00')
            po.save(update_fields=['quantity_produced'])
        
        delete_transactions_by_reference(reference)


# ==================== STOCK ADJUSTMENT SIGNALS ====================
# Status: approved/posted → Stock +/- (actual - system)
# NOTE: Admin থেকে save করলে save_related এ handle হয়, 
# এই signal শুধু programmatic save এর জন্য

@receiver(pre_save, sender='erp.StockAdjustment')
def stock_adjustment_pre_save(sender, instance, **kwargs):
    instance._old_status = None
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='erp.StockAdjustment')
def stock_adjustment_post_save(sender, instance, **kwargs):
    from django.db import transaction as db_transaction
    
    old_status = getattr(instance, '_old_status', None)
    reference = f"ADJ:{instance.adjustment_number}"
    
    trigger_statuses = ['approved', 'posted']
    
    # Use on_commit to ensure items are saved first
    def process_adjustment():
        if not is_already_processed(reference):
            items = instance.items.all()
            
            for item in items:
                diff = item.actual_quantity - item.system_quantity
                
                if diff != 0:
                    create_stock_transaction(
                        product=item.product,
                        warehouse=instance.warehouse,
                        transaction_type='adjustment',
                        quantity=diff,
                        reference=reference,
                        notes=f"{instance.get_adjustment_type_display()}: {item.reason or 'N/A'}"
                    )
    
    if instance.status in trigger_statuses and old_status not in trigger_statuses:
        db_transaction.on_commit(process_adjustment)
    
    elif old_status in trigger_statuses and instance.status not in trigger_statuses:
        delete_transactions_by_reference(reference)


# ==================== STOCK TRANSACTION DELETE SIGNAL ====================
# Transaction delete হলে stock reverse করে

@receiver(post_delete, sender='erp.StockTransaction')
def stock_transaction_post_delete(sender, instance, **kwargs):
    """Transaction delete হলে warehouse stock reverse করে"""
    from erp.models import ProductWarehouseStock
    
    stock = ProductWarehouseStock.objects.filter(
        product=instance.product,
        warehouse=instance.warehouse
    ).first()
    
    if stock:
        if instance.transaction_type in ['in', 'transfer_in']:
            stock.quantity -= instance.quantity
        elif instance.transaction_type in ['out', 'transfer_out']:
            stock.quantity += instance.quantity
        elif instance.transaction_type == 'adjustment':
            stock.quantity -= instance.quantity
        
        if stock.quantity < 0:
            stock.quantity = Decimal('0.00')
        stock.save()



# ==================== PRODUCTION ISSUE SIGNALS ====================
# Status: issued → Components OUT for multiple production orders

@receiver(pre_save, sender='erp.ProductionIssue')
def production_issue_pre_save(sender, instance, **kwargs):
    instance._old_status = None
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='erp.ProductionIssue')
def production_issue_post_save(sender, instance, **kwargs):
    from django.db import transaction as db_transaction
    
    old_status = getattr(instance, '_old_status', None)
    reference = f"PI:{instance.issue_number}"
    
    def process_issue():
        if not is_already_processed(reference):
            # Process items (components) from ProductionIssueItem
            for item in instance.items.all():
                if item.issued_quantity > 0:
                    create_stock_transaction(
                        product=item.product,
                        warehouse=instance.warehouse,
                        transaction_type='out',
                        quantity=item.issued_quantity,
                        reference=reference,
                        notes=f"Component issued: {item.product.name}"
                    )
    
    if instance.status == 'issued' and old_status != 'issued':
        db_transaction.on_commit(process_issue)
    
    elif old_status == 'issued' and instance.status != 'issued':
        delete_transactions_by_reference(reference)
