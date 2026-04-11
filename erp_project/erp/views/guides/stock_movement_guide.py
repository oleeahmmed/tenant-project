"""
Stock Movement Guide View
Shows which transactions affect stock and how
"""
from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.utils.decorators import method_decorator


@method_decorator(staff_member_required, name='dispatch')
class StockMovementGuideView(TemplateView):
    """
    Stock Movement Guide - Shows all transactions that affect inventory
    """
    template_name = 'admin/erp/guides/stock_movement_guide.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ⭐ REQUIRED: Admin context for Unfold sidebar and styling
        context.update(admin.site.each_context(self.request))
        
        # Page title
        context['title'] = 'Stock Movement Guide'
        
        # Stock IN transactions
        context['stock_in_transactions'] = [
            {
                'document': 'Goods Receipt (General)',
                'model': 'GoodsReceipt',
                'trigger_status': 'received',
                'description': 'Opening Stock, Stock Adjustment, Found Items, Transfer In',
                'reference_prefix': 'GRN:',
                'icon': 'move_to_inbox',
                'color': 'green',
            },
            {
                'document': 'Goods Receipt (PO)',
                'model': 'GoodsReceiptPO',
                'trigger_status': 'received / inspected / completed',
                'description': 'Purchase Order থেকে goods receive করলে accepted_quantity stock এ যোগ হয়',
                'reference_prefix': 'GRPO:',
                'icon': 'inventory',
                'color': 'green',
            },
            {
                'document': 'Sales Return',
                'model': 'SalesReturn',
                'trigger_status': 'completed',
                'description': 'Customer থেকে goods ফেরত আসলে stock বাড়ে',
                'reference_prefix': 'SR:',
                'icon': 'assignment_return',
                'color': 'green',
            },
            {
                'document': 'Production Receipt',
                'model': 'ProductionReceipt',
                'trigger_status': 'completed',
                'description': 'Production complete হলে finished product stock এ যোগ হয়',
                'reference_prefix': 'PRR:',
                'icon': 'fact_check',
                'color': 'green',
            },
            {
                'document': 'Inventory Transfer',
                'model': 'InventoryTransfer',
                'trigger_status': 'completed',
                'description': 'Destination warehouse এ stock IN হয়',
                'reference_prefix': 'IT:',
                'icon': 'compare_arrows',
                'color': 'green',
            },
            {
                'document': 'Stock Adjustment',
                'model': 'StockAdjustment',
                'trigger_status': 'approved / posted',
                'description': 'Actual > System হলে stock বাড়ে',
                'reference_prefix': 'ADJ:',
                'icon': 'tune',
                'color': 'green',
            },
        ]
        
        # Stock OUT transactions
        context['stock_out_transactions'] = [
            {
                'document': 'Delivery',
                'model': 'Delivery',
                'trigger_status': 'delivered',
                'description': 'Customer কে goods deliver করলে stock কমে',
                'reference_prefix': 'DL:',
                'icon': 'local_shipping',
                'color': 'red',
            },
            {
                'document': 'Quick Sale (POS)',
                'model': 'QuickSale',
                'trigger_status': 'completed',
                'description': 'POS sale complete হলে stock কমে',
                'reference_prefix': 'QS:',
                'icon': 'bolt',
                'color': 'red',
            },
            {
                'document': 'Goods Issue',
                'model': 'GoodsIssue',
                'trigger_status': 'issued',
                'description': 'Internal use, Damage, Scrap, Sample ইত্যাদির জন্য stock কমে',
                'reference_prefix': 'GI:',
                'icon': 'outbox',
                'color': 'red',
            },
            {
                'document': 'Purchase Return',
                'model': 'PurchaseReturn',
                'trigger_status': 'completed',
                'description': 'Supplier কে goods ফেরত দিলে stock কমে',
                'reference_prefix': 'PR:',
                'icon': 'keyboard_return',
                'color': 'red',
            },
            {
                'document': 'Production Receipt',
                'model': 'ProductionReceipt',
                'trigger_status': 'completed',
                'description': 'BOM components consume হয়ে stock কমে',
                'reference_prefix': 'PRR:',
                'icon': 'fact_check',
                'color': 'red',
            },
            {
                'document': 'Production Issue',
                'model': 'ProductionIssue',
                'trigger_status': 'issued',
                'description': 'Multiple production orders এর জন্য BOM components issue হয়ে stock কমে',
                'reference_prefix': 'PI:',
                'icon': 'output',
                'color': 'red',
            },
            {
                'document': 'Inventory Transfer',
                'model': 'InventoryTransfer',
                'trigger_status': 'completed',
                'description': 'Source warehouse থেকে stock OUT হয়',
                'reference_prefix': 'IT:',
                'icon': 'compare_arrows',
                'color': 'red',
            },
            {
                'document': 'Stock Adjustment',
                'model': 'StockAdjustment',
                'trigger_status': 'approved / posted',
                'description': 'Actual < System হলে stock কমে',
                'reference_prefix': 'ADJ:',
                'icon': 'tune',
                'color': 'red',
            },
        ]
        
        # No stock movement transactions
        context['no_stock_transactions'] = [
            {
                'document': 'Sales Quotation',
                'description': 'শুধু quotation, stock affect করে না',
                'icon': 'request_quote',
            },
            {
                'document': 'Sales Order',
                'description': 'Order confirm, কিন্তু stock affect করে না। Delivery তে stock কমে।',
                'icon': 'shopping_cart',
            },
            {
                'document': 'Invoice',
                'description': 'শুধু billing document, stock affect করে না',
                'icon': 'receipt',
            },
            {
                'document': 'Purchase Quotation',
                'description': 'শুধু quotation, stock affect করে না',
                'icon': 'request_quote',
            },
            {
                'document': 'Purchase Order',
                'description': 'Order confirm, কিন্তু stock affect করে না। Goods Receipt এ stock বাড়ে।',
                'icon': 'shopping_bag',
            },
            {
                'document': 'Purchase Invoice',
                'description': 'শুধু billing document, stock affect করে না',
                'icon': 'receipt_long',
            },
            {
                'document': 'Production Order',
                'description': 'শুধু planning, stock affect করে না। Production Receipt/Issue এ stock change হয়।',
                'icon': 'precision_manufacturing',
            },
            {
                'document': 'Production Issue',
                'description': 'Status "issued" হলে components stock থেকে OUT হয়',
                'icon': 'output',
            },
            {
                'document': 'Bill of Materials',
                'description': 'শুধু recipe/formula, stock affect করে না',
                'icon': 'list_alt',
            },
        ]
        
        # Important notes
        context['important_notes'] = [
            'Stock Transaction তৈরি হয় শুধুমাত্র নির্দিষ্ট status এ change হলে',
            'Status reverse করলে (যেমন delivered → pending) stock transaction delete হয়ে stock ফিরে আসে',
            'Stock Transaction delete করলে automatically stock reverse হয়',
            'Warehouse Stock = সব Stock Transaction এর sum',
            'Product এর current_stock = সব warehouse এর total stock',
            '⚠️ Production Receipt - Components OUT + Finished IN একসাথে হয়',
            '⚠️ Production Issue - শুধু Components OUT (multiple production orders এর জন্য)',
        ]
        
        return context
