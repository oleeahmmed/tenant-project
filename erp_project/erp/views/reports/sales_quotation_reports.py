"""
Sales Quotation Reports - Optimized with Django 6.0 Tasks
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
    SalesQuotation, SalesQuotationItem,
    Customer, SalesPerson, Product
)



@task()
def generate_sales_quotation_detail_report(task_id, filters, user_id):
    """Background task for detail report - Optimized sync version"""
    try:
        cache.set(f'task_{task_id}_progress', {'state': 'PROCESSING', 'status': 'Starting...', 'progress': 10}, timeout=300)
        
        items_qs = SalesQuotationItem.objects.select_related('sales_quotation', 'sales_quotation__customer', 'sales_quotation__salesperson', 'product')
        
        if filters.get('from_date'):
            items_qs = items_qs.filter(sales_quotation__quotation_date__gte=filters['from_date'])
        if filters.get('to_date'):
            items_qs = items_qs.filter(sales_quotation__quotation_date__lte=filters['to_date'])
        if filters.get('customer_id'):
            items_qs = items_qs.filter(sales_quotation__customer_id=filters['customer_id'])
        if filters.get('salesperson_id'):
            items_qs = items_qs.filter(sales_quotation__salesperson_id=filters['salesperson_id'])
        if filters.get('product_id'):
            items_qs = items_qs.filter(product_id=filters['product_id'])
        if filters.get('status'):
            items_qs = items_qs.filter(sales_quotation__status=filters['status'])
        
        cache.set(f'task_{task_id}_progress', {'state': 'PROCESSING', 'status': 'Fetching data...', 'progress': 30}, timeout=300)
        
        limit = filters.get('limit', '50')
        items_data_query = items_qs.values(
            'sales_quotation__quotation_number', 'sales_quotation__quotation_date', 'sales_quotation__valid_until',
            'sales_quotation__customer__name', 'sales_quotation__salesperson__name', 'product__name',
            'quantity', 'unit_price', 'line_total', 'sales_quotation__status'
        ).order_by('-sales_quotation__quotation_date', '-sales_quotation__quotation_number')
        
        if limit != 'all':
            try:
                items_data = list(items_data_query[:int(limit)])
            except (ValueError, TypeError):
                items_data = list(items_data_query[:50])
        else:
            items_data = list(items_data_query)
        
        cache.set(f'task_{task_id}_progress', {'state': 'PROCESSING', 'status': 'Calculating...', 'progress': 60}, timeout=300)
        
        stats = items_qs.aggregate(total_items=Count('id'), total_amount=Sum('line_total'), total_quantity=Sum('quantity'), unique_count=Count('sales_quotation', distinct=True))
        
        formatted_items = [
            {
                'quotation_number': item['sales_quotation__quotation_number'],
                'quotation_date': item['sales_quotation__quotation_date'].strftime('%Y-%m-%d'),
                'valid_until': item['sales_quotation__valid_until'].strftime('%Y-%m-%d') if item['sales_quotation__valid_until'] else '',
                'customer_name': item['sales_quotation__customer__name'],
                'salesperson_name': item['sales_quotation__salesperson__name'] or 'N/A',
                'product_name': item['product__name'],
                'quantity': float(item['quantity']),
                'unit_price': float(item['unit_price']),
                'line_total': float(item['line_total']),
                'status': item['sales_quotation__status'],
                'status_display': dict(SalesQuotation._meta.get_field('status').choices).get(item['sales_quotation__status'], item['sales_quotation__status'])
            }
            for item in items_data
        ]
        
        result = {'items': formatted_items, 'stats': {'total_items': stats['total_items'], 'unique_count': stats['unique_count'], 'total_quantity': float(stats['total_quantity'] or 0), 'total_amount': float(stats['total_amount'] or 0)}}
        
        cache.set(f'task_{task_id}_result', result, timeout=300)
        cache.set(f'task_{task_id}_progress', {'state': 'SUCCESS', 'status': 'Done!', 'progress': 100}, timeout=300)
        
    except Exception as e:
        cache.set(f'task_{task_id}_progress', {'state': 'FAILURE', 'status': f'Error: {str(e)}', 'progress': 0}, timeout=300)


@task()
def generate_sales_quotation_summary_report(task_id, filters, user_id):
    """Background task for summary report - Optimized sync version"""
    try:
        cache.set(f'task_{task_id}_progress', {'state': 'PROCESSING', 'status': 'Starting...', 'progress': 10}, timeout=300)
        
        quotations_qs = SalesQuotation.objects.select_related('customer', 'salesperson')
        
        if filters.get('from_date'):
            quotations_qs = quotations_qs.filter(quotation_date__gte=filters['from_date'])
        if filters.get('to_date'):
            quotations_qs = quotations_qs.filter(quotation_date__lte=filters['to_date'])
        if filters.get('customer_id'):
            quotations_qs = quotations_qs.filter(customer_id=filters['customer_id'])
        if filters.get('salesperson_id'):
            quotations_qs = quotations_qs.filter(salesperson_id=filters['salesperson_id'])
        if filters.get('status'):
            quotations_qs = quotations_qs.filter(status=filters['status'])
        
        cache.set(f'task_{task_id}_progress', {'state': 'PROCESSING', 'status': 'Fetching...', 'progress': 30}, timeout=300)
        
        limit = filters.get('limit', '50')
        quotations_data_query = quotations_qs.values(
            'id', 'quotation_number', 'quotation_date', 'valid_until', 'customer__name', 'salesperson__name', 'total_amount', 'status'
        ).annotate(item_count=Count('items'), total_qty=Sum('items__quantity')).order_by('-quotation_date', '-quotation_number')
        
        if limit != 'all':
            try:
                quotations_data = list(quotations_data_query[:int(limit)])
            except (ValueError, TypeError):
                quotations_data = list(quotations_data_query[:50])
        else:
            quotations_data = list(quotations_data_query)
        
        cache.set(f'task_{task_id}_progress', {'state': 'PROCESSING', 'status': 'Calculating...', 'progress': 60}, timeout=300)
        
        stats = quotations_qs.aggregate(
            total_quotations=Count('id'),
            total_amount=Sum('total_amount')
        )
        avg_amount = stats['total_amount'] / stats['total_quotations'] if stats['total_quotations'] > 0 else 0
        
        formatted_quotations = [
            {
                'quotation_number': quot['quotation_number'],
                'quotation_date': quot['quotation_date'].strftime('%Y-%m-%d'),
                'valid_until': quot['valid_until'].strftime('%Y-%m-%d') if quot['valid_until'] else '',
                'customer_name': quot['customer__name'],
                'salesperson_name': quot['salesperson__name'] or 'N/A',
                'item_count': quot['item_count'],
                'total_qty': float(quot['total_qty'] or 0),
                'total_amount': float(quot['total_amount']),
                'status': quot['status'],
                'status_display': dict(SalesQuotation._meta.get_field('status').choices).get(quot['status'], quot['status'])
            }
            for quot in quotations_data
        ]
        
        result = {'quotations': formatted_quotations, 'stats': {'total_quotations': stats['total_quotations'], 'total_amount': float(stats['total_amount'] or 0), 'avg_amount': float(avg_amount)}}
        
        cache.set(f'task_{task_id}_result', result, timeout=300)
        cache.set(f'task_{task_id}_progress', {'state': 'SUCCESS', 'status': 'Done!', 'progress': 100}, timeout=300)
        
    except Exception as e:
        cache.set(f'task_{task_id}_progress', {'state': 'FAILURE', 'status': f'Error: {str(e)}', 'progress': 0}, timeout=300)








# ==================== VIEW CLASSES ====================

class SalesQuotationDetailReportView(View):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Sales Quotation Detail Report',
            'subtitle': 'Item-level analysis with background processing',
            'status_choices': [('draft', 'Draft'), ('sent', 'Sent'), ('accepted', 'Accepted'), ('converted', 'Converted'), ('rejected', 'Rejected'), ('expired', 'Expired')],
            'filters': {'from_date': request.GET.get('from_date', ''), 'to_date': request.GET.get('to_date', ''), 'customer': request.GET.get('customer', ''), 'salesperson': request.GET.get('salesperson', ''), 'product': request.GET.get('product', ''), 'status': request.GET.get('status', '')}
        }
        return render(request, 'admin/erp/reports/sales_quotation_detail.html', context)


class SalesQuotationSummaryReportView(View):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Sales Quotation Summary Report',
            'subtitle': 'Document-level analysis with background processing',
            'status_choices': [('draft', 'Draft'), ('sent', 'Sent'), ('accepted', 'Accepted'), ('converted', 'Converted'), ('rejected', 'Rejected'), ('expired', 'Expired')],
            'filters': {'from_date': request.GET.get('from_date', ''), 'to_date': request.GET.get('to_date', ''), 'customer': request.GET.get('customer', ''), 'salesperson': request.GET.get('salesperson', ''), 'status': request.GET.get('status', '')}
        }
        return render(request, 'admin/erp/reports/sales_quotation_summary.html', context)


# ==================== API ENDPOINTS ====================

class StartDetailReportTaskView(View):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        filters = {'from_date': request.GET.get('from_date'), 'to_date': request.GET.get('to_date'), 'customer_id': request.GET.get('customer'), 'salesperson_id': request.GET.get('salesperson'), 'product_id': request.GET.get('product'), 'status': request.GET.get('status'), 'limit': request.GET.get('limit', '50')}
        cache_key = f"sq_detail_{filters['from_date']}_{filters['to_date']}_{filters['customer_id']}_{filters['salesperson_id']}_{filters['product_id']}_{filters['status']}_{filters['limit']}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        task_id = str(uuid.uuid4())
        generate_sales_quotation_detail_report.enqueue(task_id, filters, request.user.id)
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class StartSummaryReportTaskView(View):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        filters = {'from_date': request.GET.get('from_date'), 'to_date': request.GET.get('to_date'), 'customer_id': request.GET.get('customer'), 'salesperson_id': request.GET.get('salesperson'), 'status': request.GET.get('status'), 'limit': request.GET.get('limit', '50')}
        cache_key = f"sq_summary_{filters['from_date']}_{filters['to_date']}_{filters['customer_id']}_{filters['salesperson_id']}_{filters['status']}_{filters['limit']}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        task_id = str(uuid.uuid4())
        generate_sales_quotation_summary_report.enqueue(task_id, filters, request.user.id)
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckTaskStatusView(View):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress_data = cache.get(f'task_{task_id}_progress')
        if not progress_data:
            return JsonResponse({'state': 'PENDING', 'status': 'Waiting...', 'progress': 0})
        state = progress_data.get('state', 'PROCESSING')
        if state == 'SUCCESS':
            result = cache.get(f'task_{task_id}_result')
            if result:
                cache_key = cache.get(f'task_{task_id}_cache_key')
                if cache_key:
                    cache.set(cache_key, result, timeout=300)
                if 'file_url' in result:
                    return JsonResponse({'state': state, 'status': progress_data.get('status', 'Completed'), 'progress': 100, 'file_url': result['file_url'], 'filename': result['filename']})
                else:
                    return JsonResponse({'state': state, 'status': progress_data.get('status', 'Completed'), 'progress': 100, 'data': result})
        return JsonResponse({'state': state, 'status': progress_data.get('status', 'Processing...'), 'progress': progress_data.get('progress', 0), 'error': progress_data.get('status') if state == 'FAILURE' else None})




