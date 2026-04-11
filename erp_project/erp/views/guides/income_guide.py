"""
Income Management Guide View
Shows how to record all types of income in the ERP system
"""
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.decorators import method_decorator


@method_decorator(staff_member_required, name='dispatch')
class IncomeManagementGuideView(TemplateView):
    """
    Income Management Guide - Shows how to record income
    """
    template_name = 'admin/erp/guides/income_management_guide.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ⭐ REQUIRED: Admin context for Unfold sidebar and styling
        context.update(admin.site.each_context(self.request))
        
        # Page title
        context['title'] = 'Income Management Guide'
        
        return context
