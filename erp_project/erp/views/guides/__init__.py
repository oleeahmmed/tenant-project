"""
Guide Views Package
Contains all guide/help views for the ERP system
"""
from .stock_movement_guide import StockMovementGuideView
from .expense_guide import ExpenseManagementGuideView
from .income_guide import IncomeManagementGuideView
from .inventory_guide import InventoryManagementGuideView
from .production_guide import ProductionManagementGuideView
from .sales_guide import SalesManagementGuideView
from .banking_guide import BankingManagementGuideView
from .quality_service_guide import QualityServiceManagementGuideView

__all__ = [
    'StockMovementGuideView',
    'ExpenseManagementGuideView',
    'IncomeManagementGuideView',
    'InventoryManagementGuideView',
    'ProductionManagementGuideView',
    'SalesManagementGuideView',
    'BankingManagementGuideView',
    'QualityServiceManagementGuideView',
]
