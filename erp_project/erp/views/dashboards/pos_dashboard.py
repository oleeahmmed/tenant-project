"""
POS Dashboard View - Enhanced Branch-Based Point of Sales Analytics
Optimized with Django 6 Tasks for maximum performance with branch-specific features
"""
from django.contrib import admin
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Q, F, Case, When, IntegerField
from django.utils import timezone
from django.core.cache import cache
from django.tasks import task
from datetime import timedelta
from decimal import Decimal
import uuid
from django.db import models

from ...models import (
    QuickSale, QuickSaleItem, Customer, Product, Warehouse, 
    ProductWarehouseStock, StockTransaction, UserProfile
)
from django.contrib.auth.models import User


@task()
def generate_pos_dashboard_data(task_id, date_range, user_id):
    """Enhanced background task for generating branch-specific POS dashboard data"""
    try:
        cache.set(f'pos_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Initializing branch-based analytics...', 'progress': 5
        }, timeout=300)
        
        # Get user and branch information
        user = User.objects.get(id=user_id)
        user_branch = None
        accessible_branches = Warehouse.objects.filter(is_active=True)
        
        try:
            profile = user.profile
            user_branch = profile.branch
            if not user.is_superuser and not profile.can_access_all_branches:
                accessible_branches = profile.get_accessible_branches()
        except UserProfile.DoesNotExist:
            if not user.is_superuser:
                accessible_branches = Warehouse.objects.none()
        
        cache.set(f'pos_dashboard_task_{task_id}_progress', {
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
        
        cache.set(f'pos_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Fetching branch-specific POS data...', 'progress': 20
        }, timeout=300)
        
        # Build branch-filtered querysets
        pos_qs = QuickSale.objects.filter(branch__in=accessible_branches)
        
        if start_date and end_date:
            pos_qs = pos_qs.filter(sale_date__gte=start_date, sale_date__lte=end_date)
        
        cache.set(f'pos_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Calculating branch KPIs...', 'progress': 30
        }, timeout=300)
        
        # Enhanced KPIs with branch breakdown
        total_sales = pos_qs.filter(status='completed').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_transactions = pos_qs.filter(status='completed').count()
        avg_transaction = pos_qs.filter(status='completed').aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')
        total_customers = pos_qs.filter(status='completed').values('customer').distinct().count()
        total_cashiers = pos_qs.filter(status='completed').values('user').distinct().count()
        draft_sales = pos_qs.filter(status='draft').count()
        cancelled_sales = pos_qs.filter(status='cancelled').count()
        total_items_sold = QuickSaleItem.objects.filter(quick_sale__in=pos_qs, quick_sale__status='completed').aggregate(total=Sum('quantity'))['total'] or 0
        
        # Branch-specific metrics
        branch_performance = pos_qs.filter(status='completed').values(
            'branch__name', 'branch__code'
        ).annotate(
            total_sales=Sum('total_amount'),
            transaction_count=Count('id'),
            avg_transaction=Avg('total_amount'),
            unique_customers=Count('customer', distinct=True)
        ).order_by('-total_sales')
        
        # Current stock levels by branch
        stock_levels = ProductWarehouseStock.objects.filter(
            warehouse__in=accessible_branches
        ).values('warehouse__name').annotate(
            total_products=Count('product', distinct=True),
            total_stock_value=Sum(F('quantity') * F('product__purchase_price')),
            low_stock_items=Count(Case(
                When(quantity__lt=F('product__min_stock_level'), then=1),
                output_field=IntegerField()
            ))
        ).order_by('-total_stock_value')
        
        cache.set(f'pos_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Generating enhanced charts...', 'progress': 50
        }, timeout=300)
        
        # Enhanced Sales Trend with branch comparison
        sales_trend_labels = []
        sales_trend_data = []
        branch_trend_data = {}
        days_to_show = 30 if date_range in ['month', 'prev_month', 'all'] else 7
        
        # Initialize branch trend data
        for branch in accessible_branches[:5]:  # Top 5 branches
            branch_trend_data[branch.name] = []
        
        for i in range(days_to_show - 1, -1, -1):
            date = (end_date or today) - timedelta(days=i)
            if start_date and date < start_date:
                continue
            
            # Total sales for the date
            total_sales_date = QuickSale.objects.filter(
                sale_date=date, status='completed', branch__in=accessible_branches
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            sales_trend_labels.append(date.strftime('%d %b'))
            sales_trend_data.append(float(total_sales_date))
            
            # Branch-wise sales for the date
            for branch in accessible_branches[:5]:
                branch_sales = QuickSale.objects.filter(
                    sale_date=date, status='completed', branch=branch
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
                branch_trend_data[branch.name].append(float(branch_sales))
        
        # Top Products with branch breakdown
        top_products = QuickSaleItem.objects.filter(
            quick_sale__in=pos_qs, quick_sale__status='completed'
        ).values('product__name').annotate(
            total_revenue=Sum('line_total'), 
            total_qty=Sum('quantity'),
            branch_count=Count('quick_sale__branch', distinct=True)
        ).order_by('-total_revenue')[:10]
        
        product_names = [p['product__name'] for p in top_products]
        product_revenues = [float(p['total_revenue']) for p in top_products]
        product_quantities = [float(p['total_qty']) for p in top_products]
        product_branch_counts = [p['branch_count'] for p in top_products]
        
        cache.set(f'pos_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Analyzing customer patterns...', 'progress': 70
        }, timeout=300)
        
        # Top Customers with branch analysis
        top_customers = pos_qs.filter(status='completed', customer__isnull=False).values(
            'customer__name'
        ).annotate(
            total=Sum('total_amount'), 
            visit_count=Count('id'),
            branch_count=Count('branch', distinct=True),
            avg_transaction=Avg('total_amount')
        ).order_by('-total')[:10]
        
        customer_names = [c['customer__name'] or 'Walk-in' for c in top_customers]
        customer_revenues = [float(c['total']) for c in top_customers]
        customer_visits = [c['visit_count'] for c in top_customers]
        customer_branch_counts = [c['branch_count'] for c in top_customers]
        
        # Sales by Category with branch insights
        category_sales = QuickSaleItem.objects.filter(
            quick_sale__in=pos_qs, quick_sale__status='completed'
        ).values('product__category__name').annotate(
            total=Sum('line_total'),
            branch_count=Count('quick_sale__branch', distinct=True)
        ).order_by('-total')[:8]
        
        category_names = [c['product__category__name'] or 'Uncategorized' for c in category_sales]
        category_revenues = [float(c['total']) for c in category_sales]
        
        # Enhanced Cashier Performance with branch context
        cashier_performance = pos_qs.filter(status='completed', user__isnull=False).values(
            'user__username', 'user__first_name', 'user__last_name', 'branch__name'
        ).annotate(
            total=Sum('total_amount'), 
            transaction_count=Count('id'),
            avg_transaction=Avg('total_amount')
        ).order_by('-total')[:10]
        
        cashier_names = [f"{c['user__first_name'] or ''} {c['user__last_name'] or ''}".strip() or c['user__username'] for c in cashier_performance]
        cashier_revenues = [float(c['total']) for c in cashier_performance]
        cashier_transactions = [c['transaction_count'] for c in cashier_performance]
        cashier_branches = [c['branch__name'] or 'N/A' for c in cashier_performance]
        
        cache.set(f'pos_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Finalizing branch analytics...', 'progress': 90
        }, timeout=300)
        
        # Hourly Sales Pattern
        hourly_sales = {}
        for hour in range(24):
            hourly_sales[hour] = 0
        
        for sale in pos_qs.filter(status='completed'):
            hour = sale.created_at.hour
            hourly_sales[hour] += float(sale.total_amount)
        
        hourly_labels = [f"{h:02d}:00" for h in range(24)]
        hourly_data = [hourly_sales[h] for h in range(24)]
        
        # Payment Method Distribution
        payment_methods = pos_qs.filter(status='completed').values('payment_method').annotate(
            total=Sum('total_amount'), 
            count=Count('id')
        ).order_by('-total')
        payment_method_names = [dict(QuickSale.PAYMENT_METHOD_CHOICES).get(p['payment_method'], p['payment_method']) for p in payment_methods]
        payment_method_amounts = [float(p['total']) for p in payment_methods]
        
        # Real-time alerts and insights
        alerts = []
        
        # Low stock alerts
        low_stock_count = ProductWarehouseStock.objects.filter(
            warehouse__in=accessible_branches,
            quantity__lt=F('product__min_stock_level')
        ).count()
        if low_stock_count > 0:
            alerts.append({
                'type': 'warning',
                'message': f'{low_stock_count} products are running low on stock',
                'action': 'Check Inventory'
            })
        
        # High performing branch
        if branch_performance:
            top_branch = branch_performance[0]
            alerts.append({
                'type': 'success',
                'message': f'{top_branch["branch__name"]} is your top performing branch with ৳{top_branch["total_sales"]:.2f}',
                'action': 'View Details'
            })
        
        result = {
            'kpis': {
                'total_sales': float(total_sales),
                'total_transactions': total_transactions,
                'avg_transaction': float(avg_transaction),
                'total_customers': total_customers,
                'total_cashiers': total_cashiers,
                'draft_sales': draft_sales,
                'cancelled_sales': cancelled_sales,
                'total_items_sold': int(total_items_sold),
            },
            'branch_metrics': {
                'user_branch': user_branch.name if user_branch else 'All Branches',
                'accessible_branches_count': accessible_branches.count(),
                'branch_performance': list(branch_performance),
                'stock_levels': list(stock_levels),
            },
            'charts': {
                'sales_trend_labels': sales_trend_labels,
                'sales_trend_data': sales_trend_data,
                'branch_trend_data': branch_trend_data,
                'product_names': product_names,
                'product_revenues': product_revenues,
                'product_quantities': product_quantities,
                'product_branch_counts': product_branch_counts,
                'customer_names': customer_names,
                'customer_revenues': customer_revenues,
                'customer_visits': customer_visits,
                'customer_branch_counts': customer_branch_counts,
                'category_names': category_names,
                'category_revenues': category_revenues,
                'cashier_names': cashier_names,
                'cashier_revenues': cashier_revenues,
                'cashier_transactions': cashier_transactions,
                'cashier_branches': cashier_branches,
                'hourly_labels': hourly_labels,
                'hourly_data': hourly_data,
                'payment_method_names': payment_method_names,
                'payment_method_amounts': payment_method_amounts,
            },
            'alerts': alerts,
        }
        
        cache.set(f'pos_dashboard_task_{task_id}_result', result, timeout=300)
        cache.set(f'pos_dashboard_task_{task_id}_progress', {
            'state': 'SUCCESS', 'status': 'Branch-specific dashboard data ready!', 'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'pos_dashboard_task_{task_id}_progress', {
            'state': 'FAILURE', 'status': f'Error: {str(e)}', 'progress': 0
        }, timeout=300)


