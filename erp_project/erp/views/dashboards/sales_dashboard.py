"""
Sales Dashboard View - Comprehensive Sales Analytics with Background Tasks
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
    SalesQuotation, SalesOrder, Invoice, InvoiceItem,
    QuickSale, Customer, SalesPerson
)


@task()
def generate_dashboard_data(task_id, date_range, user_id):
    """Background task for generating dashboard data"""
    try:
        cache.set(f'dashboard_task_{task_id}_progress', {
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

        cache.set(f'dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Fetching sales data...', 'progress': 30
        }, timeout=300)
        
        # Build querysets
        invoice_qs = Invoice.objects.all()
        order_qs = SalesOrder.objects.all()
        quotation_qs = SalesQuotation.objects.all()
        pos_qs = QuickSale.objects.all()
        
        if start_date and end_date:
            invoice_qs = invoice_qs.filter(invoice_date__gte=start_date, invoice_date__lte=end_date)
            order_qs = order_qs.filter(order_date__gte=start_date, order_date__lte=end_date)
            quotation_qs = quotation_qs.filter(quotation_date__gte=start_date, quotation_date__lte=end_date)
            pos_qs = pos_qs.filter(sale_date__gte=start_date, sale_date__lte=end_date)
        
        # KPIs
        total_revenue = invoice_qs.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_orders = order_qs.count()
        avg_order_value = invoice_qs.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')
        pending_orders = order_qs.filter(status__in=['draft', 'confirmed']).count()
        active_customers = invoice_qs.values('customer').distinct().count()
        outstanding_receivables = Invoice.objects.filter(status__in=['sent', 'partially_paid', 'overdue']).aggregate(total=Sum('due_amount'))['total'] or Decimal('0.00')
        overdue_invoices = Invoice.objects.filter(status='overdue').count()
        pos_sales = pos_qs.filter(status='completed').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        cache.set(f'dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Generating charts...', 'progress': 60
        }, timeout=300)
        
        # Revenue Trend
        revenue_trend_labels = []
        revenue_trend_data = []
        days_to_show = 30 if date_range in ['month', 'prev_month', 'all'] else 7
        
        for i in range(days_to_show - 1, -1, -1):
            date = (end_date or today) - timedelta(days=i)
            if start_date and date < start_date:
                continue
            revenue = Invoice.objects.filter(invoice_date=date, status='paid').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            revenue_trend_labels.append(date.strftime('%d %b'))
            revenue_trend_data.append(float(revenue))
        
        # Top Products
        top_products = InvoiceItem.objects.filter(invoice__in=invoice_qs, invoice__status='paid').values('product__name').annotate(total_revenue=Sum('line_total')).order_by('-total_revenue')[:10]
        product_names = [p['product__name'] for p in top_products]
        product_revenues = [float(p['total_revenue']) for p in top_products]
        
        # Top Customers
        top_customers = invoice_qs.filter(status='paid').values('customer__name').annotate(total=Sum('total_amount')).order_by('-total')[:10]
        customer_names = [c['customer__name'] or 'Walk-in' for c in top_customers]
        customer_revenues = [float(c['total']) for c in top_customers]
        
        # Sales by Category
        category_sales = InvoiceItem.objects.filter(invoice__in=invoice_qs, invoice__status='paid').values('product__category__name').annotate(total=Sum('line_total')).order_by('-total')[:8]
        category_names = [c['product__category__name'] or 'Uncategorized' for c in category_sales]
        category_revenues = [float(c['total']) for c in category_sales]
        
        # Order Status
        order_status_values = [
            order_qs.filter(status='draft').count(),
            order_qs.filter(status='confirmed').count(),
            order_qs.filter(status='processing').count(),
            order_qs.filter(status='completed').count(),
            order_qs.filter(status='cancelled').count(),
        ]
        
        # Invoice Status
        invoice_status_values = [
            invoice_qs.filter(status='draft').count(),
            invoice_qs.filter(status='sent').count(),
            invoice_qs.filter(status='paid').count(),
            invoice_qs.filter(status='partially_paid').count(),
            invoice_qs.filter(status='overdue').count(),
            invoice_qs.filter(status='cancelled').count(),
        ]
        
        # Salesperson Performance
        salesperson_performance = invoice_qs.filter(status='paid', salesperson__isnull=False).values('salesperson__name').annotate(total=Sum('total_amount')).order_by('-total')[:10]
        salesperson_names = [s['salesperson__name'] for s in salesperson_performance]
        salesperson_revenues = [float(s['total']) for s in salesperson_performance]
        
        cache.set(f'dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Finalizing data...', 'progress': 90
        }, timeout=300)
        
        result = {
            'kpis': {
                'total_revenue': float(total_revenue),
                'total_orders': total_orders,
                'avg_order_value': float(avg_order_value),
                'pending_orders': pending_orders,
                'active_customers': active_customers,
                'outstanding_receivables': float(outstanding_receivables),
                'overdue_invoices': overdue_invoices,
                'pos_sales': float(pos_sales),
            },
            'charts': {
                'revenue_trend_labels': revenue_trend_labels,
                'revenue_trend_data': revenue_trend_data,
                'product_names': product_names,
                'product_revenues': product_revenues,
                'customer_names': customer_names,
                'customer_revenues': customer_revenues,
                'category_names': category_names,
                'category_revenues': category_revenues,
                'order_status_values': order_status_values,
                'invoice_status_values': invoice_status_values,
                'salesperson_names': salesperson_names,
                'salesperson_revenues': salesperson_revenues,
            }
        }
        
        cache.set(f'dashboard_task_{task_id}_result', result, timeout=300)
        cache.set(f'dashboard_task_{task_id}_progress', {
            'state': 'SUCCESS', 'status': 'Dashboard data ready!', 'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'dashboard_task_{task_id}_progress', {
            'state': 'FAILURE', 'status': f'Error: {str(e)}', 'progress': 0
        }, timeout=300)


class SalesDashboardView(View):
    """Sales Dashboard with comprehensive analytics"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # Recent Activities (not affected by date range)
        recent_orders = SalesOrder.objects.select_related('customer', 'salesperson').order_by('-created_at')[:10]
        recent_invoices = Invoice.objects.select_related('customer', 'salesperson').order_by('-created_at')[:10]
        overdue_invoices_list = Invoice.objects.filter(status='overdue').select_related('customer').order_by('due_date')[:10]
        
        context = {
            **admin.site.each_context(request),
            'title': 'Sales Dashboard',
            'subtitle': 'Comprehensive Sales Analytics & Performance Metrics',
            'recent_orders': recent_orders,
            'recent_invoices': recent_invoices,
            'overdue_invoices_list': overdue_invoices_list,
        }
        
        return render(request, 'admin/erp/dashboards/sales_dashboard.html', context)


class StartDashboardDataTaskView(View):
    """API endpoint to start dashboard data generation task"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        date_range = request.GET.get('range', 'month')
        
        # Check cache first
        cache_key = f"dashboard_data_{date_range}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        
        # Start background task
        task_id = str(uuid.uuid4())
        generate_dashboard_data.enqueue(task_id, date_range, request.user.id)
        cache.set(f'dashboard_task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckDashboardTaskStatusView(View):
    """API endpoint to check dashboard task status"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress_data = cache.get(f'dashboard_task_{task_id}_progress')
        
        if not progress_data:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found', 'progress': 0})
        
        response = {
            'state': progress_data['state'],
            'status': progress_data['status'],
            'progress': progress_data['progress']
        }
        
        if progress_data['state'] == 'SUCCESS':
            result = cache.get(f'dashboard_task_{task_id}_result')
            response['data'] = result
            
            # Cache the result
            cache_key = cache.get(f'dashboard_task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=1800)  # 30 minutes
        
        elif progress_data['state'] == 'FAILURE':
            response['error'] = progress_data['status']
        
        return JsonResponse(response)
