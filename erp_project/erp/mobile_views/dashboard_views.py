"""
ERP Mobile Dashboard Views
"""
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from datetime import date, timedelta


class ERPMobileDashboardView(LoginRequiredMixin, View):
    """ERP Mobile Dashboard"""
    template_name = 'erp/mobile_app/dashboard.html'
    login_url = 'erp:erp-mobile-login'
    
    def get(self, request):
        from erp.models import (
            Product, SalesOrder, PurchaseOrder, 
            Warehouse
        )
        
        today = date.today()
        month_start = today.replace(day=1)
        
        # Stats
        total_products = Product.objects.filter(is_active=True).count()
        total_warehouses = Warehouse.objects.filter(is_active=True).count()
        
        # Sales stats
        month_sales = SalesOrder.objects.filter(
            order_date__gte=month_start,
            order_date__lte=today
        ).aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )
        
        # Purchase stats
        month_purchases = PurchaseOrder.objects.filter(
            order_date__gte=month_start,
            order_date__lte=today
        ).aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )
        
        # Expense stats - temporarily set to 0
        month_expenses = {'total': 0}
        
        # Recent orders
        recent_sales = SalesOrder.objects.all().order_by('-created_at')[:5]
        recent_purchases = PurchaseOrder.objects.all().order_by('-created_at')[:5]
        
        context = {
            'total_products': total_products,
            'total_warehouses': total_warehouses,
            'month_sales_total': month_sales['total'] or 0,
            'month_sales_count': month_sales['count'] or 0,
            'month_purchases_total': month_purchases['total'] or 0,
            'month_purchases_count': month_purchases['count'] or 0,
            'month_expenses_total': month_expenses['total'] or 0,
            'recent_sales': recent_sales,
            'recent_purchases': recent_purchases,
        }
        
        return render(request, self.template_name, context)


class ERPMobileMoreView(LoginRequiredMixin, View):
    """ERP Mobile More/Settings"""
    template_name = 'erp/mobile_app/more.html'
    login_url = 'erp:erp-mobile-login'
    
    def get(self, request):
        return render(request, self.template_name)
