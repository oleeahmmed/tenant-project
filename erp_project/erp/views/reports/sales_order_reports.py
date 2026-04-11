"""
Sales Order Reports with Django 6.0 Built-in Tasks
Optimized Sales Order Reports: Detail & Summary
- Async operations with alist() and aaggregate()
- No Python loops - all operations in database
- Caching for instant repeated requests
- Background task processing with progress tracking
"""
from django.contrib import admin
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.core.cache import cache
from django.db.models import Sum, Count, Avg
from django.tasks import task
from decimal import Decimal
from datetime import datetime
import uuid
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side

from ...models import (
    SalesOrder, SalesOrderItem,
    Customer, SalesPerson, Product
)


# ==================== BACKGROUND TASK FUNCTIONS ====================

@task()
def generate_sales_order_detail_report(task_id, filters, user_id):
    """Background task for Sales Order detail report generation"""
    try:
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Starting report generation...',
            'progress': 10
        }, timeout=300)
        
        items_qs = SalesOrderItem.objects.select_related(
            'sales_order', 'sales_order__customer', 
            'sales_order__salesperson', 'product'
        )
        
        if filters.get('from_date'):
            items_qs = items_qs.filter(sales_order__order_date__gte=filters['from_date'])
        if filters.get('to_date'):
            items_qs = items_qs.filter(sales_order__order_date__lte=filters['to_date'])
        if filters.get('customer_id'):
            items_qs = items_qs.filter(sales_order__customer_id=filters['customer_id'])
        if filters.get('salesperson_id'):
            items_qs = items_qs.filter(sales_order__salesperson_id=filters['salesperson_id'])
        if filters.get('product_id'):
            items_qs = items_qs.filter(product_id=filters['product_id'])
        if filters.get('status'):
            items_qs = items_qs.filter(sales_order__status=filters['status'])
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Fetching data from database...',
            'progress': 30
        }, timeout=300)
        
        limit = filters.get('limit', '50')
        
        items_data_query = items_qs.values(
            'sales_order__order_number',
            'sales_order__order_date',
            'sales_order__delivery_date',
            'sales_order__customer__name',
            'sales_order__salesperson__name',
            'product__name',
            'quantity',
            'unit_price',
            'line_total',
            'sales_order__status'
        ).order_by('-sales_order__order_date', '-sales_order__order_number')
        
        if limit != 'all':
            try:
                limit_int = int(limit)
                items_data = list(items_data_query[:limit_int])
            except (ValueError, TypeError):
                items_data = list(items_data_query[:50])
        else:
            items_data = list(items_data_query)
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Calculating statistics...',
            'progress': 60
        }, timeout=300)
        
        stats = items_qs.aggregate(
            total_items=Count('id'),
            total_amount=Sum('line_total'),
            total_quantity=Sum('quantity'),
            unique_count=Count('sales_order', distinct=True)
        )
        
        formatted_items = [
            {
                'order_number': item['sales_order__order_number'],
                'order_date': item['sales_order__order_date'].strftime('%Y-%m-%d'),
                'delivery_date': item['sales_order__delivery_date'].strftime('%Y-%m-%d') if item['sales_order__delivery_date'] else '',
                'customer_name': item['sales_order__customer__name'],
                'salesperson_name': item['sales_order__salesperson__name'] or 'N/A',
                'product_name': item['product__name'],
                'quantity': float(item['quantity']),
                'unit_price': float(item['unit_price']),
                'line_total': float(item['line_total']),
                'status': item['sales_order__status'],
                'status_display': dict(SalesOrder._meta.get_field('status').choices).get(item['sales_order__status'], item['sales_order__status'])
            }
            for item in items_data
        ]
        
        result = {
            'items': formatted_items,
            'stats': {
                'total_items': stats['total_items'],
                'unique_count': stats['unique_count'],
                'total_quantity': float(stats['total_quantity'] or 0),
                'total_amount': float(stats['total_amount'] or 0),
            }
        }
        
        cache.set(f'task_{task_id}_result', result, timeout=300)
        cache.set(f'task_{task_id}_progress', {
            'state': 'SUCCESS',
            'status': 'Report generated successfully!',
            'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'task_{task_id}_progress', {
            'state': 'FAILURE',
            'status': f'Error: {str(e)}',
            'progress': 0
        }, timeout=300)


