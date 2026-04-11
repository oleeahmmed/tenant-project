"""
Purchase Dashboard View - Comprehensive Purchase Analytics with Background Tasks
Optimized with Django 6 Tasks for maximum performance
"""
from django.contrib import admin
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from django.core.cache import cache
from django.tasks import task
from datetime import timedelta
from decimal import Decimal
import uuid

from ...models import (
    PurchaseQuotation, PurchaseOrder, PurchaseOrderItem, GoodsReceiptPO, 
    PurchaseInvoice, PurchaseInvoiceItem, PurchaseReturn, OutgoingPayment, 
    Supplier, Product
)


@task()
def generate_purchase_dashboard_data(task_id, date_range, user_id):
    """Background task for generating purchase dashboard data"""
    try:
        cache.set(f'purchase_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Calculating date range...', 'progress': 10
        }, timeout=300)
        
        today = timezone.now().date()
        
        # Calculate date range
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
        
        cache.set(f'purchase_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Fetching purchase data...', 'progress': 30
        }, timeout=300)
        
        # Build querysets
        invoice_qs = PurchaseInvoice.objects.all()
        order_qs = PurchaseOrder.objects.all()
        quotation_qs = PurchaseQuotation.objects.all()
        receipt_qs = GoodsReceiptPO.objects.all()
        
        if start_date and end_date:
            invoice_qs = invoice_qs.filter(invoice_date__gte=start_date, invoice_date__lte=end_date)
            order_qs = order_qs.filter(order_date__gte=start_date, order_date__lte=end_date)
            quotation_qs = quotation_qs.filter(quotation_date__gte=start_date, quotation_date__lte=end_date)
            receipt_qs = receipt_qs.filter(receipt_date__gte=start_date, receipt_date__lte=end_date)
        
        # KPIs - Use both Orders and Invoices
        # Total from invoices
        total_from_invoices = invoice_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        # Total from orders (if no invoice)
        total_from_orders = order_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_purchases = total_from_invoices + total_from_orders
        
        total_orders = order_qs.count()
        avg_order_value = order_qs.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')
        pending_orders = order_qs.filter(status__in=['draft', 'sent']).count()
        active_suppliers = order_qs.values('supplier').distinct().count()
        outstanding_payables = PurchaseInvoice.objects.filter(status__in=['received', 'partially_paid', 'overdue']).aggregate(total=Sum('due_amount'))['total'] or Decimal('0.00')
        overdue_invoices = PurchaseInvoice.objects.filter(status='overdue').count()
        total_receipts = receipt_qs.count()
        
        cache.set(f'purchase_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Generating charts...', 'progress': 60
        }, timeout=300)
        
        # Purchase Trend - Use Orders
        purchase_trend_labels = []
        purchase_trend_data = []
        days_to_show = 30 if date_range in ['month', 'prev_month', 'all'] else 7
        
        for i in range(days_to_show - 1, -1, -1):
            date = (end_date or today) - timedelta(days=i)
            if start_date and date < start_date:
                continue
            # Use orders for trend
            purchases = PurchaseOrder.objects.filter(order_date=date).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            purchase_trend_labels.append(date.strftime('%d %b'))
            purchase_trend_data.append(float(purchases))
        
        # Top Products from Orders
        from ...models import PurchaseOrderItem
        top_products = PurchaseOrderItem.objects.filter(purchase_order__in=order_qs).values('product__name').annotate(total_cost=Sum('line_total'), total_qty=Sum('quantity')).order_by('-total_cost')[:10]
        product_names = [p['product__name'] for p in top_products]
        product_costs = [float(p['total_cost']) for p in top_products]
        
        # Top Suppliers from Orders
        top_suppliers = order_qs.values('supplier__name').annotate(total=Sum('total_amount')).order_by('-total')[:10]
        supplier_names = [s['supplier__name'] or 'Unknown' for s in top_suppliers]
        supplier_costs = [float(s['total']) for s in top_suppliers]
        
        # Purchase by Category from Orders
        category_purchases = PurchaseOrderItem.objects.filter(purchase_order__in=order_qs).values('product__category__name').annotate(total=Sum('line_total')).order_by('-total')[:8]
        category_names = [c['product__category__name'] or 'Uncategorized' for c in category_purchases]
        category_costs = [float(c['total']) for c in category_purchases]
        
        # Order Status
        order_status_values = [
            order_qs.filter(status='draft').count(),
            order_qs.filter(status='sent').count(),
            order_qs.filter(status='confirmed').count(),
            order_qs.filter(status='received').count(),
            order_qs.filter(status='cancelled').count(),
        ]
        
        # Invoice Status
        invoice_status_values = [
            invoice_qs.filter(status='draft').count(),
            invoice_qs.filter(status='received').count(),
            invoice_qs.filter(status='paid').count(),
            invoice_qs.filter(status='partially_paid').count(),
            invoice_qs.filter(status='overdue').count(),
            invoice_qs.filter(status='cancelled').count(),
        ]
        
        cache.set(f'purchase_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Finalizing data...', 'progress': 90
        }, timeout=300)
        
        result = {
            'kpis': {
                'total_purchases': float(total_purchases),
                'total_orders': total_orders,
                'avg_order_value': float(avg_order_value),
                'pending_orders': pending_orders,
                'active_suppliers': active_suppliers,
                'outstanding_payables': float(outstanding_payables),
                'overdue_invoices': overdue_invoices,
                'total_receipts': total_receipts,
            },
            'charts': {
                'purchase_trend_labels': purchase_trend_labels,
                'purchase_trend_data': purchase_trend_data,
                'product_names': product_names,
                'product_costs': product_costs,
                'supplier_names': supplier_names,
                'supplier_costs': supplier_costs,
                'category_names': category_names,
                'category_costs': category_costs,
                'order_status_values': order_status_values,
                'invoice_status_values': invoice_status_values,
            }
        }
        
        cache.set(f'purchase_dashboard_task_{task_id}_result', result, timeout=300)
        cache.set(f'purchase_dashboard_task_{task_id}_progress', {
            'state': 'SUCCESS', 'status': 'Dashboard data ready!', 'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'purchase_dashboard_task_{task_id}_progress', {
            'state': 'FAILURE', 'status': f'Error: {str(e)}', 'progress': 0
        }, timeout=300)


