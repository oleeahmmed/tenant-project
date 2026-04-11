# Generated migration to populate branch fields

from django.db import migrations

def populate_branch_fields(apps, schema_editor):
    """Populate branch fields with first warehouse for existing records"""
    Warehouse = apps.get_model('erp', 'Warehouse')
    SalesOrder = apps.get_model('erp', 'SalesOrder')
    Invoice = apps.get_model('erp', 'Invoice')
    PurchaseOrder = apps.get_model('erp', 'PurchaseOrder')
    PurchaseInvoice = apps.get_model('erp', 'PurchaseInvoice')
    QuickSale = apps.get_model('erp', 'QuickSale')
    
    # Get first warehouse as default
    first_warehouse = Warehouse.objects.filter(is_active=True).first()
    if not first_warehouse:
        # Create a default warehouse if none exists
        first_warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="MAIN",
            is_active=True
        )
    
    # Update all records with null branch
    SalesOrder.objects.filter(branch__isnull=True).update(branch=first_warehouse)
    Invoice.objects.filter(branch__isnull=True).update(branch=first_warehouse)
    PurchaseOrder.objects.filter(branch__isnull=True).update(branch=first_warehouse)
    PurchaseInvoice.objects.filter(branch__isnull=True).update(branch=first_warehouse)
    QuickSale.objects.filter(branch__isnull=True).update(branch=first_warehouse)

def reverse_populate_branch_fields(apps, schema_editor):
    """Reverse migration - set all branch fields to null"""
    SalesOrder = apps.get_model('erp', 'SalesOrder')
    Invoice = apps.get_model('erp', 'Invoice')
    PurchaseOrder = apps.get_model('erp', 'PurchaseOrder')
    PurchaseInvoice = apps.get_model('erp', 'PurchaseInvoice')
    QuickSale = apps.get_model('erp', 'QuickSale')
    
    SalesOrder.objects.all().update(branch=None)
    Invoice.objects.all().update(branch=None)
    PurchaseOrder.objects.all().update(branch=None)
    PurchaseInvoice.objects.all().update(branch=None)
    QuickSale.objects.all().update(branch=None)

class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0005_add_branch_system'),
    ]

    operations = [
        migrations.RunPython(populate_branch_fields, reverse_populate_branch_fields),
    ]