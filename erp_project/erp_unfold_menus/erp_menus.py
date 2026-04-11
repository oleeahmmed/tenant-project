"""
ERP Module Menu Configuration for Unfold Admin
==============================================

This file contains all menu configurations for the ERP module.
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


# ==================== ERP MODULE MENUS ====================
ERP_MENUS = [
    # ==================== DASHBOARD ====================
    {
        "title": _("Dashboard"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Main Dashboard"),
                "icon": "dashboard",
                "link": lambda request: reverse_lazy("erp:dashboard"),
                "permission": check_app_installed("erp"),
            },
            {
                "title": _("Sales Dashboard"),
                "icon": "analytics",
                "link": lambda request: reverse_lazy("erp:sales-dashboard"),
                "permission": check_app_and_permission("erp", "salesorder"),
            },
            {
                "title": _("Purchase Dashboard"),
                "icon": "shopping_cart",
                "link": lambda request: reverse_lazy("erp:purchase-dashboard"),
                "permission": check_app_and_permission("erp", "purchaseorder"),
            },
            {
                "title": _("POS Dashboard"),
                "icon": "point_of_sale",
                "link": lambda request: reverse_lazy("erp:pos-dashboard"),
                "permission": check_app_and_permission("erp", "quicksale"),
            },
            {
                "title": _("Inventory Dashboard"),
                "icon": "inventory_2",
                "link": lambda request: reverse_lazy("erp:inventory-dashboard"),
                "permission": check_app_and_permission("erp", "productwarehousestock"),
            },
            {
                "title": _("Manufacturing Dashboard"),
                "icon": "precision_manufacturing",
                "link": lambda request: reverse_lazy("erp:manufacturing-dashboard"),
                "permission": check_app_and_permission("erp", "productionorder"),
            },
            {
                "title": _("Financial Dashboard"),
                "icon": "account_balance",
                "link": lambda request: reverse_lazy("erp:financial-dashboard"),
                "permission": check_app_and_permission("erp", "journalentry"),
            },
        ],
    },
    
    # ==================== POINT OF SALES ====================
    {
        "title": _("Point of Sales"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Modern POS"),
                "icon": "storefront",
                "link": lambda request: reverse_lazy("erp:modern-pos"),
                "permission": check_app_and_permission("erp", "quicksale"),
                "badge": lambda request: "NEW",
            },
            {
                "title": _("Quick Sales"),
                "icon": "receipt",
                "link": lambda request: reverse_lazy("admin:erp_quicksale_changelist"),
                "permission": check_app_and_permission("erp", "quicksale"),
            },
            {
                "title": _("POS Sessions"),
                "icon": "schedule",
                "link": admin_changelist("erp", "possession"),
                "permission": check_app_and_permission("erp", "possession"),
            },
            {
                "title": _("Shipping Areas"),
                "icon": "local_shipping",
                "link": admin_changelist("erp", "shippingarea"),
                "permission": check_app_and_permission("erp", "shippingarea"),
            },
            {
                "title": _("POS Returns"),
                "icon": "assignment_return",
                "link": admin_changelist("erp", "posreturn"),
                "permission": check_app_and_permission("erp", "posreturn"),
            },
            {
                "title": _("User Profiles"),
                "icon": "person",
                "link": admin_changelist("erp", "userprofile"),
                "permission": check_app_and_permission("erp", "userprofile"),
            },
            {
                "title": _("User POS Dashboard"),
                "icon": "dashboard",
                "link": lambda request: reverse_lazy("erp:user-pos-dashboard"),
                "permission": check_app_and_permission("erp", "quicksale"),
            },
        ],
    },
    
    # ==================== PHASE 1: FOUNDATION & SETUP ====================
    {
        "title": _("Foundation & Setup"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Company"),
                "icon": "business",
                "link": admin_changelist("erp", "company"),
                "permission": check_app_and_permission("erp", "company"),
            },
            {
                "title": _("Warehouses"),
                "icon": "warehouse",
                "link": admin_changelist("erp", "warehouse"),
                "permission": check_app_and_permission("erp", "warehouse"),
            },
            {
                "title": _("Categories"),
                "icon": "category",
                "link": admin_changelist("erp", "category"),
                "permission": check_app_and_permission("erp", "category"),
            },
            {
                "title": _("Products"),
                "icon": "inventory_2",
                "link": admin_changelist("erp", "product"),
                "permission": check_app_and_permission("erp", "product"),
            },
            # Sizes, Colors, and Product Variants removed - managed via inline in Product admin
            {
                "title": _("Units of Measure"),
                "icon": "straighten",
                "link": admin_changelist("erp", "unitofmeasure"),
                "permission": check_app_and_permission("erp", "unitofmeasure"),
            },
            {
                "title": _("UOM Conversions"),
                "icon": "sync_alt",
                "link": admin_changelist("erp", "uomconversion"),
                "permission": check_app_and_permission("erp", "uomconversion"),
            },
            {
                "title": _("Customers"),
                "icon": "people",
                "link": admin_changelist("erp", "customer"),
                "permission": check_app_and_permission("erp", "customer"),
            },
            {
                "title": _("Suppliers"),
                "icon": "local_shipping",
                "link": admin_changelist("erp", "supplier"),
                "permission": check_app_and_permission("erp", "supplier"),
            },
            {
                "title": _("Sales Persons"),
                "icon": "badge",
                "link": admin_changelist("erp", "salesperson"),
                "permission": check_app_and_permission("erp", "salesperson"),
            },
            {
                "title": _("Payment Methods"),
                "icon": "payments",
                "link": admin_changelist("erp", "paymentmethod"),
                "permission": check_app_and_permission("erp", "paymentmethod"),
            },
        ],
    },
    
    # ==================== PHASE 2: FINANCIAL FOUNDATION ====================
    {
        "title": _("Financial Foundation"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Currencies"),
                "icon": "currency_exchange",
                "link": admin_changelist("erp", "currency"),
                "permission": check_app_and_permission("erp", "currency"),
            },
            {
                "title": _("Exchange Rates"),
                "icon": "trending_up",
                "link": admin_changelist("erp", "exchangerate"),
                "permission": check_app_and_permission("erp", "exchangerate"),
            },
            {
                "title": _("Tax Types"),
                "icon": "receipt_long",
                "link": admin_changelist("erp", "taxtype"),
                "permission": check_app_and_permission("erp", "taxtype"),
            },
            {
                "title": _("Tax Rates"),
                "icon": "percent",
                "link": admin_changelist("erp", "taxrate"),
                "permission": check_app_and_permission("erp", "taxrate"),
            },
            {
                "title": _("Payment Terms"),
                "icon": "schedule",
                "link": admin_changelist("erp", "paymentterm"),
                "permission": check_app_and_permission("erp", "paymentterm"),
            },
            {
                "title": _("Price Lists"),
                "icon": "sell",
                "link": admin_changelist("erp", "pricelist"),
                "permission": check_app_and_permission("erp", "pricelist"),
            },
            {
                "title": _("Account Types"),
                "icon": "category",
                "link": admin_changelist("erp", "accounttype"),
                "permission": check_app_and_permission("erp", "accounttype"),
            },
            {
                "title": _("Chart of Accounts"),
                "icon": "account_tree",
                "link": admin_changelist("erp", "chartofaccounts"),
                "permission": check_app_and_permission("erp", "chartofaccounts"),
            },
            {
                "title": _("Cost Centers"),
                "icon": "business_center",
                "link": admin_changelist("erp", "costcenter"),
                "permission": check_app_and_permission("erp", "costcenter"),
            },
            {
                "title": _("Projects"),
                "icon": "work",
                "link": admin_changelist("erp", "project"),
                "permission": check_app_and_permission("erp", "project"),
            },
            {
                "title": _("Fiscal Years"),
                "icon": "calendar_today",
                "link": admin_changelist("erp", "fiscalyear"),
                "permission": check_app_and_permission("erp", "fiscalyear"),
            },
        ],
    },
    
    # ==================== PHASE 3: SALES PROCESS ====================
    {
        "title": _("Sales"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Sales Quotations"),
                "icon": "request_quote",
                "link": admin_changelist("erp", "salesquotation"),
                "permission": check_app_and_permission("erp", "salesquotation"),
            },
            {
                "title": _("Sales Orders"),
                "icon": "shopping_cart",
                "link": admin_changelist("erp", "salesorder"),
                "permission": check_app_and_permission("erp", "salesorder"),
            },
            {
                "title": _("Deliveries"),
                "icon": "local_shipping",
                "link": admin_changelist("erp", "delivery"),
                "permission": check_app_and_permission("erp", "delivery"),
            },
            {
                "title": _("Invoices"),
                "icon": "receipt",
                "link": admin_changelist("erp", "invoice"),
                "permission": check_app_and_permission("erp", "invoice"),
            },
            {
                "title": _("Sales Returns"),
                "icon": "assignment_return",
                "link": admin_changelist("erp", "salesreturn"),
                "permission": check_app_and_permission("erp", "salesreturn"),
            },
        ],
    },
    

    
    # ==================== PHASE 4: PURCHASE PROCESS ====================
    {
        "title": _("Purchase"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Purchase Quotations"),
                "icon": "request_quote",
                "link": admin_changelist("erp", "purchasequotation"),
                "permission": check_app_and_permission("erp", "purchasequotation"),
            },
            {
                "title": _("Purchase Orders"),
                "icon": "shopping_bag",
                "link": admin_changelist("erp", "purchaseorder"),
                "permission": check_app_and_permission("erp", "purchaseorder"),
            },
            {
                "title": _("Goods Receipt (PO)"),
                "icon": "inventory",
                "link": admin_changelist("erp", "goodsreceiptpo"),
                "permission": check_app_and_permission("erp", "goodsreceiptpo"),
            },
            {
                "title": _("Goods Receipt (General)"),
                "icon": "move_to_inbox",
                "link": admin_changelist("erp", "goodsreceipt"),
                "permission": check_app_and_permission("erp", "goodsreceipt"),
            },
            {
                "title": _("Purchase Invoices"),
                "icon": "receipt_long",
                "link": admin_changelist("erp", "purchaseinvoice"),
                "permission": check_app_and_permission("erp", "purchaseinvoice"),
            },
            {
                "title": _("Purchase Returns"),
                "icon": "keyboard_return",
                "link": admin_changelist("erp", "purchasereturn"),
                "permission": check_app_and_permission("erp", "purchasereturn"),
            },
        ],
    },
    
    # ==================== BANKING ====================
    {
        "title": _("Banking"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Bank Accounts"),
                "icon": "account_balance",
                "link": admin_changelist("erp", "bankaccount"),
                "permission": check_app_and_permission("erp", "bankaccount"),
            },
            {
                "title": _("Incoming Payments"),
                "icon": "arrow_downward",
                "link": admin_changelist("erp", "incomingpayment"),
                "permission": check_app_and_permission("erp", "incomingpayment"),
            },
            {
                "title": _("Outgoing Payments"),
                "icon": "arrow_upward",
                "link": admin_changelist("erp", "outgoingpayment"),
                "permission": check_app_and_permission("erp", "outgoingpayment"),
            },
            {
                "title": _("Bank Statements"),
                "icon": "description",
                "link": admin_changelist("erp", "bankstatement"),
                "permission": check_app_and_permission("erp", "bankstatement"),
            },
            {
                "title": _("Bank Reconciliation"),
                "icon": "check_circle",
                "link": admin_changelist("erp", "bankreconciliation"),
                "permission": check_app_and_permission("erp", "bankreconciliation"),
            },
            {
                "title": _("Unreconciled Transactions"),
                "icon": "pending",
                "link": admin_changelist("erp", "unreconciledtransaction"),
                "permission": check_app_and_permission("erp", "unreconciledtransaction"),
            },
        ],
    },
    
    # ==================== PHASE 5: MANUFACTURING ====================
    {
        "title": _("Manufacturing"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Bill of Materials"),
                "icon": "list_alt",
                "link": admin_changelist("erp", "billofmaterials"),
                "permission": check_app_and_permission("erp", "billofmaterials"),
            },
            {
                "title": _("Production Orders"),
                "icon": "precision_manufacturing",
                "link": admin_changelist("erp", "productionorder"),
                "permission": check_app_and_permission("erp", "productionorder"),
            },
            {
                "title": _("Production Issues"),
                "icon": "output",
                "link": admin_changelist("erp", "productionissue"),
                "permission": check_app_and_permission("erp", "productionissue"),
            },
            {
                "title": _("Production Receipts"),
                "icon": "fact_check",
                "link": admin_changelist("erp", "productionreceipt"),
                "permission": check_app_and_permission("erp", "productionreceipt"),
            },
        ],
    },
    
    # ==================== PHASE 6: INVENTORY CONTROL ====================
    {
        "title": _("Inventory"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Stock Adjustments"),
                "icon": "tune",
                "link": admin_changelist("erp", "stockadjustment"),
                "permission": check_app_and_permission("erp", "stockadjustment"),
            },
            {
                "title": _("Goods Issues"),
                "icon": "outbox",
                "link": admin_changelist("erp", "goodsissue"),
                "permission": check_app_and_permission("erp", "goodsissue"),
            },
            {
                "title": _("Inventory Transfers"),
                "icon": "compare_arrows",
                "link": admin_changelist("erp", "inventorytransfer"),
                "permission": check_app_and_permission("erp", "inventorytransfer"),
            },
            {
                "title": _("Warehouse Stock"),
                "icon": "storage",
                "link": admin_changelist("erp", "productwarehousestock"),
                "permission": check_app_and_permission("erp", "productwarehousestock"),
            },
            {
                "title": _("Variant Warehouse Stock"),
                "icon": "inventory",
                "link": admin_changelist("erp", "productvariantwarehousestock"),
                "permission": check_app_and_permission("erp", "productvariantwarehousestock"),
            },
            {
                "title": _("Stock Transactions"),
                "icon": "swap_horiz",
                "link": admin_changelist("erp", "stocktransaction"),
                "permission": check_app_and_permission("erp", "stocktransaction"),
            },
        ],
    },
    
    # ==================== FIXED ASSETS ====================
    {
        "title": _("Fixed Assets"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Asset Categories"),
                "icon": "category",
                "link": admin_changelist("erp", "assetcategory"),
                "permission": check_app_and_permission("erp", "assetcategory"),
            },
            {
                "title": _("Fixed Assets"),
                "icon": "business",
                "link": admin_changelist("erp", "fixedasset"),
                "permission": check_app_and_permission("erp", "fixedasset"),
            },
            {
                "title": _("Asset Depreciation"),
                "icon": "trending_down",
                "link": admin_changelist("erp", "assetdepreciation"),
                "permission": check_app_and_permission("erp", "assetdepreciation"),
            },
            {
                "title": _("Asset Transfers"),
                "icon": "swap_horiz",
                "link": admin_changelist("erp", "assettransfer"),
                "permission": check_app_and_permission("erp", "assettransfer"),
            },
            {
                "title": _("Asset Disposals"),
                "icon": "delete_forever",
                "link": admin_changelist("erp", "assetdisposal"),
                "permission": check_app_and_permission("erp", "assetdisposal"),
            },
            {
                "title": _("Asset Maintenance"),
                "icon": "build",
                "link": admin_changelist("erp", "assetmaintenance"),
                "permission": check_app_and_permission("erp", "assetmaintenance"),
            },
        ],
    },
    
    # ==================== PHASE 7: ACCOUNTING ====================
    {
        "title": _("Accounting"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("💰 Simple Expense Entry"),
                "icon": "receipt_long",
                "link": lambda request: reverse_lazy("erp:simple-expense-entry"),
                "permission": check_app_installed("erp"),
            },
            {
                "title": _("Journal Entries"),
                "icon": "book",
                "link": admin_changelist("erp", "journalentry"),
                "permission": check_app_and_permission("erp", "journalentry"),
            },
            {
                "title": _("Budgets"),
                "icon": "pie_chart",
                "link": admin_changelist("erp", "budget"),
                "permission": check_app_and_permission("erp", "budget"),
            },
            {
                "title": _("Trial Balance"),
                "icon": "balance",
                "link": lambda request: reverse_lazy("erp:trial-balance-report"),
                "permission": check_app_and_permission("erp", "journalentry"),
            },
            {
                "title": _("Profit & Loss"),
                "icon": "trending_up",
                "link": lambda request: reverse_lazy("erp:profit-loss-report"),
                "permission": check_app_and_permission("erp", "journalentry"),
            },
            {
                "title": _("Balance Sheet"),
                "icon": "account_balance_wallet",
                "link": lambda request: reverse_lazy("erp:balance-sheet-report"),
                "permission": check_app_and_permission("erp", "journalentry"),
            },
            {
                "title": _("General Ledger"),
                "icon": "menu_book",
                "link": lambda request: reverse_lazy("erp:general-ledger-report"),
                "permission": check_app_and_permission("erp", "journalentry"),
            },
            {
                "title": _("Account Statement"),
                "icon": "description",
                "link": lambda request: reverse_lazy("erp:account-statement-report"),
                "permission": check_app_and_permission("erp", "journalentry"),
            },
        ],
    },
    
    # ==================== SALES REPORTS ====================
    {
        "title": _("Sales Reports"),
        "separator": True,
        "collapsible": True,
        "icon": "point_of_sale",
        "items": [
            {
                "title": _("Quotations (Detail)"),
                "icon": "request_quote",
                "link": lambda request: reverse_lazy("erp:sales-quotation-detail-report"),
                "permission": check_app_and_permission("erp", "salesquotation"),
            },
            {
                "title": _("Quotations (Summary)"),
                "icon": "summarize",
                "link": lambda request: reverse_lazy("erp:sales-quotation-summary-report"),
                "permission": check_app_and_permission("erp", "salesquotation"),
            },
            {
                "title": _("Orders (Detail)"),
                "icon": "shopping_cart",
                "link": lambda request: reverse_lazy("erp:sales-order-detail-report"),
                "permission": check_app_and_permission("erp", "salesorder"),
            },
            {
                "title": _("Orders (Summary)"),
                "icon": "receipt_long",
                "link": lambda request: reverse_lazy("erp:sales-order-summary-report"),
                "permission": check_app_and_permission("erp", "salesorder"),
            },
            {
                "title": _("POS Sales (Detail)"),
                "icon": "point_of_sale",
                "link": lambda request: reverse_lazy("erp:pos-detail-report"),
                "permission": check_app_and_permission("erp", "quicksale"),
            },
            {
                "title": _("POS Sales (Summary)"),
                "icon": "receipt",
                "link": lambda request: reverse_lazy("erp:pos-summary-report"),
                "permission": check_app_and_permission("erp", "quicksale"),
            },
            {
                "title": _("Sales Invoices (Detail)"),
                "icon": "description",
                "link": lambda request: reverse_lazy("erp:sales-invoice-detail-report"),
                "permission": check_app_and_permission("erp", "invoice"),
            },
            {
                "title": _("Sales Invoices (Summary)"),
                "icon": "receipt_long",
                "link": lambda request: reverse_lazy("erp:sales-invoice-summary-report"),
                "permission": check_app_and_permission("erp", "invoice"),
            },
        ],
    },
    
    # ==================== PURCHASE REPORTS ====================
    {
        "title": _("Purchase Reports"),
        "separator": True,
        "collapsible": True,
        "icon": "shopping_bag",
        "items": [
            {
                "title": _("Purchase Orders (Detail)"),
                "icon": "shopping_cart",
                "link": lambda request: reverse_lazy("erp:purchase-order-detail-report"),
                "permission": check_app_and_permission("erp", "purchaseorder"),
            },
            {
                "title": _("Purchase Orders (Summary)"),
                "icon": "receipt_long",
                "link": lambda request: reverse_lazy("erp:purchase-order-summary-report"),
                "permission": check_app_and_permission("erp", "purchaseorder"),
            },
            {
                "title": _("Purchase Invoices (Detail)"),
                "icon": "description",
                "link": lambda request: reverse_lazy("erp:purchase-invoice-detail-report"),
                "permission": check_app_and_permission("erp", "purchaseinvoice"),
            },
            {
                "title": _("Purchase Invoices (Summary)"),
                "icon": "receipt",
                "link": lambda request: reverse_lazy("erp:purchase-invoice-summary-report"),
                "permission": check_app_and_permission("erp", "purchaseinvoice"),
            },
        ],
    },
    
    # ==================== QUALITY & SERVICE MANAGEMENT ====================
    {
        "title": _("Quality & Service"),
        "separator": True,
        "collapsible": True,
        "items": [
            # Quality Control
            {
                "title": _("Quality Check Types"),
                "icon": "verified",
                "link": admin_changelist("erp", "qualitychecktype"),
                "permission": check_app_and_permission("erp", "qualitychecktype"),
            },
            {
                "title": _("Quality Checks"),
                "icon": "fact_check",
                "link": admin_changelist("erp", "qualitycheck"),
                "permission": check_app_and_permission("erp", "qualitycheck"),
            },
            {
                "title": _("Defect Types"),
                "icon": "bug_report",
                "link": admin_changelist("erp", "defecttype"),
                "permission": check_app_and_permission("erp", "defecttype"),
            },
            {
                "title": _("Quality Defects"),
                "icon": "warning",
                "link": admin_changelist("erp", "qualitydefect"),
                "permission": check_app_and_permission("erp", "qualitydefect"),
            },
            # Service Management
            {
                "title": _("Service Types"),
                "icon": "support_agent",
                "link": admin_changelist("erp", "servicetype"),
                "permission": check_app_and_permission("erp", "servicetype"),
            },
            {
                "title": _("Service Requests"),
                "icon": "support",
                "link": admin_changelist("erp", "servicerequest"),
                "permission": check_app_and_permission("erp", "servicerequest"),
            },
            # Complaint Management
            {
                "title": _("Complaint Types"),
                "icon": "report_problem",
                "link": admin_changelist("erp", "complainttype"),
                "permission": check_app_and_permission("erp", "complainttype"),
            },
            {
                "title": _("Complaints"),
                "icon": "report",
                "link": admin_changelist("erp", "complaint"),
                "permission": check_app_and_permission("erp", "complaint"),
            },
        ],
    },
    
    # ==================== AUTHENTICATION ====================
    {
        "title": _("Authentication & Authorization"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Users"),
                "icon": "person",
                "link": lambda request: reverse_lazy("admin:auth_user_changelist"),
                "permission": lambda request: request.user.has_perm("auth.view_user"),
            },
            {
                "title": _("Groups"),
                "icon": "group",
                "link": lambda request: reverse_lazy("admin:auth_group_changelist"),
                "permission": lambda request: request.user.has_perm("auth.view_group"),
            },
            {
                "title": _("Permissions"),
                "icon": "lock",
                "link": "/admin/auth/permission/",
                "permission": lambda request: request.user.is_superuser,
            },
            {
                "title": _("Content Types"),
                "icon": "category",
                "link": "/admin/contenttypes/contenttype/",
                "permission": lambda request: request.user.is_superuser,
            },
        ],
    },
    
    # ==================== GUIDES & HELP ====================
    {
        "title": _("Guides & Help"),
        "separator": True,
        "collapsible": True,
        "items": [
            {
                "title": _("Stock Movement Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("erp:stock-movement-guide"),
                "permission": check_app_installed("erp"),
            },
            {
                "title": _("Expense Management Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("erp:expense-management-guide"),
                "permission": check_app_installed("erp"),
            },
            {
                "title": _("Income Management Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("erp:income-management-guide"),
                "permission": check_app_installed("erp"),
            },
            {
                "title": _("Inventory Management Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("erp:inventory-management-guide"),
                "permission": check_app_installed("erp"),
            },
            {
                "title": _("Production Management Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("erp:production-management-guide"),
                "permission": check_app_installed("erp"),
            },
            {
                "title": _("Sales Management Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("erp:sales-management-guide"),
                "permission": check_app_installed("erp"),
            },
            {
                "title": _("Banking & Payment Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("erp:banking-management-guide"),
                "permission": check_app_installed("erp"),
            },
            {
                "title": _("Quality & Service Guide"),
                "icon": "help_outline",
                "link": lambda request: reverse_lazy("erp:quality-service-management-guide"),
                "permission": check_app_installed("erp"),
            },
        ],
    },
]