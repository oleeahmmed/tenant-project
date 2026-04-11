"""
Autocomplete API views for report filters
Fast and efficient autocomplete for large datasets
"""
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q

from ...models import Customer, SalesPerson, Product
from django.contrib.auth.models import User


class CustomerAutocompleteView(View):
    """Autocomplete API for customers"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        queryset = Customer.objects.filter(is_active=True)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(email__icontains=search) | 
                Q(phone__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        customers = queryset.only('id', 'name', 'email')[start:end]
        
        results = [
            {
                'id': customer.id,
                'text': f"{customer.name} ({customer.email or 'No email'})"
            }
            for customer in customers
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })


class SalespersonAutocompleteView(View):
    """Autocomplete API for salespersons"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        queryset = SalesPerson.objects.filter(is_active=True)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(email__icontains=search) | 
                Q(employee_id__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        salespersons = queryset.only('id', 'name', 'employee_id')[start:end]
        
        results = [
            {
                'id': sp.id,
                'text': f"{sp.name} ({sp.employee_id or 'No ID'})"
            }
            for sp in salespersons
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })


class ProductAutocompleteView(View):
    """Autocomplete API for products"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        queryset = Product.objects.filter(is_active=True)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(sku__icontains=search) | 
                Q(description__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        products = queryset.only('id', 'name', 'sku')[start:end]
        
        results = [
            {
                'id': product.id,
                'text': f"{product.name} ({product.sku})"
            }
            for product in products
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })



class CashierAutocompleteView(View):
    """Autocomplete API for cashiers (users)"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        queryset = User.objects.filter(is_active=True, is_staff=True)
        
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(first_name__icontains=search) | 
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        users = queryset.only('id', 'username', 'first_name', 'last_name', 'email')[start:end]
        
        results = [
            {
                'id': user.id,
                'text': f"{user.username} ({user.get_full_name() or user.email or 'No name'})"
            }
            for user in users
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })



class SupplierAutocompleteView(View):
    """Autocomplete API for suppliers"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        from ...models import Supplier
        queryset = Supplier.objects.filter(is_active=True)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(email__icontains=search) | 
                Q(phone__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        suppliers = queryset.only('id', 'name', 'email')[start:end]
        
        results = [
            {
                'id': supplier.id,
                'text': f"{supplier.name} ({supplier.email or 'No email'})"
            }
            for supplier in suppliers
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })


class AccountTypeAutocompleteView(View):
    """Autocomplete API for account types"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from ...models import AccountType
        
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        queryset = AccountType.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(type_category__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        account_types = queryset.only('id', 'name', 'type_category')[start:end]
        
        results = [
            {
                'id': at.id,
                'text': f"{at.name} ({at.type_category.title()})"
            }
            for at in account_types
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })


class AccountAutocompleteView(View):
    """Autocomplete API for chart of accounts"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from ...models import ChartOfAccounts
        
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        queryset = ChartOfAccounts.objects.filter(is_active=True).select_related('account_type')
        
        if search:
            queryset = queryset.filter(
                Q(account_code__icontains=search) | 
                Q(account_name__icontains=search) |
                Q(account_type__name__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        accounts = queryset.only('id', 'account_code', 'account_name', 'account_type__name')[start:end]
        
        results = [
            {
                'id': account.id,
                'text': f"{account.account_code} - {account.account_name}"
            }
            for account in accounts
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })

class WarehouseAutocompleteView(View):
    """Autocomplete API for warehouses"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from ...models import Warehouse
        
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        queryset = Warehouse.objects.filter(is_active=True)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(code__icontains=search) | 
                Q(city__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        warehouses = queryset.only('id', 'name', 'code')[start:end]
        
        results = [
            {
                'id': warehouse.id,
                'text': f"{warehouse.name} ({warehouse.code})"
            }
            for warehouse in warehouses
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })


class CategoryAutocompleteView(View):
    """Autocomplete API for categories"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from ...models import Category
        
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        queryset = Category.objects.filter(is_active=True)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        categories = queryset.only('id', 'name')[start:end]
        
        results = [
            {
                'id': category.id,
                'text': category.name
            }
            for category in categories
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })


class PaymentMethodAutocompleteView(View):
    """Autocomplete API for payment methods"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from ...models import PaymentMethod
        
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        queryset = PaymentMethod.objects.filter(is_active=True)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(method_type__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        payment_methods = queryset.only('id', 'name', 'method_type')[start:end]
        
        results = [
            {
                'id': pm.id,
                'text': f"{pm.name} ({pm.method_type})"
            }
            for pm in payment_methods
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })


class TaxRateAutocompleteView(View):
    """Autocomplete API for tax rates"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from ...models import TaxRate
        
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        queryset = TaxRate.objects.filter(is_active=True).select_related('tax_type')
        
        if search:
            queryset = queryset.filter(
                Q(tax_type__name__icontains=search) | 
                Q(rate__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        tax_rates = queryset.only('id', 'tax_type__name', 'rate')[start:end]
        
        results = [
            {
                'id': tr.id,
                'text': f"{tr.tax_type.name} ({tr.rate}%)"
            }
            for tr in tax_rates
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })


class CurrencyAutocompleteView(View):
    """Autocomplete API for currencies"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from ...models import Currency
        
        search = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        
        queryset = Currency.objects.filter(is_active=True)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(code__icontains=search) | 
                Q(symbol__icontains=search)
            )
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        currencies = queryset.only('id', 'name', 'code', 'symbol')[start:end]
        
        results = [
            {
                'id': currency.id,
                'text': f"{currency.name} ({currency.code}) {currency.symbol}"
            }
            for currency in currencies
        ]
        
        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })