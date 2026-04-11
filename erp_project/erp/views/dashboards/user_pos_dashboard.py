"""
User POS Dashboard - Dynamic Data from Database
"""
from django.contrib import admin
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from ...models import (
    QuickSale, QuickSaleItem, Product, Customer, Invoice, InvoiceItem, 
    ProductWarehouseStock, UserProfile, Warehouse
)
from django.contrib.auth.models import User


class UserPOSDashboardView(View):
    """User POS Dashboard with Dynamic Data"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=7)
        one_month_ago = today - timedelta(days=30)
        
        # Get current user or selected cashier
        selected_cashier_id = request.GET.get('cashier')
        if request.user.is_superuser and selected_cashier_id:
            try:
                cashier = User.objects.get(id=selected_cashier_id)
            except User.DoesNotExist:
                cashier = request.user
        else:
            cashier = request.user
        
        # Get user's POS Profile and default warehouse
        try:
            pos_profile = cashier.profile
            default_warehouse = pos_profile.branch
        except UserProfile.DoesNotExist:
            pos_profile = None
            default_warehouse = None
        
        # SALES BALANCE - Only this user's sales
        sales_today = QuickSale.objects.filter(
            user=cashier,
            sale_date=today,
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        sales_7days = QuickSale.objects.filter(
            user=cashier,
            sale_date__gte=seven_days_ago,
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # STOCK BALANCE - From user's default warehouse only
        if default_warehouse:
            stock_today = ProductWarehouseStock.objects.filter(
                warehouse=default_warehouse
            ).aggregate(
                total=Sum(F('quantity') * F('product__selling_price'))
            )['total'] or Decimal('0.00')
        else:
            stock_today = Decimal('0.00')
        
        # EXPENSES - Calculate from cost of goods sold (simplified)
        # Since we don't have an Expense model, we'll calculate from purchase price
        expenses_today = Decimal('0.00')
        expenses_list = []
        total_expenses = Decimal('0.00')
        
        # Calculate COGS for today's sales
        today_items = QuickSaleItem.objects.filter(
            quick_sale__user=cashier,
            quick_sale__sale_date=today,
            quick_sale__status='completed'
        ).select_related('product')
        
        for item in today_items:
            cost = (item.product.purchase_price or Decimal('0.00')) * item.quantity
            expenses_today += cost
            expenses_list.append({
                'expense_type': f'COGS - {item.product.name}',
                'created_by': cashier,
                'created_at': item.quick_sale.created_at,
                'amount': cost
            })
        
        total_expenses = expenses_today
        
        # ONLINE PAYMENTS - Only this user's sales
        online_payments = QuickSale.objects.filter(
            user=cashier,
            sale_date=today,
            status='completed'
        ).values('payment_method').annotate(
            total=Sum('total_amount')
        )
        
        payment_dict = {p['payment_method']: p['total'] for p in online_payments}
        bkash_payment = payment_dict.get('mobile', Decimal('0.00'))  # Mobile = Bkash
        card_payment = payment_dict.get('card', Decimal('0.00'))
        cash_payment = payment_dict.get('cash', Decimal('0.00'))
        mixed_payment = payment_dict.get('mixed', Decimal('0.00'))
        total_payment = bkash_payment + card_payment + cash_payment + mixed_payment
        
        # DUE CUSTOMERS - From this user's QuickSales with due amount
        due_sales = QuickSale.objects.filter(
            user=cashier,
            status='completed'
        ).annotate(
            due_amount=F('total_amount') - F('amount_received')
        ).filter(
            due_amount__gt=0
        ).select_related('customer').order_by('-sale_date')[:10]
        
        total_due = QuickSale.objects.filter(
            user=cashier,
            status='completed'
        ).annotate(
            due_amount=F('total_amount') - F('amount_received')
        ).filter(
            due_amount__gt=0
        ).aggregate(total=Sum('due_amount'))['total'] or Decimal('0.00')
        
        # PRODUCT STOCK AND SALES
        # Get products from user's default warehouse only
        if default_warehouse:
            products_with_stock = ProductWarehouseStock.objects.filter(
                warehouse=default_warehouse
            ).select_related('product').values(
                'product__id', 'product__name', 'product__unit', 'quantity'
            ).order_by('-quantity')[:20]
        else:
            products_with_stock = []
        
        # Sales by product today - Only this user's sales
        product_sales_today = QuickSaleItem.objects.filter(
            quick_sale__user=cashier,
            quick_sale__sale_date=today,
            quick_sale__status='completed'
        ).values('product__name').annotate(
            total_qty=Sum('quantity')
        )
        
        sales_dict = {p['product__name']: p['total_qty'] for p in product_sales_today}
        
        # Combine stock and sales data
        products_stock = []
        for item in products_with_stock:
            product_name = item['product__name']
            products_stock.append({
                'name': product_name,
                'stock': item['quantity'],
                'unit': item['product__unit'],
                'sales': sales_dict.get(product_name, Decimal('0.00'))
            })
        
        # All cashiers for dropdown
        all_cashiers = User.objects.filter(
            is_staff=True,
            quick_sales__isnull=False
        ).distinct().order_by('username')
        
        context = {
            **admin.site.each_context(request),
            'title': 'My POS Dashboard',
            'subtitle': 'Dashboard for Operator',
            'selected_cashier': cashier,
            'all_cashiers': all_cashiers,
            'is_superuser': request.user.is_superuser,
            'pos_profile': pos_profile,
            'default_warehouse': default_warehouse,
            
            # Sales Balance
            'sales_today': sales_today,
            'sales_7days': sales_7days,
            
            # Stock Balance
            'stock_today': stock_today,
            
            # Expenses
            'expenses_today': expenses_today,
            'expenses_list': expenses_list,
            'total_expenses': total_expenses,
            
            # Online Payments
            'bkash_payment': bkash_payment,
            'card_payment': card_payment,
            'cash_payment': cash_payment,
            'mixed_payment': mixed_payment,
            'total_payment': total_payment,
            
            # Due Customers
            'due_customers': due_sales,
            'total_due': total_due,
            
            # Products
            'products_stock': products_stock,
        }
        
        return render(request, 'admin/erp/dashboards/user_pos_dashboard.html', context)
