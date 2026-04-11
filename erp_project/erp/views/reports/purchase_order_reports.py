"""
Purchase Order Reports with Django 6.0 Built-in Tasks
Optimized Purchase Order Reports: Detail & Summary
- Sync operations with list() and aggregate()
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
from django.db.models import Sum, Count
from django.tasks import task
from decimal import Decimal
from datetime import datetime
import uuid
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side

from ...models import (
    PurchaseOrder, PurchaseOrderItem,
    Supplier, Product
)


# ==================== BACKGROUND TASK FUNCTIONS ====================

@task()
def generate_purchase_order_detail_report(task_id, filters, user_id):
    """Background task for Purchase Order detail report generation"""
    try:
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Starting report generation...',
            'progress': 10
        }, timeout=300)
        
        items_qs = PurchaseOrderItem.objects.select_related(
            'purchase_order', 'purchase_order__supplier', 'product'
        )
        
        if filters.get('from_date'):
            items_qs = items_qs.filter(purchase_order__order_date__gte=filters['from_date'])
        if filters.get('to_date'):
            items_qs = items_qs.filter(purchase_order__order_date__lte=filters['to_date'])
        if filters.get('supplier_id'):
            items_qs = items_qs.filter(purchase_order__supplier_id=filters['supplier_id'])
        if filters.get('product_id'):
            items_qs = items_qs.filter(product_id=filters['product_id'])
        if filters.get('status'):
            items_qs = items_qs.filter(purchase_order__status=filters['status'])
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Fetching data from database...',
            'progress': 30
        }, timeout=300)
        
        limit = filters.get('limit', '50')
        
        items_data_query = items_qs.values(
            'purchase_order__order_number',
            'purchase_order__order_date',
            'purchase_order__supplier__name',
            'product__name',
            'quantity',
            'unit_price',
            'line_total',
            'purchase_order__status'
        ).order_by('-purchase_order__order_date', '-purchase_order__order_number')
        
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
            unique_count=Count('purchase_order', distinct=True)
        )
        
        formatted_items = [
            {
                'order_number': item['purchase_order__order_number'],
                'order_date': item['purchase_order__order_date'].strftime('%Y-%m-%d') if item['purchase_order__order_date'] else '',
                'supplier_name': item['purchase_order__supplier__name'] or 'N/A',
                'product_name': item['product__name'],
                'quantity': float(item['quantity']),
                'unit_price': float(item['unit_price']),
                'line_total': float(item['line_total']),
                'status': item['purchase_order__status'],
                'status_display': dict(PurchaseOrder._meta.get_field('status').choices).get(item['purchase_order__status'], item['purchase_order__status'])
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
def generate_purchase_order_summary_report(task_id, filters, user_id):
    """Background task for Purchase Order summary report"""
    try:
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Starting summary generation...',
            'progress': 10
        }, timeout=300)
        
        orders_qs = PurchaseOrder.objects.select_related('supplier')
        
        if filters.get('from_date'):
            orders_qs = orders_qs.filter(order_date__gte=filters['from_date'])
        if filters.get('to_date'):
            orders_qs = orders_qs.filter(order_date__lte=filters['to_date'])
        if filters.get('supplier_id'):
            orders_qs = orders_qs.filter(supplier_id=filters['supplier_id'])
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
            'supplier__name',
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
                'order_date': order['order_date'].strftime('%Y-%m-%d') if order['order_date'] else '',
                'supplier_name': order['supplier__name'] or 'N/A',
                'item_count': order['item_count'],
                'total_qty': float(order['total_qty'] or 0),
                'total_amount': float(order['total_amount']),
                'status': order['status'],
                'status_display': dict(PurchaseOrder._meta.get_field('status').choices).get(order['status'], order['status'])
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

class PurchaseOrderDetailReportView(View):
    """Purchase Order Detail Report"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Purchase Order Detail Report',
            'subtitle': 'Item-level analysis with background processing',
            'status_choices': [
                ('draft', 'Draft'), ('sent', 'Sent'), ('confirmed', 'Confirmed'),
                ('received', 'Received'), ('completed', 'Completed'), ('cancelled', 'Cancelled')
            ],
            'filters': {
                'from_date': request.GET.get('from_date', ''),
                'to_date': request.GET.get('to_date', ''),
                'supplier': request.GET.get('supplier', ''),
                'product': request.GET.get('product', ''),
                'status': request.GET.get('status', ''),
            }
        }
        
        return render(request, 'admin/erp/reports/purchase_order_detail.html', context)


class PurchaseOrderSummaryReportView(View):
    """Purchase Order Summary Report"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Purchase Order Summary Report',
            'subtitle': 'Document-level analysis with background processing',
            'status_choices': [
                ('draft', 'Draft'), ('sent', 'Sent'), ('confirmed', 'Confirmed'),
                ('received', 'Received'), ('completed', 'Completed'), ('cancelled', 'Cancelled')
            ],
            'filters': {
                'from_date': request.GET.get('from_date', ''),
                'to_date': request.GET.get('to_date', ''),
                'supplier': request.GET.get('supplier', ''),
                'status': request.GET.get('status', ''),
            },
        }
        
        return render(request, 'admin/erp/reports/purchase_order_summary.html', context)


# ==================== API ENDPOINTS ====================

class StartPurchaseOrderDetailReportTaskView(View):
    """Start Purchase Order detail report in background with caching"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        filters = {
            'from_date': request.GET.get('from_date'),
            'to_date': request.GET.get('to_date'),
            'supplier_id': request.GET.get('supplier'),
            'product_id': request.GET.get('product'),
            'status': request.GET.get('status'),
            'limit': request.GET.get('limit', '50'),
        }
        
        cache_key = f"po_detail_{filters['from_date']}_{filters['to_date']}_{filters['supplier_id']}_{filters['product_id']}_{filters['status']}_{filters['limit']}"
        
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({
                'cached': True,
                'task_id': 'cached',
                'data': cached_result
            })
        
        task_id = str(uuid.uuid4())
        generate_purchase_order_detail_report.enqueue(task_id, filters, request.user.id)
        
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class StartPurchaseOrderSummaryReportTaskView(View):
    """Start Purchase Order summary report in background with caching"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        filters = {
            'from_date': request.GET.get('from_date'),
            'to_date': request.GET.get('to_date'),
            'supplier_id': request.GET.get('supplier'),
            'status': request.GET.get('status'),
            'limit': request.GET.get('limit', '50'),
        }
        
        cache_key = f"po_summary_{filters['from_date']}_{filters['to_date']}_{filters['supplier_id']}_{filters['status']}_{filters['limit']}"
        
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({
                'cached': True,
                'task_id': 'cached',
                'data': cached_result
            })
        
        task_id = str(uuid.uuid4())
        generate_purchase_order_summary_report.enqueue(task_id, filters, request.user.id)
        
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})