class POSDashboardView(View):
    """Enhanced POS Dashboard with comprehensive branch-based analytics"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # Get user's branch information
        user_branch = None
        accessible_branches = Warehouse.objects.filter(is_active=True)
        
        try:
            profile = request.user.profile
            user_branch = profile.branch
            if not request.user.is_superuser and not profile.can_access_all_branches:
                accessible_branches = profile.get_accessible_branches()
        except UserProfile.DoesNotExist:
            if not request.user.is_superuser:
                accessible_branches = Warehouse.objects.none()
        
        # Recent Activities (branch-filtered)
        recent_sales = QuickSale.objects.filter(
            branch__in=accessible_branches
        ).select_related('customer', 'user', 'branch').order_by('-created_at')[:10]
        
        # Top selling today (branch-filtered)
        top_selling_today = QuickSaleItem.objects.filter(
            quick_sale__sale_date=timezone.now().date(),
            quick_sale__status='completed',
            quick_sale__branch__in=accessible_branches
        ).values('product__name').annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum('line_total')
        ).order_by('-total_qty')[:10]
        
        # Branch performance summary
        branch_summary = accessible_branches.annotate(
            today_sales=Sum(
                Case(
                    When(
                        quick_sales__sale_date=timezone.now().date(),
                        quick_sales__status='completed',
                        then='quick_sales__total_amount'
                    ),
                    default=0,
                    output_field=models.DecimalField()
                )
            ),
            total_stock_value=Sum(
                F('warehouse_stocks__quantity') * F('warehouse_stocks__product__purchase_price')
            ),
            low_stock_count=Count(
                Case(
                    When(
                        warehouse_stocks__quantity__lt=F('warehouse_stocks__product__min_stock_level'),
                        then=1
                    ),
                    output_field=IntegerField()
                )
            )
        ).order_by('-today_sales')[:5]
        
        # Real-time alerts
        alerts = []
        
        # Low stock alert
        low_stock_count = ProductWarehouseStock.objects.filter(
            warehouse__in=accessible_branches,
            quantity__lt=F('product__min_stock_level')
        ).count()
        
        if low_stock_count > 0:
            alerts.append({
                'type': 'warning',
                'title': 'Low Stock Alert',
                'message': f'{low_stock_count} products are running low on stock',
                'action_url': '/admin/erp/productwarehousestock/?quantity__lt=min_stock_level'
            })
        
        # Draft sales alert
        draft_count = QuickSale.objects.filter(
            branch__in=accessible_branches,
            status='draft'
        ).count()
        
        if draft_count > 0:
            alerts.append({
                'type': 'info',
                'title': 'Pending Sales',
                'message': f'{draft_count} draft sales need to be completed',
                'action_url': '/admin/erp/quicksale/?status=draft'
            })
        
        context = {
            **admin.site.each_context(request),
            'title': 'Enhanced POS Dashboard',
            'subtitle': f'Branch-Based Point of Sales Analytics - {user_branch.name if user_branch else "All Branches"}',
            'recent_sales': recent_sales,
            'top_selling_today': top_selling_today,
            'branch_summary': branch_summary,
            'user_branch': user_branch,
            'accessible_branches_count': accessible_branches.count(),
            'alerts': alerts,
        }
        
        return render(request, 'admin/erp/dashboards/pos_dashboard.html', context)


class StartPOSDashboardDataTaskView(View):
    """API endpoint to start POS dashboard data generation task"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        date_range = request.GET.get('range', 'today')
        
        # Check cache first
        cache_key = f"pos_dashboard_data_{date_range}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        
        # Start background task
        task_id = str(uuid.uuid4())
        generate_pos_dashboard_data.enqueue(task_id, date_range, request.user.id)
        cache.set(f'pos_dashboard_task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckPOSDashboardTaskStatusView(View):
    """API endpoint to check POS dashboard task status"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress_data = cache.get(f'pos_dashboard_task_{task_id}_progress')
        
        if not progress_data:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found', 'progress': 0})
        
        response = {
            'state': progress_data['state'],
            'status': progress_data['status'],
            'progress': progress_data['progress']
        }
        
        if progress_data['state'] == 'SUCCESS':
            result = cache.get(f'pos_dashboard_task_{task_id}_result')
            response['data'] = result
            
            # Cache the result
            cache_key = cache.get(f'pos_dashboard_task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=1800)  # 30 minutes
        
        elif progress_data['state'] == 'FAILURE':
            response['error'] = progress_data['status']
        
        return JsonResponse(response)
