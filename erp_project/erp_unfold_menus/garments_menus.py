"""
Garments Module Menu Configuration for Unfold Admin
===================================================

This file contains all menu configurations for the Garments module.
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


# ==================== GARMENTS MODULE MENUS ====================
GARMENTS_MENUS = [
    # ==================== GARMENTS APP ====================
    {
        "title": _("Garments"),
        "separator": True,
        "collapsible": True,
        "items": [
            # Foundation & Setup
            {
                "title": _("Company"),
                "icon": "business",
                "link": admin_changelist("garments", "company"),
                "permission": check_app_and_permission("garments", "company"),
            },
            {
                "title": _("Factories"),
                "icon": "factory",
                "link": admin_changelist("garments", "factory"),
                "permission": check_app_and_permission("garments", "factory"),
            },
            {
                "title": _("Sizes"),
                "icon": "straighten",
                "link": admin_changelist("garments", "size"),
                "permission": check_app_and_permission("garments", "size"),
            },
            {
                "title": _("Colors"),
                "icon": "palette",
                "link": admin_changelist("garments", "color"),
                "permission": check_app_and_permission("garments", "color"),
            },
            {
                "title": _("Seasons"),
                "icon": "calendar_month",
                "link": admin_changelist("garments", "season"),
                "permission": check_app_and_permission("garments", "season"),
            },
            {
                "title": _("Garment Types"),
                "icon": "checkroom",
                "link": admin_changelist("garments", "garmenttype"),
                "permission": check_app_and_permission("garments", "garmenttype"),
            },
            # Buyers & Suppliers
            {
                "title": _("Buyers"),
                "icon": "store",
                "link": admin_changelist("garments", "buyer"),
                "permission": check_app_and_permission("garments", "buyer"),
            },
            {
                "title": _("Buyer Brands"),
                "icon": "label",
                "link": admin_changelist("garments", "buyerbrand"),
                "permission": check_app_and_permission("garments", "buyerbrand"),
            },
            {
                "title": _("Merchandisers"),
                "icon": "person_pin",
                "link": admin_changelist("garments", "merchandiser"),
                "permission": check_app_and_permission("garments", "merchandiser"),
            },
            {
                "title": _("Suppliers"),
                "icon": "local_shipping",
                "link": admin_changelist("garments", "supplier"),
                "permission": check_app_and_permission("garments", "supplier"),
            },
            # Materials
            {
                "title": _("Fabric Types"),
                "icon": "texture",
                "link": admin_changelist("garments", "fabrictype"),
                "permission": check_app_and_permission("garments", "fabrictype"),
            },
            {
                "title": _("Fabrics"),
                "icon": "layers",
                "link": admin_changelist("garments", "fabric"),
                "permission": check_app_and_permission("garments", "fabric"),
            },
            {
                "title": _("Trim Types"),
                "icon": "category",
                "link": admin_changelist("garments", "trimtype"),
                "permission": check_app_and_permission("garments", "trimtype"),
            },
            {
                "title": _("Trims"),
                "icon": "widgets",
                "link": admin_changelist("garments", "trim"),
                "permission": check_app_and_permission("garments", "trim"),
            },
            # Styles & Orders
            {
                "title": _("Styles"),
                "icon": "design_services",
                "link": admin_changelist("garments", "style"),
                "permission": check_app_and_permission("garments", "style"),
            },
            {
                "title": _("Style Costings"),
                "icon": "calculate",
                "link": admin_changelist("garments", "stylecosting"),
                "permission": check_app_and_permission("garments", "stylecosting"),
            },
            # Orders
            {
                "title": _("Buyer Orders"),
                "icon": "shopping_bag",
                "link": admin_changelist("garments", "buyerorder"),
                "permission": check_app_and_permission("garments", "buyerorder"),
            },
            # Production
            {
                "title": _("Sewing Lines"),
                "icon": "precision_manufacturing",
                "link": admin_changelist("garments", "sewingline"),
                "permission": check_app_and_permission("garments", "sewingline"),
            },
            {
                "title": _("Cutting Orders"),
                "icon": "content_cut",
                "link": admin_changelist("garments", "cuttingorder"),
                "permission": check_app_and_permission("garments", "cuttingorder"),
            },
            {
                "title": _("Bundles"),
                "icon": "inventory_2",
                "link": admin_changelist("garments", "bundle"),
                "permission": check_app_and_permission("garments", "bundle"),
            },
            {
                "title": _("Production Plans"),
                "icon": "event_note",
                "link": admin_changelist("garments", "productionplan"),
                "permission": check_app_and_permission("garments", "productionplan"),
            },
            {
                "title": _("Daily Production"),
                "icon": "today",
                "link": admin_changelist("garments", "dailyproduction"),
                "permission": check_app_and_permission("garments", "dailyproduction"),
            },
            # Quality Management
            {
                "title": _("Defect Types"),
                "icon": "bug_report",
                "link": admin_changelist("garments", "defecttype"),
                "permission": check_app_and_permission("garments", "defecttype"),
            },
            {
                "title": _("Inspections"),
                "icon": "fact_check",
                "link": admin_changelist("garments", "inspection"),
                "permission": check_app_and_permission("garments", "inspection"),
            },
            {
                "title": _("Quality Standards"),
                "icon": "verified_user",
                "link": admin_changelist("garments", "qualitystandard"),
                "permission": check_app_and_permission("garments", "qualitystandard"),
            },
            {
                "title": _("Inspection Plans"),
                "icon": "rule",
                "link": admin_changelist("garments", "inspectionplan"),
                "permission": check_app_and_permission("garments", "inspectionplan"),
            },
            {
                "title": _("Non-Conformance"),
                "icon": "warning",
                "link": admin_changelist("garments", "nonconformance"),
                "permission": check_app_and_permission("garments", "nonconformance"),
            },
            {
                "title": _("Corrective Actions"),
                "icon": "build",
                "link": admin_changelist("garments", "correctiveaction"),
                "permission": check_app_and_permission("garments", "correctiveaction"),
            },
            {
                "title": _("Quality Audits"),
                "icon": "assignment_turned_in",
                "link": admin_changelist("garments", "qualityaudit"),
                "permission": check_app_and_permission("garments", "qualityaudit"),
            },
            # Packing & Shipping
            {
                "title": _("Packing Lists"),
                "icon": "inventory",
                "link": admin_changelist("garments", "packinglist"),
                "permission": check_app_and_permission("garments", "packinglist"),
            },
            {
                "title": _("Shipments"),
                "icon": "flight_takeoff",
                "link": admin_changelist("garments", "shipment"),
                "permission": check_app_and_permission("garments", "shipment"),
            },
            # TNA & Compliance
            {
                "title": _("TNA Templates"),
                "icon": "view_timeline",
                "link": admin_changelist("garments", "tnatemplate"),
                "permission": check_app_and_permission("garments", "tnatemplate"),
            },
            {
                "title": _("TNA Tasks"),
                "icon": "task",
                "link": admin_changelist("garments", "tnatask"),
                "permission": check_app_and_permission("garments", "tnatask"),
            },
            {
                "title": _("Order TNA"),
                "icon": "timeline",
                "link": admin_changelist("garments", "ordertna"),
                "permission": check_app_and_permission("garments", "ordertna"),
            },
            {
                "title": _("Compliance Types"),
                "icon": "verified",
                "link": admin_changelist("garments", "compliancetype"),
                "permission": check_app_and_permission("garments", "compliancetype"),
            },
            {
                "title": _("Factory Compliance"),
                "icon": "shield",
                "link": admin_changelist("garments", "factorycompliance"),
                "permission": check_app_and_permission("garments", "factorycompliance"),
            },
            {
                "title": _("Test Types"),
                "icon": "science",
                "link": admin_changelist("garments", "testtype"),
                "permission": check_app_and_permission("garments", "testtype"),
            },
            {
                "title": _("Order Tests"),
                "icon": "biotech",
                "link": admin_changelist("garments", "ordertest"),
                "permission": check_app_and_permission("garments", "ordertest"),
            },
            # Costing & Pricing
            {
                "title": _("Costing Sheets"),
                "icon": "receipt_long",
                "link": admin_changelist("garments", "costingsheet"),
                "permission": check_app_and_permission("garments", "costingsheet"),
            },
            {
                "title": _("Price Lists"),
                "icon": "price_check",
                "link": admin_changelist("garments", "pricelist"),
                "permission": check_app_and_permission("garments", "pricelist"),
            },
            {
                "title": _("Quotation Costing"),
                "icon": "request_quote",
                "link": admin_changelist("garments", "quotationcosting"),
                "permission": check_app_and_permission("garments", "quotationcosting"),
            },
            {
                "title": _("Order Costing"),
                "icon": "account_balance",
                "link": admin_changelist("garments", "ordercosting"),
                "permission": check_app_and_permission("garments", "ordercosting"),
            },
            {
                "title": _("Profit Analysis"),
                "icon": "trending_up",
                "link": admin_changelist("garments", "profitanalysis"),
                "permission": check_app_and_permission("garments", "profitanalysis"),
            },
            {
                "title": _("Cost Variance"),
                "icon": "compare_arrows",
                "link": admin_changelist("garments", "costvariance"),
                "permission": check_app_and_permission("garments", "costvariance"),
            },
            # Capacity & Scheduling
            {
                "title": _("Capacity Plans"),
                "icon": "assessment",
                "link": admin_changelist("garments", "capacityplan"),
                "permission": check_app_and_permission("garments", "capacityplan"),
            },
            {
                "title": _("Production Schedule"),
                "icon": "schedule",
                "link": admin_changelist("garments", "productionschedule"),
                "permission": check_app_and_permission("garments", "productionschedule"),
            },
            {
                "title": _("Downtime Tracking"),
                "icon": "report_problem",
                "link": admin_changelist("garments", "downtimetracking"),
                "permission": check_app_and_permission("garments", "downtimetracking"),
            },
            {
                "title": _("Efficiency Tracking"),
                "icon": "speed",
                "link": admin_changelist("garments", "efficiencytracking"),
                "permission": check_app_and_permission("garments", "efficiencytracking"),
            },
            # Sample Management
            {
                "title": _("Sample Requests"),
                "icon": "request_page",
                "link": admin_changelist("garments", "samplerequest"),
                "permission": check_app_and_permission("garments", "samplerequest"),
            },
            {
                "title": _("Sample Development"),
                "icon": "construction",
                "link": admin_changelist("garments", "sampledevelopment"),
                "permission": check_app_and_permission("garments", "sampledevelopment"),
            },
            {
                "title": _("Sample Approvals"),
                "icon": "check_circle",
                "link": admin_changelist("garments", "sampleapproval"),
                "permission": check_app_and_permission("garments", "sampleapproval"),
            },
            # Material Inventory
            {
                "title": _("Fabric Receive"),
                "icon": "local_shipping",
                "link": admin_changelist("garments", "fabricreceive"),
                "permission": check_app_and_permission("garments", "fabricreceive"),
            },
            {
                "title": _("Trim Receive"),
                "icon": "move_to_inbox",
                "link": admin_changelist("garments", "trimreceive"),
                "permission": check_app_and_permission("garments", "trimreceive"),
            },
            {
                "title": _("Fabric Stock"),
                "icon": "inventory",
                "link": admin_changelist("garments", "fabricstock"),
                "permission": check_app_and_permission("garments", "fabricstock"),
            },
            {
                "title": _("Fabric Issue"),
                "icon": "output",
                "link": admin_changelist("garments", "fabricissue"),
                "permission": check_app_and_permission("garments", "fabricissue"),
            },
            {
                "title": _("Trim Stock"),
                "icon": "category",
                "link": admin_changelist("garments", "trimstock"),
                "permission": check_app_and_permission("garments", "trimstock"),
            },
            {
                "title": _("Material Requisition"),
                "icon": "assignment",
                "link": admin_changelist("garments", "materialrequisition"),
                "permission": check_app_and_permission("garments", "materialrequisition"),
            },
            # Subcontracting
            {
                "title": _("Subcontractors"),
                "icon": "business_center",
                "link": admin_changelist("garments", "subcontractor"),
                "permission": check_app_and_permission("garments", "subcontractor"),
            },
            {
                "title": _("Subcontract Orders"),
                "icon": "description",
                "link": admin_changelist("garments", "subcontractorder"),
                "permission": check_app_and_permission("garments", "subcontractorder"),
            },
            {
                "title": _("Subcontract Delivery"),
                "icon": "local_shipping",
                "link": admin_changelist("garments", "subcontractdelivery"),
                "permission": check_app_and_permission("garments", "subcontractdelivery"),
            },
        ],  # End of Garments items
    },  # End of Garments section
]