"""
Purchase Invoice Reports with Django 6.0 Built-in Tasks
Optimized Purchase Invoice Reports: Detail & Summary
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

from ...models import (
    PurchaseInvoice, PurchaseInvoiceItem,
    Supplier, Product
)


# ==================== BACKGROUND TASK FUNCTIONS ====================

@task()
def generate_purchase_invoice_detail_report(task_id, filters, user_id):
    """Background task for Purchase Invoice detail report generation"""
    try:
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Starting report generation...',
            'progress': 10
        }, timeout=300)
        
        items_qs = PurchaseInvoiceItem.objects.select_related(
            'purchase_invoice', 'purchase_invoice__supplier', 'product'
        )
        
        if filters.get('from_date'):
            items_qs = items_qs.filter(purchase_invoice__invoice_date__gte=filters['from_date'])
        if filters.get('to_date'):
            items_qs = items_qs.filter(purchase_invoice__invoice_date__lte=filters['to_date'])
        if filters.get('supplier_id'):
            items_qs = items_qs.filter(purchase_invoice__supplier_id=filters['supplier_id'])
        if filters.get('product_id'):
            items_qs = items_qs.filter(product_id=filters['product_id'])
        if filters.get('status'):
            items_qs = items_qs.filter(purchase_invoice__status=filters['status'])
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Fetching data from database...',
            'progress': 30
        }, timeout=300)
        
        limit = filters.get('limit', '50')
        
        items_data_query = items_qs.values(
            'purchase_invoice__invoice_number',
            'purchase_invoice__invoice_date',
            'purchase_invoice__due_date',
            'purchase_invoice__supplier__name',
            'product__name',
            'quantity',
            'unit_price',
            'line_total',
            'purchase_invoice__status'
        ).order_by('-purchase_invoice__invoice_date', '-purchase_invoice__invoice_number')
        
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
            unique_count=Count('purchase_invoice', distinct=True)
        )
        
        formatted_items = [
            {
                'invoice_number': item['purchase_invoice__invoice_number'],
                'invoice_date': item['purchase_invoice__invoice_date'].strftime('%Y-%m-%d') if item['purchase_invoice__invoice_date'] else '',
                'due_date': item['purchase_invoice__due_date'].strftime('%Y-%m-%d') if item['purchase_invoice__due_date'] else '',
                'supplier_name': item['purchase_invoice__supplier__name'] or 'N/A',
                'product_name': item['product__name'],
                'quantity': float(item['quantity']),
                'unit_price': float(item['unit_price']),
                'line_total': float(item['line_total']),
                'status': item['purchase_invoice__status'],
                'status_display': dict(PurchaseInvoice._meta.get_field('status').choices).get(item['purchase_invoice__status'], item['purchase_invoice__status'])
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
def generate_purchase_invoice_summary_report(task_id, filters, user_id):
    """Background task for Purchase Invoice summary report"""
    try:
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Starting summary generation...',
            'progress': 10
        }, timeout=300)
        
        invoices_qs = PurchaseInvoice.objects.select_related('supplier')
        
        if filters.get('from_date'):
            invoices_qs = invoices_qs.filter(invoice_date__gte=filters['from_date'])
        if filters.get('to_date'):
            invoices_qs = invoices_qs.filter(invoice_date__lte=filters['to_date'])
        if filters.get('supplier_id'):
            invoices_qs = invoices_qs.filter(supplier_id=filters['supplier_id'])
        if filters.get('status'):
            invoices_qs = invoices_qs.filter(status=filters['status'])
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Fetching and grouping data...',
            'progress': 30
        }, timeout=300)
        
        limit = filters.get('limit', '50')
        
        invoices_data_query = invoices_qs.values(
            'id',
            'invoice_number',
            'invoice_date',
            'due_date',
            'supplier__name',
            'total_amount',
            'paid_amount',
            'due_amount',
            'status'
        ).annotate(
            item_count=Count('items'),
            total_qty=Sum('items__quantity')
        ).order_by('-invoice_date', '-invoice_number')
        
        if limit != 'all':
            try:
                limit_int = int(limit)
                invoices_data = list(invoices_data_query[:limit_int])
            except (ValueError, TypeError):
                invoices_data = list(invoices_data_query[:50])
        else:
            invoices_data = list(invoices_data_query)
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Calculating statistics...',
            'progress': 60
        }, timeout=300)
        
        stats = invoices_qs.aggregate(
            total_invoices=Count('id'),
            total_amount=Sum('total_amount'),
            total_paid=Sum('paid_amount'),
            total_due=Sum('due_amount')
        )
        avg_amount = stats['total_amount'] / stats['total_invoices'] if stats['total_invoices'] > 0 else 0
        
        formatted_invoices = [
            {
                'invoice_number': invoice['invoice_number'],
                'invoice_date': invoice['invoice_date'].strftime('%Y-%m-%d') if invoice['invoice_date'] else '',
                'due_date': invoice['due_date'].strftime('%Y-%m-%d') if invoice['due_date'] else '',
                'supplier_name': invoice['supplier__name'] or 'N/A',
                'item_count': invoice['item_count'],
                'total_qty': float(invoice['total_qty'] or 0),
                'total_amount': float(invoice['total_amount']),
                'paid_amount': float(invoice['paid_amount']),
                'due_amount': float(invoice['due_amount']),
                'status': invoice['status'],
                'status_display': dict(PurchaseInvoice._meta.get_field('status').choices).get(invoice['status'], invoice['status'])
            }
            for invoice in invoices_data
        ]
        
        result = {
            'invoices': formatted_invoices,
            'stats': {
                'total_invoices': stats['total_invoices'],
                'total_amount': float(stats['total_amount'] or 0),
                'total_paid': float(stats['total_paid'] or 0),
                'total_due': float(stats['total_due'] or 0),
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

class PurchaseInvoiceDetailReportView(View):
    """Purchase Invoice Detail Report"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Purchase Invoice Detail Report',
            'subtitle': 'Item-level analysis with background processing',
            'status_choices': [
                ('draft', 'Draft'), ('received', 'Received'), ('paid', 'Paid'),
                ('partially_paid', 'Partially Paid'), ('overdue', 'Overdue'), ('cancelled', 'Cancelled')
            ],
            'filters': {
                'from_date': request.GET.get('from_date', ''),
                'to_date': request.GET.get('to_date', ''),
                'supplier': request.GET.get('supplier', ''),
                'product': request.GET.get('product', ''),
                'status': request.GET.get('status', ''),
            }
        }
        
        return render(request, 'admin/erp/reports/purchase_invoice_detail.html', context)


