"""
ERP API Views - Only existing models with ModelViewSet
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import DjangoModelPermissions
from django_filters.rest_framework import DjangoFilterBackend

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

from .serializers import (
    CompanySerializer, WarehouseSerializer, CategorySerializer, ProductSerializer,
    CustomerSerializer, SupplierSerializer, SalesPersonSerializer, PaymentMethodSerializer,
    UnitOfMeasureSerializer, UOMConversionSerializer,
    CurrencySerializer, ExchangeRateSerializer, TaxTypeSerializer, TaxRateSerializer,
    PaymentTermSerializer, PriceListSerializer, PriceListItemSerializer,
    BankAccountSerializer, AccountTypeSerializer, ChartOfAccountsSerializer,
    CostCenterSerializer, ProjectSerializer, FiscalYearSerializer,
    SalesQuotationSerializer, SalesQuotationItemSerializer,
    SalesOrderSerializer, SalesOrderItemSerializer,
    DeliverySerializer, DeliveryItemSerializer,
    InvoiceSerializer, InvoiceItemSerializer,
    SalesReturnSerializer, SalesReturnItemSerializer,
    IncomingPaymentSerializer, IncomingPaymentInvoiceSerializer,
    PurchaseQuotationSerializer, PurchaseQuotationItemSerializer,
    PurchaseOrderSerializer, PurchaseOrderItemSerializer,
    GoodsReceiptSerializer, GoodsReceiptItemSerializer,
    PurchaseInvoiceSerializer, PurchaseInvoiceItemSerializer,
    PurchaseReturnSerializer, PurchaseReturnItemSerializer,
    OutgoingPaymentSerializer, OutgoingPaymentInvoiceSerializer,
    BillOfMaterialsSerializer, BOMComponentSerializer,
    ProductionOrderSerializer, ProductionOrderComponentSerializer,
    ProductionReceiptSerializer, ProductionReceiptItemSerializer,
    StockAdjustmentSerializer, StockAdjustmentItemSerializer,
    GoodsIssueSerializer, GoodsIssueItemSerializer,
    InventoryTransferSerializer, InventoryTransferItemSerializer,
    ProductWarehouseStockSerializer, StockTransactionSerializer,
    JournalEntrySerializer, JournalEntryLineSerializer, BudgetSerializer,
    DiscountTypeSerializer, DiscountRuleSerializer,
    ApprovalWorkflowSerializer, ApprovalLevelSerializer, ApprovalRequestSerializer,
    NotificationTypeSerializer, NotificationSerializer,
    AlertRuleSerializer, NotificationSettingSerializer,
)


# ==================== FOUNDATION & SETUP ====================

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'created_at']


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'city']
    ordering_fields = ['name', 'code']


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'default_warehouse').all()
    serializer_class = ProductSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'sku', 'selling_price']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Support exact SKU lookup for barcode scanning
        sku = self.request.query_params.get('sku', None)
        if sku:
            queryset = queryset.filter(sku__iexact=sku)
        return queryset


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'created_at']
    
    @action(detail=False, methods=['get'])
    def by_phone(self, request):
        """Search customer by phone number
        
        Usage: /api/erp/customers/by-phone/?phone=01712345678
        """
        phone = request.query_params.get('phone', None)
        
        if not phone:
            return Response(
                {'error': 'Phone number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try exact match first
        customer = Customer.objects.filter(phone=phone, is_active=True).first()
        
        # If not found, try partial match (contains)
        if not customer:
            customer = Customer.objects.filter(
                phone__icontains=phone,
                is_active=True
            ).first()
        
        if customer:
            serializer = self.get_serializer(customer)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Customer not found'},
            status=status.HTTP_404_NOT_FOUND
        )


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'created_at']


class SalesPersonViewSet(viewsets.ModelViewSet):
    queryset = SalesPerson.objects.all()
    serializer_class = SalesPersonSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'employee_id']


class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class UnitOfMeasureViewSet(viewsets.ModelViewSet):
    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitOfMeasureSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class UOMConversionViewSet(viewsets.ModelViewSet):
    queryset = UOMConversion.objects.all()
    serializer_class = UOMConversionSerializer
    permission_classes = [DjangoModelPermissions]


# ==================== FINANCIAL FOUNDATION ====================

class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class ExchangeRateViewSet(viewsets.ModelViewSet):
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['effective_date']


class TaxTypeViewSet(viewsets.ModelViewSet):
    queryset = TaxType.objects.all()
    serializer_class = TaxTypeSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all()
    serializer_class = TaxRateSerializer
    permission_classes = [DjangoModelPermissions]


class PaymentTermViewSet(viewsets.ModelViewSet):
    queryset = PaymentTerm.objects.all()
    serializer_class = PaymentTermSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class PriceListViewSet(viewsets.ModelViewSet):
    queryset = PriceList.objects.all()
    serializer_class = PriceListSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class PriceListItemViewSet(viewsets.ModelViewSet):
    queryset = PriceListItem.objects.all()
    serializer_class = PriceListItemSerializer
    permission_classes = [DjangoModelPermissions]


class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'account_number', 'bank_name']


class AccountTypeViewSet(viewsets.ModelViewSet):
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class ChartOfAccountsViewSet(viewsets.ModelViewSet):
    queryset = ChartOfAccounts.objects.all()
    serializer_class = ChartOfAccountsSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'account_code']


class CostCenterViewSet(viewsets.ModelViewSet):
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class FiscalYearViewSet(viewsets.ModelViewSet):
    queryset = FiscalYear.objects.all()
    serializer_class = FiscalYearSerializer
    permission_classes = [DjangoModelPermissions]


# ==================== SALES PROCESS ====================

class SalesQuotationViewSet(viewsets.ModelViewSet):
    queryset = SalesQuotation.objects.select_related('customer', 'salesperson').prefetch_related('items').all()
    serializer_class = SalesQuotationSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['quotation_number', 'customer__name']
    ordering_fields = ['quotation_date', 'total_amount']


class SalesQuotationItemViewSet(viewsets.ModelViewSet):
    queryset = SalesQuotationItem.objects.select_related('product').all()
    serializer_class = SalesQuotationItemSerializer
    permission_classes = [DjangoModelPermissions]


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.select_related('customer', 'salesperson').prefetch_related('items').all()
    serializer_class = SalesOrderSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'customer__name']
    ordering_fields = ['order_date', 'total_amount']


class SalesOrderItemViewSet(viewsets.ModelViewSet):
    queryset = SalesOrderItem.objects.select_related('product').all()
    serializer_class = SalesOrderItemSerializer
    permission_classes = [DjangoModelPermissions]


class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.select_related('customer', 'sales_order').prefetch_related('items').all()
    serializer_class = DeliverySerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['delivery_number', 'customer__name']
    ordering_fields = ['delivery_date']


class DeliveryItemViewSet(viewsets.ModelViewSet):
    queryset = DeliveryItem.objects.select_related('product').all()
    serializer_class = DeliveryItemSerializer
    permission_classes = [DjangoModelPermissions]


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related('customer', 'sales_order').prefetch_related('items').all()
    serializer_class = InvoiceSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'customer__name']
    ordering_fields = ['invoice_date', 'total_amount', 'due_amount']


class InvoiceItemViewSet(viewsets.ModelViewSet):
    queryset = InvoiceItem.objects.select_related('product').all()
    serializer_class = InvoiceItemSerializer
    permission_classes = [DjangoModelPermissions]


class SalesReturnViewSet(viewsets.ModelViewSet):
    queryset = SalesReturn.objects.select_related('customer', 'sales_order').prefetch_related('items').all()
    serializer_class = SalesReturnSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['return_number', 'customer__name']
    ordering_fields = ['return_date']


class SalesReturnItemViewSet(viewsets.ModelViewSet):
    queryset = SalesReturnItem.objects.select_related('product').all()
    serializer_class = SalesReturnItemSerializer
    permission_classes = [DjangoModelPermissions]


class IncomingPaymentViewSet(viewsets.ModelViewSet):
    queryset = IncomingPayment.objects.select_related('customer', 'bank_account').prefetch_related('invoices').all()
    serializer_class = IncomingPaymentSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['payment_number', 'customer__name']
    ordering_fields = ['payment_date', 'amount']


class IncomingPaymentInvoiceViewSet(viewsets.ModelViewSet):
    queryset = IncomingPaymentInvoice.objects.all()
    serializer_class = IncomingPaymentInvoiceSerializer
    permission_classes = [DjangoModelPermissions]


# ==================== PURCHASE PROCESS ====================

class PurchaseQuotationViewSet(viewsets.ModelViewSet):
    queryset = PurchaseQuotation.objects.select_related('supplier').prefetch_related('items').all()
    serializer_class = PurchaseQuotationSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['quotation_number', 'supplier__name']
    ordering_fields = ['quotation_date', 'total_amount']


class PurchaseQuotationItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseQuotationItem.objects.select_related('product').all()
    serializer_class = PurchaseQuotationItemSerializer
    permission_classes = [DjangoModelPermissions]


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related('supplier').prefetch_related('items').all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'supplier__name']
    ordering_fields = ['order_date', 'total_amount']


class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderItem.objects.select_related('product', 'purchase_order').all()
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['purchase_order', 'product']
    search_fields = ['product__name', 'product__sku']


class GoodsReceiptViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceipt.objects.select_related('supplier', 'purchase_order').prefetch_related('items').all()
    serializer_class = GoodsReceiptSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['receipt_number', 'supplier__name']
    ordering_fields = ['receipt_date']


class GoodsReceiptItemViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceiptItem.objects.select_related('product').all()
    serializer_class = GoodsReceiptItemSerializer
    permission_classes = [DjangoModelPermissions]


class PurchaseInvoiceViewSet(viewsets.ModelViewSet):
    queryset = PurchaseInvoice.objects.select_related('supplier', 'purchase_order').prefetch_related('items').all()
    serializer_class = PurchaseInvoiceSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'supplier__name']
    ordering_fields = ['invoice_date', 'total_amount']


class PurchaseInvoiceItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseInvoiceItem.objects.select_related('product').all()
    serializer_class = PurchaseInvoiceItemSerializer
    permission_classes = [DjangoModelPermissions]


class PurchaseReturnViewSet(viewsets.ModelViewSet):
    queryset = PurchaseReturn.objects.select_related('supplier', 'purchase_order').prefetch_related('items').all()
    serializer_class = PurchaseReturnSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['return_number', 'supplier__name']
    ordering_fields = ['return_date']


class PurchaseReturnItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseReturnItem.objects.select_related('product').all()
    serializer_class = PurchaseReturnItemSerializer
    permission_classes = [DjangoModelPermissions]


class OutgoingPaymentViewSet(viewsets.ModelViewSet):
    queryset = OutgoingPayment.objects.select_related('supplier', 'bank_account').prefetch_related('invoices').all()
    serializer_class = OutgoingPaymentSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['payment_number', 'supplier__name']
    ordering_fields = ['payment_date', 'amount']


class OutgoingPaymentInvoiceViewSet(viewsets.ModelViewSet):
    queryset = OutgoingPaymentInvoice.objects.all()
    serializer_class = OutgoingPaymentInvoiceSerializer
    permission_classes = [DjangoModelPermissions]


# ==================== MANUFACTURING ====================

class BillOfMaterialsViewSet(viewsets.ModelViewSet):
    queryset = BillOfMaterials.objects.select_related('product').prefetch_related('components').all()
    serializer_class = BillOfMaterialsSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['bom_number', 'product__name']
    ordering_fields = ['created_at']


class BOMComponentViewSet(viewsets.ModelViewSet):
    queryset = BOMComponent.objects.select_related('product').all()
    serializer_class = BOMComponentSerializer
    permission_classes = [DjangoModelPermissions]


class ProductionOrderViewSet(viewsets.ModelViewSet):
    queryset = ProductionOrder.objects.select_related('product', 'bom').prefetch_related('components').all()
    serializer_class = ProductionOrderSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'product__name']
    ordering_fields = ['planned_start_date', 'created_at']


class ProductionOrderComponentViewSet(viewsets.ModelViewSet):
    queryset = ProductionOrderComponent.objects.select_related('product').all()
    serializer_class = ProductionOrderComponentSerializer
    permission_classes = [DjangoModelPermissions]


class ProductionReceiptViewSet(viewsets.ModelViewSet):
    queryset = ProductionReceipt.objects.select_related('production_order').prefetch_related('components').all()
    serializer_class = ProductionReceiptSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['receipt_number']
    ordering_fields = ['receipt_date']


class ProductionReceiptItemViewSet(viewsets.ModelViewSet):
    queryset = ProductionReceiptItem.objects.select_related('product').all()
    serializer_class = ProductionReceiptItemSerializer
    permission_classes = [DjangoModelPermissions]


# ==================== INVENTORY CONTROL ====================

class StockAdjustmentViewSet(viewsets.ModelViewSet):
    queryset = StockAdjustment.objects.select_related('warehouse').prefetch_related('items').all()
    serializer_class = StockAdjustmentSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['adjustment_number']
    ordering_fields = ['adjustment_date']


class StockAdjustmentItemViewSet(viewsets.ModelViewSet):
    queryset = StockAdjustmentItem.objects.select_related('product').all()
    serializer_class = StockAdjustmentItemSerializer
    permission_classes = [DjangoModelPermissions]


class GoodsIssueViewSet(viewsets.ModelViewSet):
    queryset = GoodsIssue.objects.select_related('warehouse').prefetch_related('items').all()
    serializer_class = GoodsIssueSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['issue_number']
    ordering_fields = ['issue_date']


class GoodsIssueItemViewSet(viewsets.ModelViewSet):
    queryset = GoodsIssueItem.objects.select_related('product').all()
    serializer_class = GoodsIssueItemSerializer
    permission_classes = [DjangoModelPermissions]


class InventoryTransferViewSet(viewsets.ModelViewSet):
    queryset = InventoryTransfer.objects.select_related('from_warehouse', 'to_warehouse').prefetch_related('items').all()
    serializer_class = InventoryTransferSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['transfer_number']
    ordering_fields = ['transfer_date']


class InventoryTransferItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryTransferItem.objects.select_related('product').all()
    serializer_class = InventoryTransferItemSerializer
    permission_classes = [DjangoModelPermissions]


class ProductWarehouseStockViewSet(viewsets.ModelViewSet):
    queryset = ProductWarehouseStock.objects.select_related('product', 'warehouse').all()
    serializer_class = ProductWarehouseStockSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['product__name', 'product__sku']


class StockTransactionViewSet(viewsets.ModelViewSet):
    queryset = StockTransaction.objects.select_related('product', 'warehouse').all()
    serializer_class = StockTransactionSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']


# ==================== ACCOUNTING ====================

class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.prefetch_related('lines').all()
    serializer_class = JournalEntrySerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['entry_number', 'description']
    ordering_fields = ['entry_date']


class JournalEntryLineViewSet(viewsets.ModelViewSet):
    queryset = JournalEntryLine.objects.select_related('account').all()
    serializer_class = JournalEntryLineSerializer
    permission_classes = [DjangoModelPermissions]


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['budget_name']


# ==================== DISCOUNT MANAGEMENT ====================

class DiscountTypeViewSet(viewsets.ModelViewSet):
    queryset = DiscountType.objects.all()
    serializer_class = DiscountTypeSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class DiscountRuleViewSet(viewsets.ModelViewSet):
    queryset = DiscountRule.objects.all()
    serializer_class = DiscountRuleSerializer
    permission_classes = [DjangoModelPermissions]


# ==================== APPROVAL WORKFLOW ====================

class ApprovalWorkflowViewSet(viewsets.ModelViewSet):
    queryset = ApprovalWorkflow.objects.all()
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ApprovalLevelViewSet(viewsets.ModelViewSet):
    queryset = ApprovalLevel.objects.all()
    serializer_class = ApprovalLevelSerializer
    permission_classes = [DjangoModelPermissions]


class ApprovalRequestViewSet(viewsets.ModelViewSet):
    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']


# ==================== NOTIFICATIONS ====================

class NotificationTypeViewSet(viewsets.ModelViewSet):
    queryset = NotificationType.objects.all()
    serializer_class = NotificationTypeSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']


class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class NotificationSettingViewSet(viewsets.ModelViewSet):
    queryset = NotificationSetting.objects.all()
    serializer_class = NotificationSettingSerializer
    permission_classes = [DjangoModelPermissions]


# ==================== POS (QUICK SALE) ====================

from erp.models import QuickSale, QuickSaleItem, UserProfile
from .serializers import QuickSaleSerializer, QuickSaleItemSerializer, QuickSaleCreateSerializer, UserProfileSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.select_related('user', 'default_customer', 'branch').all()
    serializer_class = UserProfileSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'user__email']
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's profile"""
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


