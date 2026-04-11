"""
Dashboard Views Package
Contains all dashboard views for the ERP system
"""
from .dashboard import DashboardView
from .sales_dashboard import SalesDashboardView
from .purchase_dashboard import PurchaseDashboardView
from .pos_dashboard import POSDashboardView
from .user_pos_dashboard import UserPOSDashboardView
from .inventory_dashboard import InventoryDashboardView
from .manufacturing_dashboard import ManufacturingDashboardView
from .financial_dashboard import FinancialDashboardView

__all__ = [
    'DashboardView',
    'SalesDashboardView',
    'PurchaseDashboardView',
    'POSDashboardView',
    'UserPOSDashboardView',
    'InventoryDashboardView',
    'ManufacturingDashboardView',
    'FinancialDashboardView',
]