class PurchaseInvoiceSummaryReportView(View):
    """Purchase Invoice Summary Report"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Purchase Invoice Summary Report',
            'subtitle': 'Document-level analysis with background processing',
            'status_choices': [
                ('draft', 'Draft'), ('received', 'Received'), ('paid', 'Paid'),
                ('partially_paid', 'Partially Paid'), ('overdue', 'Overdue'), ('cancelled', 'Cancelled')
            ],
            'filters': {
                'from_date': request.GET.get('from_date', ''),
                'to_date': request.GET.get('to_date', ''),
                'supplier': request.GET.get('supplier', ''),
                'status': request.GET.get('status', ''),
            },
        }
        
        return render(request, 'admin/erp/reports/purchase_invoice_summary.html', context)


# ==================== API ENDPOINTS ====================

class StartPurchaseInvoiceDetailReportTaskView(View):
    """Start Purchase Invoice detail report in background with caching"""
    
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
        
        cache_key = f"pi_detail_{filters['from_date']}_{filters['to_date']}_{filters['supplier_id']}_{filters['product_id']}_{filters['status']}_{filters['limit']}"
        
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({
                'cached': True,
                'task_id': 'cached',
                'data': cached_result
            })
        
        task_id = str(uuid.uuid4())
        generate_purchase_invoice_detail_report.enqueue(task_id, filters, request.user.id)
        
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class StartPurchaseInvoiceSummaryReportTaskView(View):
    """Start Purchase Invoice summary report in background with caching"""
    
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
        
        cache_key = f"pi_summary_{filters['from_date']}_{filters['to_date']}_{filters['supplier_id']}_{filters['status']}_{filters['limit']}"
        
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({
                'cached': True,
                'task_id': 'cached',
                'data': cached_result
            })
        
        task_id = str(uuid.uuid4())
        generate_purchase_invoice_summary_report.enqueue(task_id, filters, request.user.id)
        
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})
