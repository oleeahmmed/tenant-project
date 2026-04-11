"""
HRM Module Menu Configuration for Unfold Admin
==============================================

This file contains all menu configurations for the HRM (Human Resource Management) module.
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
    Check if app is installed (for guide links)
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
    # ==================== ORGANIZATION SETUP ====================
    {
        "title": _("Organization Setup"),
        "separator": True,
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
                "title": _("Locations"),
                "icon": "location_on",
                "link": admin_changelist("hrm", "location"),
                "permission": check_app_and_permission("hrm", "location"),
            },
            {
                "title": _("User Locations"),
                "icon": "my_location",
                "link": admin_changelist("hrm", "userlocation"),
                "permission": check_app_and_permission("hrm", "userlocation"),
            },
        ],
    },
    
    # ==================== EMPLOYEE MANAGEMENT ====================
    {
        "title": _("Employee Management"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Employees"),
                "icon": "badge",
                "link": admin_changelist("hrm", "employee"),
                "permission": check_app_and_permission("hrm", "employee"),
                "badge": lambda request: "★",
            },
            {
                "title": _("Personal Info"),
                "icon": "person",
                "link": admin_changelist("hrm", "employeepersonalinfo"),
                "permission": check_app_and_permission("hrm", "employeepersonalinfo"),
            },
            {
                "title": _("Education"),
                "icon": "school",
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
                "title": _("Salaries"),
                "icon": "payments",
                "link": admin_changelist("hrm", "employeesalary"),
                "permission": check_app_and_permission("hrm", "employeesalary"),
            },
        ],
    },
    
    # ==================== SHIFT MANAGEMENT ====================
    {
        "title": _("Shift Management"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Shifts"),
                "icon": "schedule",
                "link": admin_changelist("hrm", "shift"),
                "permission": check_app_and_permission("hrm", "shift"),
            },
            {
                "title": _("Rosters"),
                "icon": "calendar_month",
                "link": admin_changelist("hrm", "roster"),
                "permission": check_app_and_permission("hrm", "roster"),
            },
            {
                "title": _("Roster Assignments"),
                "icon": "assignment_ind",
                "link": admin_changelist("hrm", "rosterassignment"),
                "permission": check_app_and_permission("hrm", "rosterassignment"),
            },
            {
                "title": _("Roster Days"),
                "icon": "event_note",
                "link": admin_changelist("hrm", "rosterday"),
                "permission": check_app_and_permission("hrm", "rosterday"),
            },
        ],
    },
    
    # ==================== ATTENDANCE MANAGEMENT ====================
    {
        "title": _("Attendance Management"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Attendance"),
                "icon": "fact_check",
                "link": admin_changelist("hrm", "attendance"),
                "permission": check_app_and_permission("hrm", "attendance"),
            },
            {
                "title": _("Attendance Logs"),
                "icon": "fingerprint",
                "link": admin_changelist("hrm", "attendancelog"),
                "permission": check_app_and_permission("hrm", "attendancelog"),
                "badge": lambda request: "🔥",
            },
            {
                "title": _("Overtime"),
                "icon": "more_time",
                "link": admin_changelist("hrm", "overtime"),
                "permission": check_app_and_permission("hrm", "overtime"),
            },
        ],
    },
    
    # ==================== LEAVE MANAGEMENT ====================
    {
        "title": _("Leave Management"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Leave Types"),
                "icon": "event_busy",
                "link": admin_changelist("hrm", "leavetype"),
                "permission": check_app_and_permission("hrm", "leavetype"),
            },
            {
                "title": _("Leave Applications"),
                "icon": "pending_actions",
                "link": admin_changelist("hrm", "leaveapplication"),
                "permission": check_app_and_permission("hrm", "leaveapplication"),
            },
            {
                "title": _("Leave Balances"),
                "icon": "account_balance_wallet",
                "link": admin_changelist("hrm", "leavebalance"),
                "permission": check_app_and_permission("hrm", "leavebalance"),
            },
            {
                "title": _("Holidays"),
                "icon": "celebration",
                "link": admin_changelist("hrm", "holiday"),
                "permission": check_app_and_permission("hrm", "holiday"),
            },
        ],
    },
    
    # ==================== DEVICE MANAGEMENT ====================
    {
        "title": _("Device Management"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("ZK Devices"),
                "icon": "devices",
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
                "title": _("Device Heartbeats"),
                "icon": "favorite",
                "link": admin_changelist("hrm", "deviceheartbeat"),
                "permission": check_app_and_permission("hrm", "deviceheartbeat"),
            },
            {
                "title": _("Operation Logs"),
                "icon": "history",
                "link": admin_changelist("hrm", "operationlog"),
                "permission": check_app_and_permission("hrm", "operationlog"),
            },
            {
                "title": _("TCP Sync Logs"),
                "icon": "sync",
                "link": admin_changelist("hrm", "tcpsynclog"),
                "permission": check_app_and_permission("hrm", "tcpsynclog"),
            },
            {
                "title": _("Fingerprint Templates"),
                "icon": "fingerprint",
                "link": admin_changelist("hrm", "fingerprinttemplate"),
                "permission": check_app_and_permission("hrm", "fingerprinttemplate"),
            },
            {
                "title": _("Face Templates"),
                "icon": "face",
                "link": admin_changelist("hrm", "facetemplate"),
                "permission": check_app_and_permission("hrm", "facetemplate"),
            },
        ],
    },
    
    # ==================== NOTICES & COMMUNICATION ====================
    {
        "title": _("Notices & Communication"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Notices"),
                "icon": "campaign",
                "link": admin_changelist("hrm", "notice"),
                "permission": check_app_and_permission("hrm", "notice"),
            },
        ],
    },
    
    # ==================== HRM GUIDES & HELP ====================
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