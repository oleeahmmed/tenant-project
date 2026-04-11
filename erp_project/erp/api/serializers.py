"""
ERP API Serializers - Only existing models
"""
from rest_framework import serializers
from erp.models import (
    Company, Warehouse, Category, Product, Customer, Supplier, SalesPerson,
    SalesQuotation, SalesQuotationItem, SalesOrder, SalesOrderItem,
    Invoice, InvoiceItem, SalesReturn, SalesReturnItem,
    Delivery, DeliveryItem,
    PurchaseQuotation, PurchaseQuotationItem, PurchaseOrder, PurchaseOrderItem,
    GoodsReceipt, GoodsReceiptItem, PurchaseInvoice, PurchaseInvoiceItem,
    PurchaseReturn, PurchaseReturnItem,
    BillOfMaterials, BOMComponent, ProductionOrder, ProductionOrderComponent,
    ProductionReceipt, ProductionReceiptItem,
    GoodsIssue, GoodsIssueItem, ProductWarehouseStock,
    InventoryTransfer, InventoryTransferItem, StockTransaction,
    BankAccount, IncomingPayment, IncomingPaymentInvoice,
    OutgoingPayment, OutgoingPaymentInvoice,
    AccountType, ChartOfAccounts, CostCenter, Project, FiscalYear,
    JournalEntry, JournalEntryLine, Budget,
    Currency, ExchangeRate, TaxType, TaxRate, PaymentTerm, PriceList, PriceListItem,
    UnitOfMeasure, UOMConversion, StockAdjustment, StockAdjustmentItem,
    DiscountType, DiscountRule,
    ApprovalWorkflow, ApprovalLevel, ApprovalRequest,
    NotificationType, Notification, AlertRule, NotificationSetting,
    PaymentMethod,
)