@task()
def generate_sales_order_summary_report(task_id, filters, user_id):
    """Background task for Sales Order summary report"""
    try:
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Starting summary generation...',
            'progress': 10
        }, timeout=300)
        
        orders_qs = SalesOrder.objects.select_related('customer', 'salesperson')
        
        if filters.get('from_date'):
            orders_qs = orders_qs.filter(order_date__gte=filters['from_date'])
        if filters.get('to_date'):
            orders_qs = orders_qs.filter(order_date__lte=filters['to_date'])
        if filters.get('customer_id'):
            orders_qs = orders_qs.filter(customer_id=filters['customer_id'])
        if filters.get('salesperson_id'):
            orders_qs = orders_qs.filter(salesperson_id=filters['salesperson_id'])
        if filters.get('status'):
            orders_qs = orders_qs.filter(status=filters['status'])
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Fetching and grouping data...',
            'progress': 30
        }, timeout=300)
        
        limit = filters.get('limit', '50')
        
        orders_data_query = orders_qs.values(
            'id',
            'order_number',
            'order_date',
            'delivery_date',
            'customer__name',
            'salesperson__name',
            'total_amount',
            'status'
        ).annotate(
            item_count=Count('items'),
            total_qty=Sum('items__quantity')
        ).order_by('-order_date', '-order_number')
        
        if limit != 'all':
            try:
                limit_int = int(limit)
                orders_data = list(orders_data_query[:limit_int])
            except (ValueError, TypeError):
                orders_data = list(orders_data_query[:50])
        else:
            orders_data = list(orders_data_query)
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Calculating statistics...',
            'progress': 60
        }, timeout=300)
        
        stats = orders_qs.aggregate(
            total_orders=Count('id'),
            total_amount=Sum('total_amount')
        )
        avg_amount = stats['total_amount'] / stats['total_orders'] if stats['total_orders'] > 0 else 0
        
        formatted_orders = [
            {
                'order_number': order['order_number'],
                'order_date': order['order_date'].strftime('%Y-%m-%d'),
                'delivery_date': order['delivery_date'].strftime('%Y-%m-%d') if order['delivery_date'] else '',
                'customer_name': order['customer__name'],
                'salesperson_name': order['salesperson__name'] or 'N/A',
                'item_count': order['item_count'],
                'total_qty': float(order['total_qty'] or 0),
                'total_amount': float(order['total_amount']),
                'status': order['status'],
                'status_display': dict(SalesOrder._meta.get_field('status').choices).get(order['status'], order['status'])
            }
            for order in orders_data
        ]
        
        result = {
            'orders': formatted_orders,
            'stats': {
                'total_orders': stats['total_orders'],
                'total_amount': float(stats['total_amount'] or 0),
                'avg_amount': float(avg_amount),
            }
        }
        
        cache.set(f'task_{task_id}_result', result, timeout=300)
        cache.set(f'task_{task_id}_progress', {
            'state': 'SUCCESS',
            'status': 'Summary completed!',
            'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'task_{task_id}_progress', {
            'state': 'FAILURE',
            'status': f'Error: {str(e)}',
            'progress': 0
        }, timeout=300)








# ==================== VIEW CLASSES ====================

class SalesOrderDetailReportView(View):
    """Sales Order Detail Report"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Sales Order Detail Report',
            'subtitle': 'Item-level analysis with background processing',
            'status_choices': [
                ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('processing', 'Processing'),
                ('completed', 'Completed'), ('cancelled', 'Cancelled')
            ],
            'filters': {
                'from_date': request.GET.get('from_date', ''),
                'to_date': request.GET.get('to_date', ''),
                'customer': request.GET.get('customer', ''),
                'salesperson': request.GET.get('salesperson', ''),
                'product': request.GET.get('product', ''),
                'status': request.GET.get('status', ''),
            }
        }
        
        return render(request, 'admin/erp/reports/sales_order_detail.html', context)


class SalesOrderSummaryReportView(View):
    """Sales Order Summary Report"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Sales Order Summary Report',
            'subtitle': 'Document-level analysis with background processing',
            'status_choices': [
                ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('processing', 'Processing'),
                ('completed', 'Completed'), ('cancelled', 'Cancelled')
            ],
            'filters': {
                'from_date': request.GET.get('from_date', ''),
                'to_date': request.GET.get('to_date', ''),
                'customer': request.GET.get('customer', ''),
                'salesperson': request.GET.get('salesperson', ''),
                'status': request.GET.get('status', ''),
            },
        }
        
        return render(request, 'admin/erp/reports/sales_order_summary.html', context)


# ==================== API ENDPOINTS ====================

class StartSalesOrderDetailReportTaskView(View):
    """Start Sales Order detail report in background with caching"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        filters = {
            'from_date': request.GET.get('from_date'),
            'to_date': request.GET.get('to_date'),
            'customer_id': request.GET.get('customer'),
            'salesperson_id': request.GET.get('salesperson'),
            'product_id': request.GET.get('product'),
            'status': request.GET.get('status'),
            'limit': request.GET.get('limit', '50'),
        }
        
        cache_key = f"so_detail_{filters['from_date']}_{filters['to_date']}_{filters['customer_id']}_{filters['salesperson_id']}_{filters['product_id']}_{filters['status']}_{filters['limit']}"
        
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({
                'cached': True,
                'task_id': 'cached',
                'data': cached_result
            })
        
        task_id = str(uuid.uuid4())
        generate_sales_order_detail_report.enqueue(task_id, filters, request.user.id)
        
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class StartSalesOrderSummaryReportTaskView(View):
    """Start Sales Order summary report in background with caching"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        filters = {
            'from_date': request.GET.get('from_date'),
            'to_date': request.GET.get('to_date'),
            'customer_id': request.GET.get('customer'),
            'salesperson_id': request.GET.get('salesperson'),
            'status': request.GET.get('status'),
            'limit': request.GET.get('limit', '50'),
        }
        
        cache_key = f"so_summary_{filters['from_date']}_{filters['to_date']}_{filters['customer_id']}_{filters['salesperson_id']}_{filters['status']}_{filters['limit']}"
        
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({
                'cached': True,
                'task_id': 'cached',
                'data': cached_result
            })
        
        task_id = str(uuid.uuid4())
        generate_sales_order_summary_report.enqueue(task_id, filters, request.user.id)
        
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})





