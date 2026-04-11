"""Compliance Unfold Menus"""
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


def get_compliance_menus():
    """Get Compliance menu structure"""
    return [
        {
            "title": _("Compliance"),
            "separator": True,
            "collapsible": True,
            "items": [
                {
                    "title": _("Provident Fund"),
                    "icon": "savings",
                    "link": admin_changelist("compliance", "providentfund"),
                    "permission": check_app_and_permission("compliance", "providentfund"),
                },
                {
                    "title": _("Gratuity"),
                    "icon": "volunteer_activism",
                    "link": admin_changelist("compliance", "gratuity"),
                    "permission": check_app_and_permission("compliance", "gratuity"),
                },
                {
                    "title": _("Leave Entitlements"),
                    "icon": "event_available",
                    "link": admin_changelist("compliance", "leaveentitlement"),
                    "permission": check_app_and_permission("compliance", "leaveentitlement"),
                },
                {
                    "title": _("Increments"),
                    "icon": "trending_up",
                    "link": admin_changelist("compliance", "increment"),
                    "permission": check_app_and_permission("compliance", "increment"),
                },
                {
                    "title": _("Transfers/Promotions"),
                    "icon": "swap_horiz",
                    "link": admin_changelist("compliance", "transfer"),
                    "permission": check_app_and_permission("compliance", "transfer"),
                },
                {
                    "title": _("Performance Appraisals"),
                    "icon": "star",
                    "link": admin_changelist("compliance", "performanceappraisal"),
                    "permission": check_app_and_permission("compliance", "performanceappraisal"),
                },
                {
                    "title": _("Service Books"),
                    "icon": "menu_book",
                    "link": admin_changelist("compliance", "servicebook"),
                    "permission": check_app_and_permission("compliance", "servicebook"),
                },
                {
                    "title": _("Appointment Letters"),
                    "icon": "description",
                    "link": admin_changelist("compliance", "appointmentletter"),
                    "permission": check_app_and_permission("compliance", "appointmentletter"),
                },
                {
                    "title": _("Resignations"),
                    "icon": "logout",
                    "link": admin_changelist("compliance", "resignation"),
                    "permission": check_app_and_permission("compliance", "resignation"),
                },
                {
                    "title": _("Terminations"),
                    "icon": "cancel",
                    "link": admin_changelist("compliance", "termination"),
                    "permission": check_app_and_permission("compliance", "termination"),
                },
                {
                    "title": _("Warnings"),
                    "icon": "warning",
                    "link": admin_changelist("compliance", "warning"),
                    "permission": check_app_and_permission("compliance", "warning"),
                },
                {
                    "title": _("Trainings"),
                    "icon": "school",
                    "link": admin_changelist("compliance", "training"),
                    "permission": check_app_and_permission("compliance", "training"),
                },
            ],
        },
    ]
