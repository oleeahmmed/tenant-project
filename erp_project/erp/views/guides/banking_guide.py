"""
Banking & Payment Management Guide View
Shows comprehensive guide for banking and payment management in Bangla
"""
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.decorators import method_decorator


@method_decorator(staff_member_required, name='dispatch')
class BankingManagementGuideView(TemplateView):
    """
    Banking Management Guide - Shows how to manage banking and payments
    """
    template_name = 'admin/erp/guides/banking_management_guide.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ⭐ REQUIRED: Admin context for Unfold sidebar and styling
        context.update(admin.site.each_context(self.request))
        
        # Page title
        context['title'] = 'Banking & Payment Management Guide'
        
        return context
