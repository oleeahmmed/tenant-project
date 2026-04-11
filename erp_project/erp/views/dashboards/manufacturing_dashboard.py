"""
Manufacturing Dashboard View - Production & BOM Analytics
Optimized with Django 6 Tasks for maximum performance
Expert-level manufacturing management insights
"""
from django.contrib import admin
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, F, Q, DecimalField
from django.utils import timezone
from django.core.cache import cache
from django.tasks import task
from datetime import timedelta
from decimal import Decimal
import uuid

from ...models import (
    ProductionOrder, ProductionReceipt, ProductionIssue,
    ProductionOrderComponent, ProductionReceiptItem, ProductionIssueItem,
    BillOfMaterials, Product, Category
)


@task()
def generate_manufacturing_dashboard_data(task_id, date_range, user_id):
    """Background task for generating manufacturing dashboard data"""
    try:
        cache.set(f'manufacturing_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Calculating date range...', 'progress': 5
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
        
        cache.set(f'manufacturing_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Analyzing production orders...', 'progress': 15
        }, timeout=300)
        
        # Production Orders
        orders_qs = ProductionOrder.objects.all()
        if start_date and end_date:
            orders_qs = orders_qs.filter(order_date__gte=start_date, order_date__lte=end_date)
        
        total_orders = orders_qs.count()
        completed_orders = orders_qs.filter(status='completed').count()
        in_progress_orders = orders_qs.filter(status='in_progress').count()
        pending_orders = orders_qs.filter(status='draft').count()
        
        # Production quantities
        total_planned_qty = orders_qs.aggregate(total=Sum('quantity_to_produce'))['total'] or 0
        total_produced_qty = orders_qs.filter(status='completed').aggregate(total=Sum('quantity_produced'))['total'] or 0
        
        # Production efficiency (completed vs planned)
        production_efficiency = (float(total_produced_qty) / float(total_planned_qty) * 100) if total_planned_qty > 0 else 0
        
        # BOMs
        total_boms = BillOfMaterials.objects.count()
        active_boms = BillOfMaterials.objects.filter(status='active').count()
        
        cache.set(f'manufacturing_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Calculating material usage...', 'progress': 30
        }, timeout=300)
        
        # Material consumption
        material_issued = ProductionIssue.objects.filter(status='completed')
        if start_date and end_date:
            material_issued = material_issued.filter(issue_date__gte=start_date, issue_date__lte=end_date)
        
        total_material_value = Decimal('0.00')
        for issue in material_issued:
            for item in issue.items.all():
                total_material_value += item.issued_quantity * (item.product.purchase_price or Decimal('0.00'))
        
        cache.set(f'manufacturing_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Generating charts...', 'progress': 50
        }, timeout=300)
        
        # Production Trend
        production_labels = []
        production_data = []
        days_to_show = 30 if date_range in ['month', 'prev_month', 'all'] else 7
        
        for i in range(days_to_show - 1, -1, -1):
            date = (end_date or today) - timedelta(days=i)
            if start_date and date < start_date:
                continue
            qty = ProductionOrder.objects.filter(order_date=date, status='completed').aggregate(total=Sum('quantity_produced'))['total'] or 0
            production_labels.append(date.strftime('%d %b'))
            production_data.append(float(qty))
        
        # Order Status Distribution
        status_labels = ['Draft', 'In Progress', 'Completed', 'Cancelled']
        status_values = [
            orders_qs.filter(status='draft').count(),
            orders_qs.filter(status='in_progress').count(),
            orders_qs.filter(status='completed').count(),
            orders_qs.filter(status='cancelled').count(),
        ]
        
        # Top Produced Products
        top_products = orders_qs.filter(status='completed').values('product__name').annotate(
            total_qty=Sum('quantity_produced')
        ).order_by('-total_qty')[:10]
        
        product_names = [p['product__name'] for p in top_products]
        product_quantities = [float(p['total_qty']) for p in top_products]
        
        cache.set(f'manufacturing_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Analyzing components...', 'progress': 70
        }, timeout=300)
        
        # Material Consumption (Top Components)
        component_usage = ProductionIssueItem.objects.filter(
            production_issue__status='completed'
        )
        if start_date and end_date:
            component_usage = component_usage.filter(
                production_issue__issue_date__gte=start_date,
                production_issue__issue_date__lte=end_date
            )
        
        top_components = component_usage.values('product__name').annotate(
            total_qty=Sum('issued_quantity')
        ).order_by('-total_qty')[:10]
        
        component_names = [c['product__name'] for c in top_components]
        component_quantities = [float(c['total_qty']) for c in top_components]
        
        # Production by Category
        category_production = orders_qs.filter(status='completed').values(
            'product__category__name'
        ).annotate(total_qty=Sum('quantity_produced')).order_by('-total_qty')[:8]
        
        category_names = [c['product__category__name'] or 'Uncategorized' for c in category_production]
        category_quantities = [float(c['total_qty']) for c in category_production]
        
        # Production Receipts
        receipts_qs = ProductionReceipt.objects.all()
        if start_date and end_date:
            receipts_qs = receipts_qs.filter(receipt_date__gte=start_date, receipt_date__lte=end_date)
        
        total_receipts = receipts_qs.count()
        completed_receipts = receipts_qs.filter(status='completed').count()
        
        # Production Issues
        issues_qs = ProductionIssue.objects.all()
        if start_date and end_date:
            issues_qs = issues_qs.filter(issue_date__gte=start_date, issue_date__lte=end_date)
        
        total_issues = issues_qs.count()
        completed_issues = issues_qs.filter(status='completed').count()
        
        cache.set(f'manufacturing_dashboard_task_{task_id}_progress', {
            'state': 'PROCESSING', 'status': 'Finalizing data...', 'progress': 90
        }, timeout=300)
        
        # Efficiency by Product (Top 10)
        efficiency_data = []
        for product in Product.objects.all()[:20]:
            planned = orders_qs.filter(product=product).aggregate(total=Sum('quantity_to_produce'))['total'] or 0
            produced = orders_qs.filter(product=product, status='completed').aggregate(total=Sum('quantity_produced'))['total'] or 0
            if planned > 0:
                efficiency = (float(produced) / float(planned)) * 100
                efficiency_data.append({
                    'name': product.name,
                    'efficiency': efficiency
                })
        
        efficiency_data.sort(key=lambda x: x['efficiency'], reverse=True)
        efficiency_data = efficiency_data[:10]
        efficiency_names = [e['name'] for e in efficiency_data]
        efficiency_values = [e['efficiency'] for e in efficiency_data]
        
        result = {
            'kpis': {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'in_progress_orders': in_progress_orders,
                'pending_orders': pending_orders,
                'total_planned_qty': float(total_planned_qty),
                'total_produced_qty': float(total_produced_qty),
                'production_efficiency': production_efficiency,
                'total_boms': total_boms,
                'active_boms': active_boms,
                'total_material_value': float(total_material_value),
                'total_receipts': total_receipts,
                'total_issues': total_issues,
            },
            'charts': {
                'production_labels': production_labels,
                'production_data': production_data,
                'status_labels': status_labels,
                'status_values': status_values,
                'product_names': product_names,
                'product_quantities': product_quantities,
                'component_names': component_names,
                'component_quantities': component_quantities,
                'category_names': category_names,
                'category_quantities': category_quantities,
                'efficiency_names': efficiency_names,
                'efficiency_values': efficiency_values,
            }
        }
        
        cache.set(f'manufacturing_dashboard_task_{task_id}_result', result, timeout=300)
        cache.set(f'manufacturing_dashboard_task_{task_id}_progress', {
            'state': 'SUCCESS', 'status': 'Dashboard data ready!', 'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'manufacturing_dashboard_task_{task_id}_progress', {
            'state': 'FAILURE', 'status': f'Error: {str(e)}', 'progress': 0
        }, timeout=300)


