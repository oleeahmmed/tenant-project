"""
Financial Dashboard View - Accounting & Finance Analytics
Optimized with Django 6 Tasks for maximum performance
"""
from django.contrib import admin
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.cache import cache
from django.tasks import task
from datetime import timedelta
from decimal import Decimal
import uuid

from ...models import (
    Invoice, InvoiceItem, PurchaseInvoice, PurchaseInvoiceItem,
    IncomingPayment, OutgoingPayment, QuickSale
)


@task()
def generate_financial_dashboard_data(task_id, date_range, user_id):
    """Background task for generating financial dashboard data"""
    try:
        cache.set(f'financial_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Calculating date range...', 'progress': 5
        }, timeout=300)
        
        today = timezone.now().date()
        
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
        else:
            start_date = None
            end_date = None
        
        cache.set(f'financial_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Calculating revenue...', 'progress': 15
        }, timeout=300)
        
        # Revenue (Sales Invoices + POS)
        invoices_qs = Invoice.objects.all()
        if start_date and end_date:
            invoices_qs = invoices_qs.filter(invoice_date__gte=start_date, invoice_date__lte=end_date)
        
        total_revenue = invoices_qs.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # POS Revenue
        pos_qs = QuickSale.objects.all()
        if start_date and end_date:
            pos_qs = pos_qs.filter(sale_date__gte=start_date, sale_date__lte=end_date)
        pos_revenue = pos_qs.filter(status='completed').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        total_revenue += pos_revenue
        
        # Expenses (Purchase Invoices)
        purchase_invoices_qs = PurchaseInvoice.objects.all()
        if start_date and end_date:
            purchase_invoices_qs = purchase_invoices_qs.filter(invoice_date__gte=start_date, invoice_date__lte=end_date)
        
        total_expenses = purchase_invoices_qs.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Net Profit
        net_profit = total_revenue - total_expenses
        profit_margin = (float(net_profit) / float(total_revenue) * 100) if total_revenue > 0 else 0
        
        cache.set(f'financial_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Calculating receivables & payables...', 'progress': 30
        }, timeout=300)
        
        # Accounts Receivable (Outstanding Sales Invoices)
        accounts_receivable = Invoice.objects.filter(
            Q(status='sent') | Q(status='partially_paid')
        ).aggregate(total=Sum('due_amount'))['total'] or Decimal('0.00')
        
        # Accounts Payable (Outstanding Purchase Invoices)
        accounts_payable = PurchaseInvoice.objects.filter(
            Q(status='received') | Q(status='partially_paid')
        ).aggregate(total=Sum('due_amount'))['total'] or Decimal('0.00')
        
        # Cash Balance (Incoming - Outgoing Payments)
        incoming_payments = IncomingPayment.objects.filter(status='completed')
        if start_date and end_date:
            incoming_payments = incoming_payments.filter(payment_date__gte=start_date, payment_date__lte=end_date)
        total_incoming = incoming_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        outgoing_payments = OutgoingPayment.objects.filter(status='completed')
        if start_date and end_date:
            outgoing_payments = outgoing_payments.filter(payment_date__gte=start_date, payment_date__lte=end_date)
        total_outgoing = outgoing_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        cash_balance = total_incoming - total_outgoing
        
        # Outstanding & Overdue
        outstanding_invoices = Invoice.objects.filter(Q(status='sent') | Q(status='partially_paid')).count()
        overdue_invoices = Invoice.objects.filter(
            Q(status='sent') | Q(status='partially_paid'),
            due_date__lt=today
        ).count()
        
        cache.set(f'financial_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Generating charts...', 'progress': 50
        }, timeout=300)
        
        # Revenue vs Expenses Trend
        trend_labels = []
        revenue_data = []
        expense_data = []
        profit_data = []
        days_to_show = 30 if date_range in ['month', 'prev_month', 'all'] else 7
        
        for i in range(days_to_show - 1, -1, -1):
            date = (end_date or today) - timedelta(days=i)
            if start_date and date < start_date:
                continue
            
            rev = Invoice.objects.filter(invoice_date=date, status='paid').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            pos_rev = QuickSale.objects.filter(sale_date=date, status='completed').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            exp = PurchaseInvoice.objects.filter(invoice_date=date, status='paid').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            total_rev = float(rev + pos_rev)
            total_exp = float(exp)
            
            trend_labels.append(date.strftime('%d %b'))
            revenue_data.append(total_rev)
            expense_data.append(total_exp)
            profit_data.append(total_rev - total_exp)
        
        # Payment Status Distribution
        payment_status_labels = ['Paid', 'Partially Paid', 'Unpaid', 'Overdue']
        payment_status_values = [
            Invoice.objects.filter(status='paid').count(),
            Invoice.objects.filter(status='partially_paid').count(),
            Invoice.objects.filter(status='sent').exclude(due_date__lt=today).count(),
            Invoice.objects.filter(status='sent', due_date__lt=today).count(),
        ]
        
        # Revenue by Source
        invoice_revenue = float(invoices_qs.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'))
        pos_revenue_float = float(pos_qs.filter(status='completed').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'))
        
        revenue_source_labels = ['Sales Invoices', 'POS Sales']
        revenue_source_values = [invoice_revenue, pos_revenue_float]
        
        # Cash Flow (Monthly)
        cashflow_labels = []
        cashflow_in = []
        cashflow_out = []
        for i in range(6, -1, -1):
            month_date = today - timedelta(days=i*30)
            month_start = month_date.replace(day=1)
            if month_date.month == 12:
                month_end = month_date.replace(day=31)
            else:
                month_end = (month_date.replace(month=month_date.month+1, day=1) - timedelta(days=1))
            
            incoming = IncomingPayment.objects.filter(
                payment_date__gte=month_start,
                payment_date__lte=month_end,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            outgoing = OutgoingPayment.objects.filter(
                payment_date__gte=month_start,
                payment_date__lte=month_end,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            cashflow_labels.append(month_start.strftime('%b %Y'))
            cashflow_in.append(float(incoming))
            cashflow_out.append(float(outgoing))
        
        cache.set(f'financial_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Finalizing data...', 'progress': 90
        }, timeout=300)
        
        result = {
            'kpis': {
                'total_revenue': float(total_revenue),
                'total_expenses': float(total_expenses),
                'net_profit': float(net_profit),
                'profit_margin': profit_margin,
                'accounts_receivable': float(accounts_receivable),
                'accounts_payable': float(accounts_payable),
                'cash_balance': float(cash_balance),
                'outstanding_invoices': outstanding_invoices,
                'overdue_invoices': overdue_invoices,
            },
            'charts': {
                'trend_labels': trend_labels,
                'revenue_data': revenue_data,
                'expense_data': expense_data,
                'profit_data': profit_data,
                'payment_status_labels': payment_status_labels,
                'payment_status_values': payment_status_values,
                'revenue_source_labels': revenue_source_labels,
                'revenue_source_values': revenue_source_values,
                'cashflow_labels': cashflow_labels,
                'cashflow_in': cashflow_in,
                'cashflow_out': cashflow_out,
            }
        }
        
        cache.set(f'financial_dashboard_task_{task_id}_result', result, timeout=300)
        cache.set(f'financial_dashboard_task_{task_id}_progress', {
            'state': 'SUCCESS', 'status': 'Dashboard data ready!', 'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'financial_dashboard_task_{task_id}_progress', {
            'state': 'FAILURE', 'status': f'Error: {str(e)}', 'progress': 0
        }, timeout=300)


class FinancialDashboardView(View):
    """Financial Dashboard with comprehensive accounting analytics"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # Recent Transactions
        recent_invoices = Invoice.objects.select_related('customer').order_by('-created_at')[:10]
        recent_payments = IncomingPayment.objects.select_related('customer').order_by('-created_at')[:10]
        
        context = {
            **admin.site.each_context(request),
            'title': 'Financial Dashboard',
            'subtitle': 'Accounting & Finance Analytics',
            'recent_invoices': recent_invoices,
            'recent_payments': recent_payments,
        }
        
        return render(request, 'admin/erp/dashboards/financial_dashboard.html', context)


class StartFinancialDashboardDataTaskView(View):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        date_range = request.GET.get('range', 'month')
        cache_key = f"financial_dashboard_data_{date_range}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        
        task_id = str(uuid.uuid4())
        generate_financial_dashboard_data.enqueue(task_id, date_range, request.user.id)
        cache.set(f'financial_dashboard_task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckFinancialDashboardTaskStatusView(View):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress_data = cache.get(f'financial_dashboard_task_{task_id}_progress')
        
        if not progress_data:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found', 'progress': 0})
        
        response = {
            'state': progress_data['state'],
            'status': progress_data['status'],
            'progress': progress_data['progress']
        }
        
        if progress_data['state'] == 'SUCCESS':
            result = cache.get(f'financial_dashboard_task_{task_id}_result')
            response['data'] = result
            
            cache_key = cache.get(f'financial_dashboard_task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=1800)
        
        elif progress_data['state'] == 'FAILURE':
            response['error'] = progress_data['status']
        
        return JsonResponse(response)
