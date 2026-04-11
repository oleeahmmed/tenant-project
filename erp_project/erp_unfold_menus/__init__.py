"""
Unfold Admin Menu Configuration
===============================

This package contains organized menu configurations for the Unfold admin interface.
Each app has its own menu configuration file for better maintainability.

Usage:
    from unfold.erp_menus import ERP_MENUS
    from unfold.hrm_menus import HRM_MENUS
    from unfold.hrm_report_menus import HRM_REPORT_MENUS
    from unfold.garments_menus import GARMENTS_MENUS
    from unfold.payroll_menus import PAYROLL_MENUS
    from unfold.compliance_menus import COMPLIANCE_MENUS
    
    # In settings.py
    UNFOLD = {
        "SIDEBAR": {
            "navigation": [
                *ERP_MENUS,
                *HRM_MENUS,
                *PAYROLL_MENUS,
                *COMPLIANCE_MENUS,
                *HRM_REPORT_MENUS,
                *GARMENTS_MENUS,
            ]
        }
    }
"""

from .erp_menus import ERP_MENUS
from .hrm_menus import HRM_MENUS
from .hrm_report_menus import HRM_REPORT_MENUS
from .garments_menus import GARMENTS_MENUS
from .payroll_menus import get_payroll_menus
from .compliance_menus import get_compliance_menus

# Get dynamic menus
PAYROLL_MENUS = get_payroll_menus()
COMPLIANCE_MENUS = get_compliance_menus()

# Combined navigation for easy import
ALL_MENUS = [
    *ERP_MENUS,
    *HRM_MENUS,
    *PAYROLL_MENUS,
    *COMPLIANCE_MENUS,
    *HRM_REPORT_MENUS,
    *GARMENTS_MENUS,
]

__all__ = ['ERP_MENUS', 'HRM_MENUS', 'PAYROLL_MENUS', 'COMPLIANCE_MENUS', 'HRM_REPORT_MENUS', 'GARMENTS_MENUS', 'ALL_MENUS']