class ManufacturingDashboardView(View):
    """Manufacturing Dashboard with comprehensive production analytics"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # Recent Activities
        recent_orders = ProductionOrder.objects.select_related('product').order_by('-created_at')[:10]
        recent_receipts = ProductionReceipt.objects.select_related('production_order').order_by('-created_at')[:10]
        
        context = {
            **admin.site.each_context(request),
            'title': 'Manufacturing Dashboard',
            'subtitle': 'Production Orders & BOM Analytics',
            'recent_orders': recent_orders,
            'recent_receipts': recent_receipts,
        }
        
        return render(request, 'admin/erp/dashboards/manufacturing_dashboard.html', context)


class StartManufacturingDashboardDataTaskView(View):
    """API endpoint to start manufacturing dashboard data generation task"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        date_range = request.GET.get('range', 'month')
        
        # Check cache first
        cache_key = f"manufacturing_dashboard_data_{date_range}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        
        # Start background task
        task_id = str(uuid.uuid4())
        generate_manufacturing_dashboard_data.enqueue(task_id, date_range, request.user.id)
        cache.set(f'manufacturing_dashboard_task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckManufacturingDashboardTaskStatusView(View):
    """API endpoint to check manufacturing dashboard task status"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress_data = cache.get(f'manufacturing_dashboard_task_{task_id}_progress')
        
        if not progress_data:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found', 'progress': 0})
        
        response = {
            'state': progress_data['state'],
            'status': progress_data['status'],
            'progress': progress_data['progress']
        }
        
        if progress_data['state'] == 'SUCCESS':
            result = cache.get(f'manufacturing_dashboard_task_{task_id}_result')
            response['data'] = result
            
            # Cache the result
            cache_key = cache.get(f'manufacturing_dashboard_task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=1800)  # 30 minutes
        
        elif progress_data['state'] == 'FAILURE':
            response['error'] = progress_data['status']
        
        return JsonResponse(response)
