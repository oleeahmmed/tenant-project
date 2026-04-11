"""
ERP Mobile Expense Views
"""
from .base_crud import MobileListView, MobileDetailView
# from erp.models import Expense


class ExpenseListView(MobileListView):
    # model = Expense
    template_name = 'erp/mobile_app/expense_list.html'
    context_object_name = 'expenses'
    search_fields = ['description', 'category']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Temporarily return empty queryset until Expense model is created
        from django.db.models import QuerySet
        return QuerySet()


class ExpenseDetailView(MobileDetailView):
    # model = Expense
    template_name = 'erp/mobile_app/expense_detail.html'
    context_object_name = 'expense'
    
    def get(self, request, pk):
        # Temporarily return empty response
        from django.shortcuts import render
        return render(request, self.template_name, {'expense': None})
