# Data migration to populate branch fields

from django.db import migrations
from django.contrib.auth.models import User


def populate_branch_fields(apps, schema_editor):
    """Populate branch fields based on user profiles and existing data"""
    
    # Get models
    Warehouse = apps.get_model('erp', 'Warehouse')
    UserProfile = apps.get_model('erp', 'UserProfile')
    
    # Get default warehouse (first active warehouse)
    default_warehouse = Warehouse.objects.filter(is_active=True).first()
    if not default_warehouse:
        print("⚠️  No active warehouse found. Creating default warehouse...")
        default_warehouse = Warehouse.objects.create(
            name="Main Branch",
            code="MAIN",
            is_active=True
        )
    
    # Models to update
    models_to_update = [
        'IncomingPayment', 'OutgoingPayment', 'BankStatement', 'JournalEntry',
        'StockAdjustment', 'GoodsIssue', 'GoodsReceipt', 'GoodsReceiptPO',
        'SalesQuotation', 'SalesReturn', 'Delivery',
        'PurchaseQuotation', 'PurchaseReturn'
    ]
    
    for model_name in models_to_update:
        try:
            Model = apps.get_model('erp', model_name)
            
            # Update records without branch
            updated_count = Model.objects.filter(branch__isnull=True).update(
                branch=default_warehouse
            )
            
            if updated_count > 0:
                print(f"✅ Updated {updated_count} {model_name} records with default branch")
        
        except Exception as e:
            print(f"⚠️  Could not update {model_name}: {e}")
    
    # Special handling for InventoryTransfer (has from_branch and to_branch)
    try:
        InventoryTransfer = apps.get_model('erp', 'InventoryTransfer')
        
        # Update from_branch
        updated_from = InventoryTransfer.objects.filter(from_branch__isnull=True).update(
            from_branch=default_warehouse
        )
        
        # Update to_branch  
        updated_to = InventoryTransfer.objects.filter(to_branch__isnull=True).update(
            to_branch=default_warehouse
        )
        
        if updated_from > 0 or updated_to > 0:
            print(f"✅ Updated InventoryTransfer: {updated_from} from_branch, {updated_to} to_branch")
    
    except Exception as e:
        print(f"⚠️  Could not update InventoryTransfer: {e}")


def reverse_populate_branch_fields(apps, schema_editor):
    """Reverse migration - set branch fields to null"""
    
    models_to_update = [
        'IncomingPayment', 'OutgoingPayment', 'BankStatement', 'JournalEntry',
        'StockAdjustment', 'GoodsIssue', 'GoodsReceipt', 'GoodsReceiptPO',
        'SalesQuotation', 'SalesReturn', 'Delivery',
        'PurchaseQuotation', 'PurchaseReturn', 'InventoryTransfer'
    ]
    
    for model_name in models_to_update:
        try:
            Model = apps.get_model('erp', model_name)
            Model.objects.all().update(branch=None)
            print(f"✅ Cleared branch field for {model_name}")
        except Exception as e:
            print(f"⚠️  Could not clear {model_name}: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0007_add_branch_to_high_priority_models'),
    ]

    operations = [
        migrations.RunPython(
            populate_branch_fields,
            reverse_populate_branch_fields
        ),
    ]
