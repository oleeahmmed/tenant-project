"""
Inventory Dashboard View - Comprehensive Stock & Warehouse Analytics
Optimized with Django 6 Tasks for maximum performance
Expert-level inventory management insights
"""
from django.contrib import admin
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, F, Q, DecimalField, ExpressionWrapper
from django.utils import timezone
from django.core.cache import cache
from django.tasks import task
from datetime import timedelta
from decimal import Decimal
import uuid

from ...models import (
    Product, StockTransaction, Warehouse, Category, ProductWarehouseStock,
    SalesOrderItem, PurchaseOrderItem, QuickSaleItem
)


@task()
def generate_inventory_dashboard_data(task_id, date_range, user_id):
    """Background task for generating inventory dashboard data"""
    try:
        cache.set(f'inventory_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Calculating date range...', 'progress': 5
        }, timeout=300)
        
        today = timezone.now().date()
        
        # Calculate date range for movements
        if date_range == 'today':
            start_date = end_date = today
        elif date_range == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif date_range == 'month':
            start_date = today.replace(day=1)
            end_date = today
        elif date_range == 'prev_month':
            first_day_current = today.replace(day=1)
            last_day_prev = first_day_current - timedelta(days=1)
            start_date = last_day_prev.replace(day=1)
            end_date = last_day_prev
        elif date_range == 'year':
            start_date = today.replace(month=1, day=1)
            end_date = today
        else:  # all
            start_date = None
            end_date = None
        
        cache.set(f'inventory_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Analyzing inventory levels...', 'progress': 15
        }, timeout=300)
        
        # Get all products with current stock
        products = Product.objects.all()
        
        # Calculate total stock value using ProductWarehouseStock
        total_stock_value = Decimal('0.00')
        for product in products:
            stock_qty = product.current_stock  # This uses the property
            total_stock_value += stock_qty * (product.purchase_price or Decimal('0.00'))
        
        # Low stock alerts (below min_stock_level)
        low_stock_count = 0
        out_of_stock_count = 0
        reorder_needed = 0
        
        for product in products:
            stock = product.current_stock
            if stock == 0:
                out_of_stock_count += 1
            elif stock <= product.min_stock_level:
                low_stock_count += 1
                reorder_needed += 1
        
        # Total SKUs
        total_skus = products.count()
        active_skus = sum(1 for p in products if p.current_stock > 0)
        
        # Dead stock (no movement in last 90 days)
        ninety_days_ago = today - timedelta(days=90)
        recent_movements = StockTransaction.objects.filter(
            created_at__date__gte=ninety_days_ago
        ).values_list('product_id', flat=True).distinct()
        dead_stock_count = sum(1 for p in products if p.id not in recent_movements and p.current_stock > 0)
        
        cache.set(f'inventory_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Calculating stock movements...', 'progress': 30
        }, timeout=300)
        
        # Stock movements
        movements_qs = StockTransaction.objects.all()
        if start_date and end_date:
            movements_qs = movements_qs.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
        
        total_inbound = movements_qs.filter(transaction_type='in').aggregate(total=Sum('quantity'))['total'] or 0
        total_outbound = movements_qs.filter(transaction_type='out').aggregate(total=Sum('quantity'))['total'] or 0
        
        cache.set(f'inventory_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Generating charts...', 'progress': 50
        }, timeout=300)
        
        # Stock Level Trend (last 30 days)
        stock_trend_labels = []
        stock_trend_data = []
        for i in range(29, -1, -1):
            date = today - timedelta(days=i)
            # This is simplified - in production you'd track historical stock levels
            stock_trend_labels.append(date.strftime('%d %b'))
            stock_trend_data.append(float(total_stock_value))  # Simplified
        
        # ABC Analysis - Top 20% products by value
        products_with_value = []
        for p in products:
            stock_qty = p.current_stock
            value = float(stock_qty * (p.purchase_price or Decimal('0.00')))
            if value > 0:
                products_with_value.append({
                    'name': p.name,
                    'value': value,
                    'stock': float(stock_qty)
                })
        
        products_with_value.sort(key=lambda x: x['value'], reverse=True)
        abc_products = products_with_value[:10]
        abc_names = [p['name'] for p in abc_products]
        abc_values = [p['value'] for p in abc_products]
        
        # Stock Movement Trend (In vs Out)
        movement_labels = []
        inbound_data = []
        outbound_data = []
        days_to_show = 30 if date_range in ['month', 'prev_month', 'all'] else 7
        
        for i in range(days_to_show - 1, -1, -1):
            date = (end_date or today) - timedelta(days=i)
            if start_date and date < start_date:
                continue
            inbound = StockTransaction.objects.filter(created_at__date=date, transaction_type='in').aggregate(total=Sum('quantity'))['total'] or 0
            outbound = StockTransaction.objects.filter(created_at__date=date, transaction_type='out').aggregate(total=Sum('quantity'))['total'] or 0
            movement_labels.append(date.strftime('%d %b'))
            inbound_data.append(float(inbound))
            outbound_data.append(float(outbound))
        
        cache.set(f'inventory_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Analyzing product performance...', 'progress': 70
        }, timeout=300)
        
        # Top Moving Products (by quantity sold)
        top_movers = []
        for product in products:
            if start_date and end_date:
                sales_qty = SalesOrderItem.objects.filter(
                    product=product,
                    sales_order__order_date__gte=start_date,
                    sales_order__order_date__lte=end_date
                ).aggregate(total=Sum('quantity'))['total'] or 0
                pos_qty = QuickSaleItem.objects.filter(
                    product=product,
                    quick_sale__sale_date__gte=start_date,
                    quick_sale__sale_date__lte=end_date
                ).aggregate(total=Sum('quantity'))['total'] or 0
            else:
                sales_qty = SalesOrderItem.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
                pos_qty = QuickSaleItem.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
            
            total_qty = float(sales_qty) + float(pos_qty)
            if total_qty > 0:
                top_movers.append({'name': product.name, 'qty': total_qty})
        
        top_movers.sort(key=lambda x: x['qty'], reverse=True)
        top_movers = top_movers[:10]
        top_mover_names = [p['name'] for p in top_movers]
        top_mover_quantities = [p['qty'] for p in top_movers]
        
        # Slow Moving Products (low turnover)
        slow_movers = []
        for product in products:
            stock_qty = product.current_stock
            if stock_qty and stock_qty > 0:
                if start_date and end_date:
                    sales_qty = SalesOrderItem.objects.filter(
                        product=product,
                        sales_order__order_date__gte=start_date,
                        sales_order__order_date__lte=end_date
                    ).aggregate(total=Sum('quantity'))['total'] or 0
                    pos_qty = QuickSaleItem.objects.filter(
                        product=product,
                        quick_sale__sale_date__gte=start_date,
                        quick_sale__sale_date__lte=end_date
                    ).aggregate(total=Sum('quantity'))['total'] or 0
                else:
                    sales_qty = SalesOrderItem.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
                    pos_qty = QuickSaleItem.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
                
                total_qty = float(sales_qty) + float(pos_qty)
                if total_qty < 5:  # Very low movement
                    slow_movers.append({
                        'name': product.name,
                        'stock': float(stock_qty),
                        'value': float(stock_qty * (product.purchase_price or Decimal('0.00')))
                    })
        
        slow_movers.sort(key=lambda x: x['value'], reverse=True)
        slow_movers = slow_movers[:10]
        slow_mover_names = [p['name'] for p in slow_movers]
        slow_mover_values = [p['value'] for p in slow_movers]
        
        # Stock by Category
        category_stock = {}
        for product in products:
            if product.category:
                cat_name = product.category.name
                if cat_name not in category_stock:
                    category_stock[cat_name] = Decimal('0.00')
                stock_qty = product.current_stock
                category_stock[cat_name] += stock_qty * (product.purchase_price or Decimal('0.00'))
        
        category_names = list(category_stock.keys())[:8]
        category_values = [float(category_stock[name]) for name in category_names]
        
        # Stock by Warehouse
        warehouse_stock = {}
        for warehouse in Warehouse.objects.all():
            warehouse_products = ProductWarehouseStock.objects.filter(warehouse=warehouse)
            total_value = Decimal('0.00')
            for ws in warehouse_products:
                total_value += ws.quantity * (ws.product.purchase_price or Decimal('0.00'))
            if total_value > 0:
                warehouse_stock[warehouse.name] = float(total_value)
        
        warehouse_names = list(warehouse_stock.keys())
        warehouse_values = list(warehouse_stock.values())
        
        cache.set(f'inventory_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Finalizing data...', 'progress': 90
        }, timeout=300)
        
        # Stock Status Distribution
        stock_status_labels = ['In Stock', 'Low Stock', 'Out of Stock']
        stock_status_values = [
            active_skus - low_stock_count,
            low_stock_count,
            out_of_stock_count
        ]
        
        # Reorder Analysis
        reorder_products = []
        for product in products:
            stock = product.current_stock
            if stock <= product.min_stock_level:
                reorder_products.append({
                    'product': product,
                    'current': float(stock),
                    'min': float(product.min_stock_level)
                })
        
        reorder_products.sort(key=lambda x: x['current'])
        reorder_products = reorder_products[:10]
        
        reorder_names = [r['product'].name for r in reorder_products]
        reorder_current = [r['current'] for r in reorder_products]
        reorder_points = [r['min'] for r in reorder_products]
        
        result = {
            'kpis': {
                'total_stock_value': float(total_stock_value),
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count,
                'reorder_needed': reorder_needed,
                'total_skus': total_skus,
                'active_skus': active_skus,
                'dead_stock_count': dead_stock_count,
                'total_inbound': float(total_inbound),
                'total_outbound': float(total_outbound),
            },
            'charts': {
                'stock_trend_labels': stock_trend_labels,
                'stock_trend_data': stock_trend_data,
                'abc_names': abc_names,
                'abc_values': abc_values,
                'movement_labels': movement_labels,
                'inbound_data': inbound_data,
                'outbound_data': outbound_data,
                'top_mover_names': top_mover_names,
                'top_mover_quantities': top_mover_quantities,
                'slow_mover_names': slow_mover_names,
                'slow_mover_values': slow_mover_values,
                'category_names': category_names,
                'category_values': category_values,
                'warehouse_names': warehouse_names,
                'warehouse_values': warehouse_values,
                'stock_status_labels': stock_status_labels,
                'stock_status_values': stock_status_values,
                'reorder_names': reorder_names,
                'reorder_current': reorder_current,
                'reorder_points': reorder_points,
            }
        }
        
        cache.set(f'inventory_dashboard_task_{task_id}_result', result, timeout=300)
        cache.set(f'inventory_dashboard_task_{task_id}_progress', {
            'state': 'SUCCESS', 'status': 'Dashboard data ready!', 'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'inventory_dashboard_task_{task_id}_progress', {
            'state': 'FAILURE', 'status': f'Error: {str(e)}', 'progress': 0
        }, timeout=300)


