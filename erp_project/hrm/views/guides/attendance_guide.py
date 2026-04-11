"""
Attendance Management Guide View
Shows comprehensive guide for attendance tracking in Bangla
"""
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.decorators import method_decorator


@method_decorator(staff_member_required, name='dispatch')
class AttendanceManagementGuideView(TemplateView):
    """
    Attendance Management Guide - Shows how to track and manage attendance
    """
    template_name = 'admin/hrm/guides/attendance_management_guide.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context['title'] = 'Attendance Management Guide'
        return context
