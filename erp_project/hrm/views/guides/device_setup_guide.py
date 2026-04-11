"""
Device Setup Guide View
Shows comprehensive guide for device setup and management in Bangla
"""
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.decorators import method_decorator


@method_decorator(staff_member_required, name='dispatch')
class DeviceSetupGuideView(TemplateView):
    """
    Device Setup Guide - Shows how to setup and manage attendance devices
    """
    template_name = 'admin/hrm/guides/device_setup_guide.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context['title'] = 'Device Setup & Management Guide'
        return context
