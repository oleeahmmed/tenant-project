"""
Salary & Payroll Guide View
Shows comprehensive guide for salary and payroll management in Bangla
"""
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.decorators import method_decorator


@method_decorator(staff_member_required, name='dispatch')
class SalaryPayrollGuideView(TemplateView):
    """
    Salary & Payroll Guide - Shows how to manage salary and payroll
    """
    template_name = 'admin/hrm/guides/salary_payroll_guide.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context['title'] = 'Salary & Payroll Management Guide'
        return context
