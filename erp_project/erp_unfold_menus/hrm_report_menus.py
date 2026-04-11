"""
HRM Reports Menu Configuration for Unfold Admin
===============================================

This file contains all report menu configurations for the HRM module.
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.apps import apps


def check_app_installed(app_label):
    """
    Check if app is installed
    Returns a permission check function for menu items
    """
    def permission_check(request):
        # Check if app is installed
        if not apps.is_installed(app_label):
            return False
        
        # Check if user is staff
        return request.user.is_staff
    
    return permission_check


# ==================== HRM REPORTS MENUS ====================
HRM_REPORT_MENUS = [
    {
        "title": _("HRM Reports"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Attendance Log Report"),
                "icon": "assessment",
                "link": lambda request: reverse_lazy("hrm:attendance-log-report"),
                "permission": check_app_installed("hrm"),
            },
            {
                "title": _("Daily Attendance Report"),
                "icon": "summarize",
                "link": lambda request: reverse_lazy("hrm:daily-attendance-report"),
                "permission": check_app_installed("hrm"),
            },
        ],
    },
]