class PurchaseDashboardView(View):
    """Purchase Dashboard with comprehensive analytics"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # Recent Activities
        recent_orders = PurchaseOrder.objects.select_related('supplier').order_by('-created_at')[:10]
        recent_invoices = PurchaseInvoice.objects.select_related('supplier').order_by('-created_at')[:10]
        overdue_invoices_list = PurchaseInvoice.objects.filter(status='overdue').select_related('supplier').order_by('due_date')[:10]
        
        context = {
            **admin.site.each_context(request),
            'title': 'Purchase Dashboard',
            'subtitle': 'Comprehensive Purchase Analytics & Performance Metrics',
            'recent_orders': recent_orders,
            'recent_invoices': recent_invoices,
            'overdue_invoices_list': overdue_invoices_list,
        }
        
        return render(request, 'admin/erp/dashboards/purchase_dashboard.html', context)


class StartPurchaseDashboardDataTaskView(View):
    """API endpoint to start purchase dashboard data generation task"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        date_range = request.GET.get('range', 'month')
        
        # Check cache first
        cache_key = f"purchase_dashboard_data_{date_range}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        
        # Start background task
        task_id = str(uuid.uuid4())
        generate_purchase_dashboard_data.enqueue(task_id, date_range, request.user.id)
        cache.set(f'purchase_dashboard_task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckPurchaseDashboardTaskStatusView(View):
    """API endpoint to check purchase dashboard task status"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress_data = cache.get(f'purchase_dashboard_task_{task_id}_progress')
        
        if not progress_data:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found', 'progress': 0})
        
        response = {
            'state': progress_data['state'],
            'status': progress_data['status'],
            'progress': progress_data['progress']
        }
        
        if progress_data['state'] == 'SUCCESS':
            result = cache.get(f'purchase_dashboard_task_{task_id}_result')
            response['data'] = result
            
            # Cache the result
            cache_key = cache.get(f'purchase_dashboard_task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=1800)  # 30 minutes
        
        elif progress_data['state'] == 'FAILURE':
            response['error'] = progress_data['status']
        
        return JsonResponse(response)
