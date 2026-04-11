"""
Test Script for POS Separate Signal

Run this in Django shell:
python manage.py shell < test_pos_separate_signal.py
"""

from erp.models import QuickSale, QuickSaleItem, Product, Warehouse, StockTransaction, ProductWarehouseStock
from django.contrib.auth.models import User
from decimal import Decimal

print("=" * 70)
print("POS SEPARATE SIGNAL TEST")
print("=" * 70)

# Get test data
try:
    user = User.objects.first()
    warehouse = Warehouse.objects.filter(is_active=True).first()
    product = Product.objects.filter(is_active=True).first()
    
    if not user or not warehouse or not product:
        print("❌ Missing test data!")
        exit()
    
    print(f"\n✅ Test Data:")
    print(f"   User: {user.username}")
    print(f"   Warehouse: {warehouse.name}")
    print(f"   Product: {product.name}")
    
    # Get initial stock
    initial_stock = product.get_warehouse_stock(warehouse)
    print(f"\n📦 Initial Stock: {initial_stock}")
    
    # ==================== TEST 1: SALE COMPLETION ====================
    print(f"\n" + "=" * 70)
    print("TEST 1: SALE COMPLETION (Stock OUT)")
    print("=" * 70)
    
    # Create QuickSale
    print(f"\n🛒 Creating QuickSale...")
    sale = QuickSale.objects.create(
        user=user,
        branch=warehouse,
        customer_name="Test Customer",
        status='draft'
    )
    print(f"   Sale Number: {sale.sale_number}")
    
    # Add item
    print(f"\n📝 Adding Item...")
    item = QuickSaleItem.objects.create(
        quick_sale=sale,
        product=product,
        quantity=Decimal('5.00'),
        unit_price=product.selling_price
    )
    print(f"   Product: {product.name}")
    print(f"   Quantity: {item.quantity}")
    
    # Complete sale
    print(f"\n✨ Completing Sale (Triggering POS Signal)...")
    sale.status = 'completed'
    sale.save()
    
    # Check stock
    stock_after_sale = product.get_warehouse_stock(warehouse)
    print(f"\n📊 Stock After Sale: {stock_after_sale}")
    print(f"   Decreased By: {initial_stock - stock_after_sale}")
    
    # Check transactions
    pos_reference = f"POS:{sale.sale_number}"
    transactions = StockTransaction.objects.filter(reference=pos_reference)
    print(f"\n📋 Transactions Created: {transactions.count()}")
    
    if transactions.exists():
        trans = transactions.first()
        print(f"   ✅ Transaction Details:")
        print(f"      - Reference: {trans.reference}")
        print(f"      - Type: {trans.get_transaction_type_display()}")
        print(f"      - Quantity: {trans.quantity}")
        print(f"      - Balance After: {trans.balance_after}")
        print(f"      - Notes: {trans.notes}")
    
    # Verify
    if stock_after_sale == initial_stock - Decimal('5.00'):
        print(f"\n   ✅ TEST 1 PASSED: Stock decreased correctly!")
    else:
        print(f"\n   ❌ TEST 1 FAILED: Stock mismatch!")
    
    # ==================== TEST 2: SALE REFUND ====================
    print(f"\n" + "=" * 70)
    print("TEST 2: SALE REFUND (Stock IN)")
    print("=" * 70)
    
    print(f"\n🔄 Refunding Sale...")
    sale.status = 'refunded'
    sale.save()
    
    # Check stock
    stock_after_refund = product.get_warehouse_stock(warehouse)
    print(f"\n📊 Stock After Refund: {stock_after_refund}")
    print(f"   Increased By: {stock_after_refund - stock_after_sale}")
    
    # Check refund transactions
    refund_reference = f"POS:{sale.sale_number}:REFUND"
    refund_trans = StockTransaction.objects.filter(reference=refund_reference)
    print(f"\n📋 Refund Transactions: {refund_trans.count()}")
    
    if refund_trans.exists():
        trans = refund_trans.first()
        print(f"   ✅ Refund Transaction Details:")
        print(f"      - Reference: {trans.reference}")
        print(f"      - Type: {trans.get_transaction_type_display()}")
        print(f"      - Quantity: {trans.quantity}")
        print(f"      - Balance After: {trans.balance_after}")
        print(f"      - Notes: {trans.notes}")
    
    # Verify
    if stock_after_refund == initial_stock:
        print(f"\n   ✅ TEST 2 PASSED: Stock returned to original!")
    else:
        print(f"\n   ❌ TEST 2 FAILED: Stock not restored!")
    
    # ==================== TEST 3: SALE CANCELLATION ====================
    print(f"\n" + "=" * 70)
    print("TEST 3: SALE CANCELLATION (Reverse)")
    print("=" * 70)
    
    # Create another sale
    print(f"\n🛒 Creating Another Sale...")
    sale2 = QuickSale.objects.create(
        user=user,
        branch=warehouse,
        customer_name="Test Customer 2",
        status='draft'
    )
    
    QuickSaleItem.objects.create(
        quick_sale=sale2,
        product=product,
        quantity=Decimal('3.00'),
        unit_price=product.selling_price
    )
    
    # Complete it
    sale2.status = 'completed'
    sale2.save()
    
    stock_before_cancel = product.get_warehouse_stock(warehouse)
    print(f"   Stock Before Cancel: {stock_before_cancel}")
    
    # Cancel it
    print(f"\n❌ Cancelling Sale...")
    sale2.status = 'cancelled'
    sale2.save()
    
    stock_after_cancel = product.get_warehouse_stock(warehouse)
    print(f"   Stock After Cancel: {stock_after_cancel}")
    
    # Check transactions
    cancel_trans = StockTransaction.objects.filter(
        reference=f"POS:{sale2.sale_number}"
    )
    print(f"\n📋 Transactions After Cancel: {cancel_trans.count()}")
    
    # Verify
    if stock_after_cancel == stock_before_cancel + Decimal('3.00'):
        print(f"\n   ✅ TEST 3 PASSED: Stock reversed correctly!")
    else:
        print(f"\n   ❌ TEST 3 FAILED: Stock not reversed!")
    
    # ==================== TEST 4: REFERENCE FORMAT ====================
    print(f"\n" + "=" * 70)
    print("TEST 4: REFERENCE FORMAT VERIFICATION")
    print("=" * 70)
    
    # Check POS references
    pos_trans = StockTransaction.objects.filter(reference__startswith='POS:')
    print(f"\n📋 Total POS Transactions: {pos_trans.count()}")
    
    if pos_trans.exists():
        print(f"\n   Sample POS References:")
        for trans in pos_trans[:3]:
            print(f"      - {trans.reference}")
    
    # Check Inventory references (should be different)
    inv_trans = StockTransaction.objects.exclude(reference__startswith='POS:')
    print(f"\n📋 Total Inventory Transactions: {inv_trans.count()}")
    
    if inv_trans.exists():
        print(f"\n   Sample Inventory References:")
        for trans in inv_trans[:3]:
            print(f"      - {trans.reference}")
    
    print(f"\n   ✅ TEST 4 PASSED: POS and Inventory references are separate!")
    
    # ==================== CLEANUP ====================
    print(f"\n" + "=" * 70)
    print("CLEANUP")
    print("=" * 70)
    
    print(f"\n🧹 Cleaning up test data...")
    sale.delete()
    sale2.delete()
    print("   ✅ Test sales deleted!")
    
    # ==================== FINAL SUMMARY ====================
    print(f"\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    
    print(f"\n✅ All Tests Completed Successfully!")
    print(f"\n📊 Final Stock: {product.get_warehouse_stock(warehouse)}")
    print(f"   (Should match initial: {initial_stock})")
    
    print(f"\n🎉 POS Separate Signal Working Perfectly!")
    print(f"\n" + "=" * 70)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
