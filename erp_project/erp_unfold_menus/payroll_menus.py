"""Payroll Unfold Menus"""
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


def get_payroll_menus():
    """Get Payroll menu structure"""
    return [
        {
            "title": _("Payroll"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Salary Structures"),
                    "icon": "account_balance_wallet",
                    "link": admin_changelist("payroll", "salarystructure"),
                    "permission": check_app_and_permission("payroll", "salarystructure"),
                },
                {
                    "title": _("Employee Salaries"),
                    "icon": "person",
                    "link": admin_changelist("payroll", "employeesalary"),
                    "permission": check_app_and_permission("payroll", "employeesalary"),
                },
                {
                    "title": _("Salary Months"),
                    "icon": "calendar_month",
                    "link": admin_changelist("payroll", "salarymonth"),
                    "permission": check_app_and_permission("payroll", "salarymonth"),
                },
                {
                    "title": _("Salary Slips"),
                    "icon": "receipt_long",
                    "link": admin_changelist("payroll", "salaryslip"),
                    "permission": check_app_and_permission("payroll", "salaryslip"),
                },
                {
                    "title": _("Bonuses"),
                    "icon": "card_giftcard",
                    "link": admin_changelist("payroll", "bonus"),
                    "permission": check_app_and_permission("payroll", "bonus"),
                },
                {
                    "title": _("Salary Advances"),
                    "icon": "payments",
                    "link": admin_changelist("payroll", "salaryadvance"),
                    "permission": check_app_and_permission("payroll", "salaryadvance"),
                },
                {
                    "title": _("Loans"),
                    "icon": "account_balance",
                    "link": admin_changelist("payroll", "advanceloan"),
                    "permission": check_app_and_permission("payroll", "advanceloan"),
                },
                {
                    "title": _("Overtime Policies"),
                    "icon": "schedule",
                    "link": admin_changelist("payroll", "overtimepolicy"),
                    "permission": check_app_and_permission("payroll", "overtimepolicy"),
                },
                {
                    "title": _("Deduction Rules"),
                    "icon": "remove_circle",
                    "link": admin_changelist("payroll", "deductionrule"),
                    "permission": check_app_and_permission("payroll", "deductionrule"),
                },
                {
                    "title": _("Tax Slabs"),
                    "icon": "account_balance",
                    "link": admin_changelist("payroll", "taxslab"),
                    "permission": check_app_and_permission("payroll", "taxslab"),
                },
                {
                    "title": _("Payroll Settings"),
                    "icon": "settings",
                    "link": admin_changelist("payroll", "payrollsettings"),
                    "permission": check_app_and_permission("payroll", "payrollsettings"),
                },
            ],
        },
    ]
