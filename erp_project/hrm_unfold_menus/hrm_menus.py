"""
HRM Module Menu Configuration for Unfold Admin
==============================================

This file contains all menu configurations for the HRM module.
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.apps import apps


def admin_changelist(app_label, model_name):
    """Helper function to generate admin changelist URL"""
    return lambda request: reverse_lazy(f"admin:{app_label}_{model_name}_changelist")


def check_app_and_permission(app_label, model_name):
    """
    Check if app is installed and user has view permission for the model
    Returns a permission check function for menu items
    """
    def permission_check(request):
        # Check if app is installed
        if not apps.is_installed(app_label):
            return False
        
        # Check if user has view permission
        permission = f"{app_label}.view_{model_name.lower()}"
        return request.user.has_perm(permission)
    
    return permission_check


def check_app_installed(app_label):
    """
    Check if app is installed (for dashboard and report links)
    Returns a permission check function for menu items
    """
    def permission_check(request):
        # Check if app is installed
        if not apps.is_installed(app_label):
            return False
        
        # Check if user is staff
        return request.user.is_staff
    
    return permission_check


# ==================== HRM MODULE MENUS ====================
HRM_MENUS = [
    # ==================== HRM SEPARATOR ====================
    {
        "title": _("HRM System"),
        "separator": True,
        "collapsible": True,
        "items": [],
    },
    
    # ==================== EMPLOYEE MANAGEMENT ====================
    {
        "title": _("Employee Management"),
        "icon": "people",
        "collapsible": True,
        "items": [
            {
                "title": _("Employees"),
                "icon": "person",
                "link": admin_changelist("hrm", "employee"),
                "permission": check_app_and_permission("hrm", "employee"),
            },
            {
                "title": _("Personal Info"),
                "icon": "badge",
                "link": admin_changelist("hrm", "employeepersonalinfo"),
                "permission": check_app_and_permission("hrm", "employeepersonalinfo"),
            },
            {
                "title": _("Education"),
                "icon": "school"),
                "link": admin_changelist("hrm", "employeeeducation"),
                "permission": check_app_and_permission("hrm", "employeeeducation"),
            },
            {
                "title": _("Skills"),
                "icon": "psychology",
                "link": admin_changelist("hrm", "employeeskill"),
                "permission": check_app_and_permission("hrm", "employeeskill"),
            },
            {
                "title": _("Salary Info"),
                "icon": "payments",
                "link": admin_changelist("hrm", "employeesalary"),
                "permission": check_app_and_permission("hrm", "employeesalary"),
            },
        ],
    },
    
    # ==================== ORGANIZATION ====================
    {
        "title": _("Organization"),
        "icon": "business",
        "collapsible": True,
        "items": [
            {
                "title": _("Departments"),
                "icon": "corporate_fare",
                "link": admin_changelist("hrm", "department"),
                "permission": check_app_and_permission("hrm", "department"),
            },
            {
                "title": _("Designations"),
                "icon": "work",
                "link": admin_changelist("hrm", "designation"),
                "permission": check_app_and_permission("hrm", "designation"),
            },
            {
                "title": _("Shifts"),
                "icon": "schedule",
                "link": admin_changelist("hrm", "shift"),
                "permission": check_app_and_permission("hrm", "shift"),
            },
        ],
    },
    
    # ==================== DEVICE MANAGEMENT ====================
    {
        "title": _("Device Management"),
        "icon": "devices",
        "collapsible": True,
        "items": [
            {
                "title": _("ZK Devices"),
                "icon": "fingerprint",
                "link": admin_changelist("hrm", "zkdevice"),
                "permission": check_app_and_permission("hrm", "zkdevice"),
            },
            {
                "title": _("Device Users"),
                "icon": "group",
                "link": admin_changelist("hrm", "deviceuser"),
                "permission": check_app_and_permission("hrm", "deviceuser"),
            },
            {
                "title": _("Device Commands"),
                "icon": "terminal",
                "link": admin_changelist("hrm", "devicecommand"),
                "permission": check_app_and_permission("hrm", "devicecommand"),
            },
            {
                "title": _("Device Heartbeat"),
                "icon": "favorite",
                "link": admin_changelist("hrm", "deviceheartbeat"),
                "permission": check_app_and_permission("hrm", "deviceheartbeat"),
            },
        ],
    },
    
    # ==================== ATTENDANCE ====================
    {
        "title": _("Attendance"),
        "icon": "event_available",
        "collapsible": True,
        "items": [
            {
                "title": _("Attendance Logs"),
                "icon": "list_alt",
                "link": admin_changelist("hrm", "attendancelog"),
                "permission": check_app_and_permission("hrm", "attendancelog"),
            },
            {
                "title": _("Attendance Records"),
                "icon": "fact_check",
                "link": admin_changelist("hrm", "attendance"),
                "permission": check_app_and_permission("hrm", "attendance"),
            },
            {
                "title": _("Overtime Records"),
                "icon": "access_time",
                "link": admin_changelist("hrm", "overtime"),
                "permission": check_app_and_permission("hrm", "overtime"),
            },
        ],
    },
    
    # ==================== LEAVE MANAGEMENT ====================
    {
        "title": _("Leave Management"),
        "icon": "beach_access",
        "collapsible": True,
        "items": [
            {
                "title": _("Leave Types"),
                "icon": "category",
                "link": admin_changelist("hrm", "leavetype"),
                "permission": check_app_and_permission("hrm", "leavetype"),
            },
            {
                "title": _("Leave Balances"),
                "icon": "account_balance_wallet",
                "link": admin_changelist("hrm", "leavebalance"),
                "permission": check_app_and_permission("hrm", "leavebalance"),
            },
            {
                "title": _("Leave Applications"),
                "icon": "assignment",
                "link": admin_changelist("hrm", "leaveapplication"),
                "permission": check_app_and_permission("hrm", "leaveapplication"),
            },
        ],
    },
    
    # ==================== REPORTS ====================
    {
        "title": _("HRM Reports"),
        "icon": "assessment",
        "collapsible": True,
        "items": [
            {
                "title": _("Attendance Log Report"),
                "icon": "description",
                "link": lambda request: reverse_lazy("hrm:attendance-log-report"),
                "permission": check_app_installed("hrm"),
            },
            {
                "title": _("Daily Attendance Report"),
                "icon": "today",
                "link": lambda request: reverse_lazy("hrm:daily-attendance-report"),
                "permission": check_app_installed("hrm"),
            },
        ],
    },
    
    # ==================== SETTINGS ====================
    {
        "title": _("HRM Settings"),
        "icon": "settings",
        "collapsible": True,
        "items": [
            {
                "title": _("Holidays"),
                "icon": "celebration",
                "link": admin_changelist("hrm", "holiday"),
                "permission": check_app_and_permission("hrm", "holiday"),
            },
            {
                "title": _("Locations"),
                "icon": "location_on",
                "link": admin_changelist("hrm", "location"),
                "permission": check_app_and_permission("hrm", "location"),
            },
            {
                "title": _("Notices"),
                "icon": "campaign",
                "link": admin_changelist("hrm", "notice"),
                "permission": check_app_and_permission("hrm", "notice"),
            },
        ],
    },
    
    # ==================== GUIDES & HELP ====================
    {
        "title": _("HRM Guides & Help"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Employee Management Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("hrm:employee-management-guide"),
                "permission": check_app_installed("hrm"),
            },
            {
                "title": _("Device Setup Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("hrm:device-setup-guide"),
                "permission": check_app_installed("hrm"),
            },
            {
                "title": _("Attendance Management Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("hrm:attendance-management-guide"),
                "permission": check_app_installed("hrm"),
            },
            {
                "title": _("Leave Management Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("hrm:leave-management-guide"),
                "permission": check_app_installed("hrm"),
            },
            {
                "title": _("Salary & Payroll Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("hrm:salary-payroll-guide"),
                "permission": check_app_installed("hrm"),
            },
        ],
    },
]
