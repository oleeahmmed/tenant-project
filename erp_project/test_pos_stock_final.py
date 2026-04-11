#!/usr/bin/env python
"""
POS Stock Management Test - Final Implementation
Tests the new save() method approach (no signals)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from django.contrib.auth import get_user_model
from erp.models import (
    Product, Warehouse, QuickSale, QuickSaleItem,
    ProductWarehouseStock, StockTransaction
)

User = get_user_model()


def test_pos_stock_management():
    """Test POS stock management via save() method"""
    
    print("\n" + "="*60)
    print("POS STOCK MANAGEMENT TEST - SAVE() METHOD APPROACH")
    print("="*60)
    
    # Setup
    user = User.objects.filter(is_staff=True).first()
    warehouse = Warehouse.objects.filter(is_active=True).first()
    product = Product.objects.filter(is_active=True).first()
    
    if not all([user, warehouse, product]):
        print("❌ Missing required data (user, warehouse, or product)")
        return
    
    print(f"\n📦 Product: {product.name}")
    print(f"🏢 Warehouse: {warehouse.name}")
    print(f"👤 User: {user.username}")
    
    # Get initial stock
    initial_stock = ProductWarehouseStock.objects.filter(
        product=product,
        warehouse=warehouse
    ).first()
    
    initial_qty = initial_stock.quantity if initial_stock else Decimal('0.00')
    print(f"\n📊 Initial Stock: {initial_qty}")
    
    # TEST 1: Create new sale with status='completed'
    print("\n" + "-"*60)
    print("TEST 1: Create New Sale (status='completed')")
    print("-"*60)
    
    sale = QuickSale.objects.create(
        user=user,
        branch=warehouse,
        customer_name="Test Customer",
        status='completed',
        subtotal=Decimal('100.00'),
        total_amount=Decimal('100.00'),
        amount_received=Decimal('100.00')
    )
    
    QuickSaleItem.objects.create(
        quick_sale=sale,
        product=product,
        quantity=Decimal('5.00'),
        unit_price=Decimal('20.00'),
        line_total=Decimal('100.00')
    )
    
    print(f"✅ Sale Created: {sale.sale_number}")
    
    # Check stock after sale
    stock_after_sale = ProductWarehouseStock.objects.get(
        product=product,
        warehouse=warehouse
    )
    print(f"📊 Stock After Sale: {stock_after_sale.quantity}")
    print(f"📉 Stock Decreased: {initial_qty - stock_after_sale.quantity}")
    
    # Check transaction
    reference = f"POS:{sale.sale_number}"
    transactions = StockTransaction.objects.filter(reference=reference)
    print(f"📝 Transactions Created: {transactions.count()}")
    
    if transactions.exists():
        trans = transactions.first()
        print(f"   - Type: {trans.transaction_type}")
        print(f"   - Quantity: {trans.quantity}")
        print(f"   - Reference: {trans.reference}")
    
    # TEST 2: Refund the sale
    print("\n" + "-"*60)
    print("TEST 2: Refund Sale")
    print("-"*60)
    
    sale.status = 'refunded'
    sale.save()
    
    print(f"✅ Sale Refunded: {sale.sale_number}")
    
    # Check stock after refund
    stock_after_refund = ProductWarehouseStock.objects.get(
        product=product,
        warehouse=warehouse
    )
    print(f"📊 Stock After Refund: {stock_after_refund.quantity}")
    print(f"📈 Stock Increased: {stock_after_refund.quantity - stock_after_sale.quantity}")
    
    # Check refund transactions
    refund_reference = f"{reference}:REFUND"
    refund_transactions = StockTransaction.objects.filter(reference=refund_reference)
    print(f"📝 Refund Transactions: {refund_transactions.count()}")
    
    if refund_transactions.exists():
        trans = refund_transactions.first()
        print(f"   - Type: {trans.transaction_type}")
        print(f"   - Quantity: {trans.quantity}")
        print(f"   - Reference: {trans.reference}")
    
    # TEST 3: Create another sale and cancel it
    print("\n" + "-"*60)
    print("TEST 3: Create and Cancel Sale")
    print("-"*60)
    
    sale2 = QuickSale.objects.create(
        user=user,
        branch=warehouse,
        customer_name="Test Customer 2",
        status='completed',
        subtotal=Decimal('50.00'),
        total_amount=Decimal('50.00'),
        amount_received=Decimal('50.00')
    )
    
    QuickSaleItem.objects.create(
        quick_sale=sale2,
        product=product,
        quantity=Decimal('2.00'),
        unit_price=Decimal('25.00'),
        line_total=Decimal('50.00')
    )
    
    print(f"✅ Sale 2 Created: {sale2.sale_number}")
    
    stock_before_cancel = ProductWarehouseStock.objects.get(
        product=product,
        warehouse=warehouse
    ).quantity
    print(f"📊 Stock Before Cancel: {stock_before_cancel}")
    
    # Cancel the sale
    sale2.status = 'cancelled'
    sale2.save()
    
    print(f"✅ Sale 2 Cancelled: {sale2.sale_number}")
    
    stock_after_cancel = ProductWarehouseStock.objects.get(
        product=product,
        warehouse=warehouse
    ).quantity
    print(f"📊 Stock After Cancel: {stock_after_cancel}")
    print(f"📈 Stock Restored: {stock_after_cancel - stock_before_cancel}")
    
    # Check transactions deleted
    reference2 = f"POS:{sale2.sale_number}"
    transactions2 = StockTransaction.objects.filter(reference=reference2)
    print(f"📝 Transactions After Cancel: {transactions2.count()} (should be 0)")
    
    # SUMMARY
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    final_stock = ProductWarehouseStock.objects.get(
        product=product,
        warehouse=warehouse
    ).quantity
    
    print(f"📊 Initial Stock: {initial_qty}")
    print(f"📊 Final Stock: {final_stock}")
    print(f"📊 Net Change: {final_stock - initial_qty}")
    print(f"\n✅ All tests completed!")
    
    # Cleanup
    print("\n🧹 Cleaning up test data...")
    sale.delete()
    sale2.delete()
    print("✅ Cleanup complete")


if __name__ == '__main__':
    test_pos_stock_management()