class InventoryDashboardView(View):
    """Inventory Dashboard with comprehensive stock analytics"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # Recent Activities
        recent_movements = StockTransaction.objects.select_related('product', 'warehouse').order_by('-created_at')[:15]
        
        # Critical Stock Alerts
        products = Product.objects.all()
        critical_stock = []
        for product in products:
            stock = product.current_stock
            if stock <= product.min_stock_level:
                critical_stock.append(product)
        
        critical_stock.sort(key=lambda p: p.current_stock)
        critical_stock = critical_stock[:10]
        
        context = {
            **admin.site.each_context(request),
            'title': 'Inventory Dashboard',
            'subtitle': 'Stock Management & Warehouse Analytics',
            'recent_movements': recent_movements,
            'critical_stock': critical_stock,
        }
        
        return render(request, 'admin/erp/dashboards/inventory_dashboard.html', context)


class StartInventoryDashboardDataTaskView(View):
    """API endpoint to start inventory dashboard data generation task"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        date_range = request.GET.get('range', 'month')
        
        # Check cache first
        cache_key = f"inventory_dashboard_data_{date_range}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        
        # Start background task
        task_id = str(uuid.uuid4())
        generate_inventory_dashboard_data.enqueue(task_id, date_range, request.user.id)
        cache.set(f'inventory_dashboard_task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckInventoryDashboardTaskStatusView(View):
    """API endpoint to check inventory dashboard task status"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress_data = cache.get(f'inventory_dashboard_task_{task_id}_progress')
        
        if not progress_data:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found', 'progress': 0})
        
        response = {
            'state': progress_data['state'],
            'status': progress_data['status'],
            'progress': progress_data['progress']
        }
        
        if progress_data['state'] == 'SUCCESS':
            result = cache.get(f'inventory_dashboard_task_{task_id}_result')
            response['data'] = result
            
            # Cache the result
            cache_key = cache.get(f'inventory_dashboard_task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=1800)  # 30 minutes
        
        elif progress_data['state'] == 'FAILURE':
            response['error'] = progress_data['status']
        
        return JsonResponse(response)
