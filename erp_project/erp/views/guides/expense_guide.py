"""
Expense Management Guide View
Shows how to record all types of expenses in the ERP system
"""
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.decorators import method_decorator


@method_decorator(staff_member_required, name='dispatch')
class ExpenseManagementGuideView(TemplateView):
    """
    Expense Management Guide - Shows how to record expenses
    """
    template_name = 'admin/erp/guides/expense_management_guide.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ⭐ REQUIRED: Admin context for Unfold sidebar and styling
        context.update(admin.site.each_context(self.request))
        
        # Page title
        context['title'] = 'Expense Management Guide'
        
        return context
