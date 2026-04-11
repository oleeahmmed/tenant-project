"""
Production Module Utility Functions
"""
from decimal import Decimal
from django.db import transaction
import logging

from erp.models import (
    BillOfMaterials, ProductionOrder, ProductionOrderComponent,
    SalesOrder, Warehouse
)

logger = logging.getLogger(__name__)


@transaction.atomic
def copy_bom_to_production_order(bom_id, quantity_to_produce=None, warehouse_id=None, sales_order_id=None):
    """
    Create a production order from a BOM
    Copies all components from the BOM
    """
    try:
        bom = BillOfMaterials.objects.prefetch_related('components__product').get(id=bom_id)
        
        # Set default quantity if not provided
        if quantity_to_produce is None:
            quantity_to_produce = bom.quantity
        
        # Get default warehouse if not provided
        warehouse = None
        if warehouse_id:
            warehouse = Warehouse.objects.get(id=warehouse_id)
        else:
            warehouse = Warehouse.objects.filter(is_active=True).first()
        
        # Get sales order if provided
        sales_order = None
        if sales_order_id:
            sales_order = SalesOrder.objects.get(id=sales_order_id)
        
        # Create production order
        production_order = ProductionOrder.objects.create(
            bom=bom,
            product=bom.product,
            warehouse=warehouse,
            quantity_to_produce=quantity_to_produce,
            sales_order=sales_order,
            status='draft',
        )
        
        logger.info(f"Created production order {production_order.order_number} from BOM {bom.bom_number}")
        
        # Copy components from BOM
        items_created = 0
        for bom_component in bom.components.all():
            try:
                # Calculate required quantity based on production quantity
                required_qty = bom_component.quantity * quantity_to_produce
                # Add scrap percentage
                if bom_component.scrap_percentage > 0:
                    scrap_factor = Decimal('1.00') + (bom_component.scrap_percentage / Decimal('100.00'))
                    required_qty = required_qty * scrap_factor
                
                ProductionOrderComponent.objects.create(
                    production_order=production_order,
                    product=bom_component.product,
                    quantity_required=required_qty,
                    unit_cost=bom_component.unit_cost,
                )
                items_created += 1
            except Exception as item_error:
                logger.error(f"Error copying BOM component {bom_component.id}: {str(item_error)}")
                raise
        
        if items_created == 0:
            return None, "No components to copy from BOM"
        
        logger.info(f"Copied {items_created} components from BOM {bom.bom_number} to production order {production_order.order_number}")
        
        return production_order, None
    except BillOfMaterials.DoesNotExist:
        return None, "Bill of Materials not found"
    except Exception as e:
        logger.error(f"Error in copy_bom_to_production_order: {str(e)}")
        return None, str(e)



@transaction.atomic
def copy_production_order_to_receipt(order_id):
    """
    Create a production receipt from a production order
    Copies the product and planned quantity
    """
    try:
        production_order = ProductionOrder.objects.get(id=order_id)
        
        # Import here to avoid circular imports
        from erp.models import ProductionReceipt, ProductionReceiptItem
        
        # Create production receipt
        production_receipt = ProductionReceipt.objects.create(
            production_order=production_order,
            warehouse=production_order.warehouse,
            status='draft',
        )
        
        logger.info(f"Created production receipt {production_receipt.receipt_number} from order {production_order.order_number}")
        
        # Create receipt item for the finished product
        ProductionReceiptItem.objects.create(
            production_receipt=production_receipt,
            product=production_order.product,
            planned_quantity=production_order.quantity_to_produce,
            received_quantity=production_order.quantity_to_produce,
            unit_cost=Decimal('0.00'),  # Will be calculated based on component costs
        )
        
        logger.info(f"Created receipt item for product {production_order.product.name}")
        
        return production_receipt, None
    except ProductionOrder.DoesNotExist:
        return None, "Production Order not found"
    except Exception as e:
        logger.error(f"Error in copy_production_order_to_receipt: {str(e)}")
        return None, str(e)
