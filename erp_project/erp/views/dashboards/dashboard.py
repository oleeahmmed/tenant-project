"""
Dashboard View
"""
from django.contrib import admin
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from ...models import (
    SalesOrder, Invoice, InvoiceItem, PurchaseOrder,
    Product, Customer, Supplier, Warehouse, BankAccount,
    Project, ProductionOrder, PurchaseInvoice
)


class DashboardView(View):
    """ERP Dashboard View with Charts"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        
        # ==================== KEY METRICS ====================
        
        # Master Data Counts
        total_customers = Customer.objects.filter(is_active=True).count()
        total_suppliers = Supplier.objects.filter(is_active=True).count()
        total_products = Product.objects.filter(is_active=True).count()
        total_warehouses = Warehouse.objects.filter(is_active=True).count()
        
        # Sales Metrics
        total_sales_orders = SalesOrder.objects.count()
        pending_sales_orders = SalesOrder.objects.filter(status__in=['draft', 'confirmed']).count()
        total_invoices = Invoice.objects.count()
        unpaid_invoices = Invoice.objects.filter(status__in=['draft', 'sent', 'partially_paid']).count()
        
        # Purchase Metrics
        total_purchase_orders = PurchaseOrder.objects.count()
        pending_purchase_orders = PurchaseOrder.objects.filter(status__in=['draft', 'sent']).count()
        
        # Production Metrics
        active_projects = Project.objects.filter(status='active').count()
        active_production_orders = ProductionOrder.objects.filter(status__in=['draft', 'planned', 'in_progress']).count()
        
        # Financial Metrics
        total_revenue = Invoice.objects.filter(
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        total_receivables = Invoice.objects.filter(
            status__in=['sent', 'partially_paid', 'overdue']
        ).aggregate(total=Sum('due_amount'))['total'] or Decimal('0.00')
        
        total_payables = PurchaseInvoice.objects.filter(
            status__in=['received', 'partially_paid', 'overdue']
        ).aggregate(total=Sum('due_amount'))['total'] or Decimal('0.00')
        
        # Monthly revenue
        monthly_revenue = Invoice.objects.filter(
            invoice_date__year=today.year,
            invoice_date__month=today.month,
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Bank balance
        total_bank_balance = BankAccount.objects.filter(
            is_active=True
        ).aggregate(total=Sum('current_balance'))['total'] or Decimal('0.00')
        
        # Inventory value (calculated from warehouse stocks)
        from ...models import ProductWarehouseStock
        total_stock_value = ProductWarehouseStock.objects.aggregate(
            total=Sum(F('quantity') * F('product__purchase_price'))
        )['total'] or Decimal('0.00')
        
        # Low stock products (using Python since current_stock is a property)
        low_stock_products_list = [
            p for p in Product.objects.filter(is_active=True)
            if p.current_stock <= p.min_stock_level
        ]
        low_stock_count = len(low_stock_products_list)
        
        # ==================== CHART DATA ====================
        
        # 1. Weekly Sales Trend (Last 7 days)
        weekly_sales = []
        weekly_labels = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            sales = Invoice.objects.filter(
                invoice_date=date,
                status='paid'
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            weekly_sales.append(float(sales))
            weekly_labels.append(date.strftime('%d %b'))
        
        # 2. Sales vs Purchase (Last 6 months)
        sales_vs_purchase_labels = []
        sales_data = []
        purchase_data = []
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=i*30)
            month_label = month_date.strftime('%b %Y')
            sales_vs_purchase_labels.append(month_label)
            
            sales = Invoice.objects.filter(
                invoice_date__year=month_date.year,
                invoice_date__month=month_date.month,
                status='paid'
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            sales_data.append(float(sales))
            
            purchases = PurchaseOrder.objects.filter(
                order_date__year=month_date.year,
                order_date__month=month_date.month
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            purchase_data.append(float(purchases))
        
        # 3. Sales Order Status Distribution
        order_status_labels = ['Draft', 'Confirmed', 'Processing', 'Completed', 'Cancelled']
        order_status_data = [
            SalesOrder.objects.filter(status='draft').count(),
            SalesOrder.objects.filter(status='confirmed').count(),
            SalesOrder.objects.filter(status='processing').count(),
            SalesOrder.objects.filter(status='completed').count(),
            SalesOrder.objects.filter(status='cancelled').count(),
        ]
        
        # 4. Top 5 Products by Revenue
        top_products = InvoiceItem.objects.values(
            'product__name'
        ).annotate(
            total_revenue=Sum('line_total')
        ).order_by('-total_revenue')[:5]
        
        product_names = [p['product__name'] for p in top_products]
        product_revenues = [float(p['total_revenue']) for p in top_products]
        
        # 5. Top 5 Customers by Revenue
        top_customers = Invoice.objects.filter(
            status='paid'
        ).values('customer__name').annotate(
            total=Sum('total_amount')
        ).order_by('-total')[:5]
        
        customer_names = [c['customer__name'] for c in top_customers]
        customer_revenues = [float(c['total']) for c in top_customers]
        
        # 6. Inventory Status (using Python since current_stock is a property)
        all_products = Product.objects.filter(is_active=True)
        in_stock = sum(1 for p in all_products if p.current_stock > p.min_stock_level)
        low_stock = sum(1 for p in all_products if 0 < p.current_stock <= p.min_stock_level)
        out_of_stock = sum(1 for p in all_products if p.current_stock <= 0)
        
        inventory_labels = ['In Stock', 'Low Stock', 'Out of Stock']
        inventory_data = [in_stock, low_stock, out_of_stock]
        
        # ==================== RECENT ACTIVITIES ====================
        
        # Recent Sales Orders
        recent_sales_orders = SalesOrder.objects.select_related(
            'customer', 'salesperson'
        ).order_by('-created_at')[:5]
        
        # Recent Purchase Orders
        recent_purchase_orders = PurchaseOrder.objects.select_related(
            'supplier'
        ).order_by('-created_at')[:5]
        
        # Recent Invoices
        recent_invoices = Invoice.objects.select_related(
            'customer'
        ).order_by('-created_at')[:5]
        
        # Low Stock Products (already calculated above)
        low_stock_products = sorted(
            low_stock_products_list,
            key=lambda p: p.current_stock
        )[:10]
        
        context = {
            **admin.site.each_context(request),
            'title': 'ERP Dashboard',
            'subtitle': 'Business Overview & Analytics',
            
            # Key Metrics
            'total_customers': total_customers,
            'total_suppliers': total_suppliers,
            'total_products': total_products,
            'total_warehouses': total_warehouses,
            'total_sales_orders': total_sales_orders,
            'pending_sales_orders': pending_sales_orders,
            'total_invoices': total_invoices,
            'unpaid_invoices': unpaid_invoices,
            'total_purchase_orders': total_purchase_orders,
            'pending_purchase_orders': pending_purchase_orders,
            'active_projects': active_projects,
            'active_production_orders': active_production_orders,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'total_receivables': total_receivables,
            'total_payables': total_payables,
            'total_bank_balance': total_bank_balance,
            'total_stock_value': total_stock_value,
            'low_stock_count': low_stock_count,
            
            # Chart Data (JSON)
            'weekly_sales': json.dumps(weekly_sales),
            'weekly_labels': json.dumps(weekly_labels),
            'sales_vs_purchase_labels': json.dumps(sales_vs_purchase_labels),
            'sales_data': json.dumps(sales_data),
            'purchase_data': json.dumps(purchase_data),
            'order_status_labels': json.dumps(order_status_labels),
            'order_status_data': json.dumps(order_status_data),
            'product_names': json.dumps(product_names),
            'product_revenues': json.dumps(product_revenues),
            'customer_names': json.dumps(customer_names),
            'customer_revenues': json.dumps(customer_revenues),
            'inventory_labels': json.dumps(inventory_labels),
            'inventory_data': json.dumps(inventory_data),
            
            # Recent Activities
            'recent_sales_orders': recent_sales_orders,
            'recent_purchase_orders': recent_purchase_orders,
            'recent_invoices': recent_invoices,
            'low_stock_products': low_stock_products,
        }
        
        return render(request, 'admin/erp/dashboards/dashboard.html', context)
