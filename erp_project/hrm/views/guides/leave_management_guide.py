"""
Leave Management Guide View
Shows comprehensive guide for leave management in Bangla
"""
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.decorators import method_decorator


@method_decorator(staff_member_required, name='dispatch')
class LeaveManagementGuideView(TemplateView):
    """
    Leave Management Guide - Shows how to manage employee leaves
    """
    template_name = 'admin/hrm/guides/leave_management_guide.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context['title'] = 'Leave Management Guide'
        return context