class QuickSaleViewSet(viewsets.ModelViewSet):
    queryset = QuickSale.objects.select_related('customer', 'warehouse', 'user').prefetch_related('items').all()
    serializer_class = QuickSaleSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['sale_number', 'customer_name', 'customer_phone']
    ordering_fields = ['sale_date', 'total_amount', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return QuickSaleCreateSerializer
        return QuickSaleSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a quick sale - update stock"""
        quick_sale = self.get_object()
        success, message = quick_sale.complete_sale()
        
        if success:
            return Response({'status': 'completed', 'message': message})
        return Response({'status': 'error', 'message': message}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's sales"""
        from django.utils import timezone
        today = timezone.now().date()
        sales = self.queryset.filter(sale_date=today)
        serializer = self.get_serializer(sales, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get sales summary"""
        from django.db.models import Sum, Count
        from django.utils import timezone
        
        today = timezone.now().date()
        
        today_sales = self.queryset.filter(sale_date=today, status='completed')
        today_summary = today_sales.aggregate(
            total_sales=Sum('total_amount'),
            total_orders=Count('id')
        )
        
        return Response({
            'today': {
                'total_sales': today_summary['total_sales'] or 0,
                'total_orders': today_summary['total_orders'] or 0,
            }
        })


class QuickSaleItemViewSet(viewsets.ModelViewSet):
    queryset = QuickSaleItem.objects.select_related('product', 'quick_sale').all()
    serializer_class = QuickSaleItemSerializer
    permission_classes = [DjangoModelPermissions]