# ==================== FOUNDATION & SETUP ====================

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    default_warehouse_name = serializers.CharField(source='default_warehouse.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Product
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class SalesPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesPerson
        fields = '__all__'


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = '__all__'


class UOMConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UOMConversion
        fields = '__all__'


# ==================== FINANCIAL FOUNDATION ====================

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'


class ExchangeRateSerializer(serializers.ModelSerializer):
    from_currency = serializers.CharField()
    to_currency = serializers.CharField()
    
    class Meta:
        model = ExchangeRate
        fields = '__all__'
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['from_currency'] = instance.from_currency.code
        data['to_currency'] = instance.to_currency.code
        return data
    
    def to_internal_value(self, data):
        if isinstance(data.get('from_currency'), str):
            try:
                from_curr = Currency.objects.get(code=data['from_currency'])
                data['from_currency'] = from_curr.id
            except Currency.DoesNotExist:
                raise serializers.ValidationError({'from_currency': 'Currency not found'})
        
        if isinstance(data.get('to_currency'), str):
            try:
                to_curr = Currency.objects.get(code=data['to_currency'])
                data['to_currency'] = to_curr.id
            except Currency.DoesNotExist:
                raise serializers.ValidationError({'to_currency': 'Currency not found'})
        
        return super().to_internal_value(data)


class TaxTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxType
        fields = '__all__'


class TaxRateSerializer(serializers.ModelSerializer):
    tax_type_name = serializers.CharField(source='tax_type.name', read_only=True)
    
    class Meta:
        model = TaxRate
        fields = '__all__'


class PaymentTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTerm
        fields = '__all__'


class PriceListSerializer(serializers.ModelSerializer):
    currency_name = serializers.CharField(source='currency.code', read_only=True, allow_null=True)
    
    class Meta:
        model = PriceList
        fields = '__all__'


class PriceListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceListItem
        fields = '__all__'


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'


class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = '__all__'


class ChartOfAccountsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChartOfAccounts
        fields = '__all__'


class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Project
        fields = '__all__'


class FiscalYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalYear
        fields = '__all__'


# ==================== SALES PROCESS ====================

class SalesQuotationItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SalesQuotationItem
        fields = '__all__'


class SalesQuotationSerializer(serializers.ModelSerializer):
    items = SalesQuotationItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = SalesQuotation
        fields = '__all__'


class SalesOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SalesOrderItem
        fields = '__all__'


class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = '__all__'


class DeliveryItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = DeliveryItem
        fields = '__all__'


class DeliverySerializer(serializers.ModelSerializer):
    items = DeliveryItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = Delivery
        fields = '__all__'


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = '__all__'


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = Invoice
        fields = '__all__'


class SalesReturnItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SalesReturnItem
        fields = '__all__'


class SalesReturnSerializer(serializers.ModelSerializer):
    items = SalesReturnItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = SalesReturn
        fields = '__all__'


class IncomingPaymentInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomingPaymentInvoice
        fields = '__all__'


class IncomingPaymentSerializer(serializers.ModelSerializer):
    invoices = IncomingPaymentInvoiceSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = IncomingPayment
        fields = '__all__'


# ==================== PURCHASE PROCESS ====================

class PurchaseQuotationItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = PurchaseQuotationItem
        fields = '__all__'


class PurchaseQuotationSerializer(serializers.ModelSerializer):
    items = PurchaseQuotationItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = PurchaseQuotation
        fields = '__all__'


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    remaining_to_receive = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    received_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = '__all__'


class GoodsReceiptItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = GoodsReceiptItem
        fields = '__all__'


class GoodsReceiptSerializer(serializers.ModelSerializer):
    items = GoodsReceiptItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = GoodsReceipt
        fields = '__all__'


class PurchaseInvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = PurchaseInvoiceItem
        fields = '__all__'


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    items = PurchaseInvoiceItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = PurchaseInvoice
        fields = '__all__'


class PurchaseReturnItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = PurchaseReturnItem
        fields = '__all__'


class PurchaseReturnSerializer(serializers.ModelSerializer):
    items = PurchaseReturnItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = PurchaseReturn
        fields = '__all__'


class OutgoingPaymentInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutgoingPaymentInvoice
        fields = '__all__'


class OutgoingPaymentSerializer(serializers.ModelSerializer):
    invoices = OutgoingPaymentInvoiceSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = OutgoingPayment
        fields = '__all__'


# ==================== MANUFACTURING ====================

class BOMComponentSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = BOMComponent
        fields = '__all__'


class BillOfMaterialsSerializer(serializers.ModelSerializer):
    components = BOMComponentSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = BillOfMaterials
        fields = '__all__'


class ProductionOrderComponentSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductionOrderComponent
        fields = '__all__'


class ProductionOrderSerializer(serializers.ModelSerializer):
    components = ProductionOrderComponentSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductionOrder
        fields = '__all__'


class ProductionReceiptItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductionReceiptItem
        fields = '__all__'


class ProductionReceiptSerializer(serializers.ModelSerializer):
    items = ProductionReceiptItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductionReceipt
        fields = '__all__'


# ==================== INVENTORY CONTROL ====================

class StockAdjustmentItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = StockAdjustmentItem
        fields = '__all__'


class StockAdjustmentSerializer(serializers.ModelSerializer):
    items = StockAdjustmentItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = StockAdjustment
        fields = '__all__'


class GoodsIssueItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = GoodsIssueItem
        fields = '__all__'


class GoodsIssueSerializer(serializers.ModelSerializer):
    items = GoodsIssueItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = GoodsIssue
        fields = '__all__'


class InventoryTransferItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = InventoryTransferItem
        fields = '__all__'


class InventoryTransferSerializer(serializers.ModelSerializer):
    items = InventoryTransferItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = InventoryTransfer
        fields = '__all__'


class ProductWarehouseStockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    
    class Meta:
        model = ProductWarehouseStock
        fields = '__all__'


class StockTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = StockTransaction
        fields = '__all__'


# ==================== ACCOUNTING ====================

class JournalEntryLineSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = JournalEntryLine
        fields = '__all__'


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalEntryLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = JournalEntry
        fields = '__all__'


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = '__all__'


# ==================== DISCOUNT MANAGEMENT ====================

class DiscountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountType
        fields = '__all__'


class DiscountRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountRule
        fields = '__all__'


# ==================== APPROVAL WORKFLOW ====================

class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalWorkflow
        fields = '__all__'


class ApprovalLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalLevel
        fields = '__all__'


class ApprovalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRequest
        fields = '__all__'


# ==================== NOTIFICATIONS ====================

class NotificationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationType
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class AlertRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRule
        fields = '__all__'


class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = '__all__'


# ==================== POS (QUICK SALE) ====================

from erp.models import QuickSale, QuickSaleItem, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    default_customer_name = serializers.CharField(source='default_customer.name', read_only=True, allow_null=True)
    default_warehouse_name = serializers.CharField(source='default_warehouse.name', read_only=True, allow_null=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'


class QuickSaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = QuickSaleItem
        fields = '__all__'


class QuickSaleSerializer(serializers.ModelSerializer):
    items = QuickSaleItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, allow_null=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = QuickSale
        fields = '__all__'
        read_only_fields = ['sale_number', 'user']


class QuickSaleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Quick Sale with items - warehouse/customer from user profile"""
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    
    class Meta:
        model = QuickSale
        fields = ['id', 'sale_number', 'customer_name', 'customer_phone', 'discount_amount', 
                  'payment_method', 'amount_received', 'notes', 'items', 'subtotal', 'total_amount']
        read_only_fields = ['id', 'sale_number', 'subtotal', 'total_amount']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        request = self.context.get('request')
        user = request.user
        
        # Set user
        validated_data['user'] = user
        
        # Get warehouse and customer from user's profile
        from erp.models import UserProfile, Warehouse
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.branch:
                validated_data['branch'] = profile.branch
            if profile.default_customer:
                validated_data['customer'] = profile.default_customer
        except UserProfile.DoesNotExist:
            # Fallback to first active warehouse
            first_wh = Warehouse.objects.filter(is_active=True).first()
            if first_wh:
                validated_data['branch'] = first_wh
        
        # Create QuickSale
        quick_sale = QuickSale.objects.create(**validated_data)
        
        # Create items
        from decimal import Decimal
        for item_data in items_data:
            QuickSaleItem.objects.create(
                quick_sale=quick_sale,
                product_id=item_data['product'],
                quantity=Decimal(str(item_data['quantity'])),
                unit_price=Decimal(str(item_data['unit_price']))
            )
        
        # Calculate totals
        quick_sale.calculate_totals()
        
        return quick_sale
