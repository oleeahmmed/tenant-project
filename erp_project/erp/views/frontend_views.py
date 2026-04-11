"""
Frontend Views for ERP Module
CRUD Operations for Category, Warehouse, Product, Company, Customer, Supplier - Class-Based Views
"""
from decimal import Decimal
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from erp.models import Category, Warehouse, Product, Company, Customer, Supplier, SalesPerson, PaymentMethod, UnitOfMeasure


class CategoryListView(LoginRequiredMixin, ListView):
    """
    Display list of all categories with search and pagination
    """
    model = Category
    template_name = 'erp/frontend/category_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12  # 12 items per page (3x4 grid)
    
    def get_queryset(self):
        queryset = Category.objects.all()
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        # Get base queryset for stats
        queryset = Category.objects.all()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Calculate stats
        context['search_query'] = search_query
        context['status_filter'] = status_filter
        context['total_categories'] = queryset.count()
        context['active_count'] = queryset.filter(is_active=True).count()
        context['inactive_count'] = queryset.filter(is_active=False).count()
        
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new category
    """
    model = Category
    template_name = 'erp/frontend/category_form.html'
    fields = ['name', 'description', 'is_active']
    success_url = reverse_lazy('erp:category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context
    
    def form_valid(self, form):
        # Handle checkbox value
        is_active = self.request.POST.get('is_active', 'off')
        form.instance.is_active = (is_active == 'on')
        
        messages.success(self.request, f'Category "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing category
    """
    model = Category
    template_name = 'erp/frontend/category_form.html'
    fields = ['name', 'description', 'is_active']
    success_url = reverse_lazy('erp:category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        context['category'] = self.object
        return context
    
    def form_valid(self, form):
        # Handle checkbox value
        is_active = self.request.POST.get('is_active', 'off')
        form.instance.is_active = (is_active == 'on')
        
        messages.success(self.request, f'Category "{form.instance.name}" updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a category
    """
    model = Category
    success_url = reverse_lazy('erp:category_list')
    
    def get(self, request, *args, **kwargs):
        # Redirect GET requests to list page
        return redirect('erp:category_list')
    
    def post(self, request, *args, **kwargs):
        category = self.get_object()
        category_name = category.name
        
        try:
            self.object = category
            self.object.delete()
            messages.success(request, f'Category "{category_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting category: {str(e)}')
        
        return redirect(self.success_url)


class CategoryDetailView(LoginRequiredMixin, DetailView):
    """
    View category details
    """
    model = Category
    template_name = 'erp/frontend/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get products in this category
        products = self.object.products.all()[:10]  # First 10 products
        
        context['products'] = products
        context['total_products'] = self.object.products.count()
        
        return context



# ==================== WAREHOUSE CRUD ====================

class WarehouseListView(LoginRequiredMixin, ListView):
    """
    Display list of all warehouses with search and pagination
    """
    model = Warehouse
    template_name = 'erp/frontend/warehouse_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Warehouse.objects.all()
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(code__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(manager__icontains=search_query)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        queryset = Warehouse.objects.all()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(code__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(manager__icontains=search_query)
            )
        
        context['search_query'] = search_query
        context['status_filter'] = status_filter
        context['total_warehouses'] = queryset.count()
        context['active_count'] = queryset.filter(is_active=True).count()
        context['inactive_count'] = queryset.filter(is_active=False).count()
        
        return context


class WarehouseCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new warehouse
    """
    model = Warehouse
    template_name = 'erp/frontend/warehouse_form.html'
    fields = ['name', 'code', 'address', 'city', 'country', 'phone', 'manager', 'is_active']
    success_url = reverse_lazy('erp:warehouse_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context
    
    def form_valid(self, form):
        is_active = self.request.POST.get('is_active', 'off')
        form.instance.is_active = (is_active == 'on')
        
        messages.success(self.request, f'Warehouse "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class WarehouseUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing warehouse
    """
    model = Warehouse
    template_name = 'erp/frontend/warehouse_form.html'
    fields = ['name', 'code', 'address', 'city', 'country', 'phone', 'manager', 'is_active']
    success_url = reverse_lazy('erp:warehouse_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        context['warehouse'] = self.object
        return context
    
    def form_valid(self, form):
        is_active = self.request.POST.get('is_active', 'off')
        form.instance.is_active = (is_active == 'on')
        
        messages.success(self.request, f'Warehouse "{form.instance.name}" updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class WarehouseDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a warehouse
    """
    model = Warehouse
    success_url = reverse_lazy('erp:warehouse_list')
    
    def get(self, request, *args, **kwargs):
        return redirect('erp:warehouse_list')
    
    def post(self, request, *args, **kwargs):
        warehouse = self.get_object()
        warehouse_name = warehouse.name
        
        try:
            self.object = warehouse
            self.object.delete()
            messages.success(request, f'Warehouse "{warehouse_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting warehouse: {str(e)}')
        
        return redirect(self.success_url)


class WarehouseDetailView(LoginRequiredMixin, DetailView):
    """
    View warehouse details
    """
    model = Warehouse
    template_name = 'erp/frontend/warehouse_detail.html'
    context_object_name = 'warehouse'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get products in this warehouse
        products = self.object.default_products.all()[:10]
        
        context['products'] = products
        context['total_products'] = self.object.default_products.count()
        
        return context


# ==================== PRODUCT CRUD ====================

class ProductListView(LoginRequiredMixin, ListView):
    """
    Display list of all products with search and pagination
    """
    model = Product
    template_name = 'erp/frontend/product_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'default_warehouse')
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Apply category filter
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(sku__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        category_id = self.request.GET.get('category', '')
        
        queryset = Product.objects.all()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(sku__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        context['search_query'] = search_query
        context['status_filter'] = status_filter
        context['category_id'] = category_id
        context['categories'] = Category.objects.filter(is_active=True)
        context['total_products'] = queryset.count()
        context['active_count'] = queryset.filter(is_active=True).count()
        context['inactive_count'] = queryset.filter(is_active=False).count()
        
        return context


class ProductCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new product
    """
    model = Product
    template_name = 'erp/frontend/product_form.html'
    fields = ['name', 'sku', 'category', 'description', 'unit', 'default_warehouse', 'default_bom', 'purchase_price', 'selling_price', 'min_stock_level', 'is_active']
    success_url = reverse_lazy('erp:product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context
    
    def form_valid(self, form):
        is_active = self.request.POST.get('is_active', 'off')
        form.instance.is_active = (is_active == 'on')
        
        messages.success(self.request, f'Product "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing product
    """
    model = Product
    template_name = 'erp/frontend/product_form.html'
    fields = ['name', 'sku', 'category', 'description', 'unit', 'default_warehouse', 'default_bom', 'purchase_price', 'selling_price', 'min_stock_level', 'is_active']
    success_url = reverse_lazy('erp:product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        context['product'] = self.object
        return context
    
    def form_valid(self, form):
        is_active = self.request.POST.get('is_active', 'off')
        form.instance.is_active = (is_active == 'on')
        
        messages.success(self.request, f'Product "{form.instance.name}" updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a product
    """
    model = Product
    success_url = reverse_lazy('erp:product_list')
    
    def get(self, request, *args, **kwargs):
        return redirect('erp:product_list')
    
    def post(self, request, *args, **kwargs):
        product = self.get_object()
        product_name = product.name
        
        try:
            self.object = product
            self.object.delete()
            messages.success(request, f'Product "{product_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting product: {str(e)}')
        
        return redirect(self.success_url)


class ProductDetailView(LoginRequiredMixin, DetailView):
    """
    View product details
    """
    model = Product
    template_name = 'erp/frontend/product_detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get warehouse stocks
        warehouse_stocks = self.object.warehouse_stocks.select_related('warehouse').all()
        
        context['warehouse_stocks'] = warehouse_stocks
        context['total_stock'] = self.object.current_stock
        
        return context


# ==================== COMPANY CRUD ====================

class CompanyListView(LoginRequiredMixin, ListView):
    """
    Display list of all companies with search and pagination
    """
    model = Company
    template_name = 'erp/frontend/company_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Company.objects.all()
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(city__icontains=search_query) |
                Q(country__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        
        queryset = Company.objects.all()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(city__icontains=search_query) |
                Q(country__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        context['search_query'] = search_query
        context['total_companies'] = queryset.count()
        
        return context


class CompanyCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new company
    """
    model = Company
    template_name = 'erp/frontend/company_form.html'
    fields = ['name', 'logo', 'address', 'city', 'country', 'phone', 'email', 'website', 'tax_number']
    success_url = reverse_lazy('erp:company_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Company "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing company
    """
    model = Company
    template_name = 'erp/frontend/company_form.html'
    fields = ['name', 'logo', 'address', 'city', 'country', 'phone', 'email', 'website', 'tax_number']
    success_url = reverse_lazy('erp:company_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        context['company'] = self.object
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Company "{form.instance.name}" updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class CompanyDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a company
    """
    model = Company
    success_url = reverse_lazy('erp:company_list')
    
    def get(self, request, *args, **kwargs):
        return redirect('erp:company_list')
    
    def post(self, request, *args, **kwargs):
        company = self.get_object()
        company_name = company.name
        
        try:
            self.object = company
            self.object.delete()
            messages.success(request, f'Company "{company_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting company: {str(e)}')
        
        return redirect(self.success_url)


class CompanyDetailView(LoginRequiredMixin, DetailView):
    """
    View company details
    """
    model = Company
    template_name = 'erp/frontend/company_detail.html'
    context_object_name = 'company'



# ==================== CUSTOMER CRUD ====================

class CustomerListView(LoginRequiredMixin, ListView):
    """
    Display list of all customers with search and pagination
    """
    model = Customer
    template_name = 'erp/frontend/customer_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Customer.objects.all()
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(city__icontains=search_query)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        queryset = Customer.objects.all()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(city__icontains=search_query)
            )
        
        context['search_query'] = search_query
        context['status_filter'] = status_filter
        context['total_customers'] = queryset.count()
        context['active_count'] = queryset.filter(is_active=True).count()
        context['inactive_count'] = queryset.filter(is_active=False).count()
        
        return context


class CustomerCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new customer
    """
    model = Customer
    template_name = 'erp/frontend/customer_form.html'
    fields = ['name', 'email', 'phone', 'address', 'city', 'country', 'tax_number', 'credit_limit', 'is_active']
    success_url = reverse_lazy('erp:customer_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context
    
    def form_valid(self, form):
        is_active = self.request.POST.get('is_active', 'off')
        form.instance.is_active = (is_active == 'on')
        
        messages.success(self.request, f'Customer "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing customer
    """
    model = Customer
    template_name = 'erp/frontend/customer_form.html'
    fields = ['name', 'email', 'phone', 'address', 'city', 'country', 'tax_number', 'credit_limit', 'is_active']
    success_url = reverse_lazy('erp:customer_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        context['customer'] = self.object
        return context
    
    def form_valid(self, form):
        is_active = self.request.POST.get('is_active', 'off')
        form.instance.is_active = (is_active == 'on')
        
        messages.success(self.request, f'Customer "{form.instance.name}" updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a customer
    """
    model = Customer
    success_url = reverse_lazy('erp:customer_list')
    
    def get(self, request, *args, **kwargs):
        return redirect('erp:customer_list')
    
    def post(self, request, *args, **kwargs):
        customer = self.get_object()
        customer_name = customer.name
        
        try:
            self.object = customer
            self.object.delete()
            messages.success(request, f'Customer "{customer_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting customer: {str(e)}')
        
        return redirect(self.success_url)


class CustomerDetailView(LoginRequiredMixin, DetailView):
    """
    View customer details
    """
    model = Customer
    template_name = 'erp/frontend/customer_detail.html'
    context_object_name = 'customer'


# ==================== SUPPLIER CRUD ====================

class SupplierListView(LoginRequiredMixin, ListView):
    """
    Display list of all suppliers with search and pagination
    """
    model = Supplier
    template_name = 'erp/frontend/supplier_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Supplier.objects.all()
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(city__icontains=search_query)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        queryset = Supplier.objects.all()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(city__icontains=search_query)
            )
        
        context['search_query'] = search_query
        context['status_filter'] = status_filter
        context['total_suppliers'] = queryset.count()
        context['active_count'] = queryset.filter(is_active=True).count()
        context['inactive_count'] = queryset.filter(is_active=False).count()
        
        return context


class SupplierCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new supplier
    """
    model = Supplier
    template_name = 'erp/frontend/supplier_form.html'
    fields = ['name', 'email', 'phone', 'address', 'city', 'country', 'tax_number', 'is_active']
    success_url = reverse_lazy('erp:supplier_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context
    
    def form_valid(self, form):
        is_active = self.request.POST.get('is_active', 'off')
        form.instance.is_active = (is_active == 'on')
        
        messages.success(self.request, f'Supplier "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing supplier
    """
    model = Supplier
    template_name = 'erp/frontend/supplier_form.html'
    fields = ['name', 'email', 'phone', 'address', 'city', 'country', 'tax_number', 'is_active']
    success_url = reverse_lazy('erp:supplier_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        context['supplier'] = self.object
        return context
    
    def form_valid(self, form):
        is_active = self.request.POST.get('is_active', 'off')
        form.instance.is_active = (is_active == 'on')
        
        messages.success(self.request, f'Supplier "{form.instance.name}" updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a supplier
    """
    model = Supplier
    success_url = reverse_lazy('erp:supplier_list')
    
    def get(self, request, *args, **kwargs):
        return redirect('erp:supplier_list')
    
    def post(self, request, *args, **kwargs):
        supplier = self.get_object()
        supplier_name = supplier.name
        
        try:
            self.object = supplier
            self.object.delete()
            messages.success(request, f'Supplier "{supplier_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting supplier: {str(e)}')
        
        return redirect(self.success_url)


class SupplierDetailView(LoginRequiredMixin, DetailView):
    """
    View supplier details
    """
    model = Supplier
    template_name = 'erp/frontend/supplier_detail.html'
    context_object_name = 'supplier'


# ==================== SALESPERSON CRUD ====================

class SalesPersonListView(LoginRequiredMixin, ListView):
    """
    Display list of all sales persons with search and pagination
    """
    model = SalesPerson
    template_name = 'erp/frontend/salesperson_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = SalesPerson.objects.all()
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(employee_id__icontains=search_query)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        queryset = SalesPerson.objects.all()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(employee_id__icontains=search_query)
            )
        
        context['search_query'] = search_query
        context['status_filter'] = status_filter
        context['total_salespersons'] = queryset.count()
        context['active_count'] = queryset.filter(is_active=True).count()
        context['inactive_count'] = queryset.filter(is_active=False).count()
        
        return context


class SalesPersonCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new sales person
    """
    model = SalesPerson
    template_name = 'erp/frontend/salesperson_form.html'
    fields = ['name', 'email', 'phone', 'employee_id', 'commission_rate', 'is_active']
    success_url = reverse_lazy('erp:salesperson_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create'
        context['button_text'] = 'Create'
        return context
    
    def form_valid(self, form):
        # Handle boolean fields
        is_active = self.request.POST.get('is_active', 'False')
        form.instance.is_active = (is_active == 'True')
        
        # Handle commission_rate - set default if empty
        commission_rate = self.request.POST.get('commission_rate', '')
        if not commission_rate or commission_rate.strip() == '':
            form.instance.commission_rate = Decimal('0.00')
        
        response = super().form_valid(form)
        messages.success(self.request, f'Sales Person "{self.object.name}" created successfully!')
        return response
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class SalesPersonUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update a sales person
    """
    model = SalesPerson
    template_name = 'erp/frontend/salesperson_form.html'
    fields = ['name', 'email', 'phone', 'employee_id', 'commission_rate', 'is_active']
    success_url = reverse_lazy('erp:salesperson_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update'
        context['button_text'] = 'Update'
        return context
    
    def form_valid(self, form):
        # Handle boolean fields
        is_active = self.request.POST.get('is_active', 'False')
        form.instance.is_active = (is_active == 'True')
        
        # Handle commission_rate - set default if empty
        commission_rate = self.request.POST.get('commission_rate', '')
        if not commission_rate or commission_rate.strip() == '':
            form.instance.commission_rate = Decimal('0.00')
        
        response = super().form_valid(form)
        messages.success(self.request, f'Sales Person "{self.object.name}" updated successfully!')
        return response
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class SalesPersonDetailView(LoginRequiredMixin, DetailView):
    """
    Display details of a sales person
    """
    model = SalesPerson
    template_name = 'erp/frontend/salesperson_detail.html'
    context_object_name = 'salesperson'


class SalesPersonDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a sales person
    """
    model = SalesPerson
    success_url = reverse_lazy('erp:salesperson_list')
    
    def get(self, request, *args, **kwargs):
        return redirect('erp:salesperson_list')
    
    def post(self, request, *args, **kwargs):
        salesperson = self.get_object()
        salesperson_name = salesperson.name
        
        try:
            self.object = salesperson
            self.object.delete()
            messages.success(request, f'Sales Person "{salesperson_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting sales person: {str(e)}')
        
        return redirect(self.success_url)


# ==================== PAYMENT METHOD CRUD ====================

class PaymentMethodListView(LoginRequiredMixin, ListView):
    """
    Display list of all payment methods with search and pagination
    """
    model = PaymentMethod
    template_name = 'erp/frontend/paymentmethod_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = PaymentMethod.objects.all()
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(code__icontains=search_query) |
                Q(account_name__icontains=search_query)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        queryset = PaymentMethod.objects.all()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(code__icontains=search_query) |
                Q(account_name__icontains=search_query)
            )
        
        context['search_query'] = search_query
        context['status_filter'] = status_filter
        context['total_methods'] = queryset.count()
        context['active_count'] = queryset.filter(is_active=True).count()
        context['inactive_count'] = queryset.filter(is_active=False).count()
        
        return context


class PaymentMethodCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new payment method
    """
    model = PaymentMethod
    template_name = 'erp/frontend/paymentmethod_form.html'
    fields = ['name', 'code', 'payment_type', 'account_number', 'account_name', 'is_active']
    success_url = reverse_lazy('erp:paymentmethod_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create'
        context['button_text'] = 'Create'
        return context
    
    def form_valid(self, form):
        # Handle boolean fields
        is_active = self.request.POST.get('is_active', 'False')
        form.instance.is_active = (is_active == 'True')
        
        response = super().form_valid(form)
        messages.success(self.request, f'Payment Method "{self.object.name}" created successfully!')
        return response
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class PaymentMethodUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update a payment method
    """
    model = PaymentMethod
    template_name = 'erp/frontend/paymentmethod_form.html'
    fields = ['name', 'code', 'payment_type', 'account_number', 'account_name', 'is_active']
    success_url = reverse_lazy('erp:paymentmethod_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update'
        context['button_text'] = 'Update'
        return context
    
    def form_valid(self, form):
        # Handle boolean fields
        is_active = self.request.POST.get('is_active', 'False')
        form.instance.is_active = (is_active == 'True')
        
        response = super().form_valid(form)
        messages.success(self.request, f'Payment Method "{self.object.name}" updated successfully!')
        return response
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class PaymentMethodDetailView(LoginRequiredMixin, DetailView):
    """
    Display details of a payment method
    """
    model = PaymentMethod
    template_name = 'erp/frontend/paymentmethod_detail.html'
    context_object_name = 'paymentmethod'


class PaymentMethodDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a payment method
    """
    model = PaymentMethod
    success_url = reverse_lazy('erp:paymentmethod_list')
    
    def get(self, request, *args, **kwargs):
        return redirect('erp:paymentmethod_list')
    
    def post(self, request, *args, **kwargs):
        paymentmethod = self.get_object()
        paymentmethod_name = paymentmethod.name
        
        try:
            self.object = paymentmethod
            self.object.delete()
            messages.success(request, f'Payment Method "{paymentmethod_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting payment method: {str(e)}')
        
        return redirect(self.success_url)


# ==================== UNIT OF MEASURE CRUD ====================

class UnitOfMeasureListView(LoginRequiredMixin, ListView):
    """
    Display list of all units of measure with search and pagination
    """
    model = UnitOfMeasure
    template_name = 'erp/frontend/unitofmeasure_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = UnitOfMeasure.objects.all()
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(code__icontains=search_query) |
                Q(uom_type__icontains=search_query)
            )
        
        return queryset.order_by('uom_type', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        queryset = UnitOfMeasure.objects.all()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(code__icontains=search_query) |
                Q(uom_type__icontains=search_query)
            )
        
        context['search_query'] = search_query
        context['status_filter'] = status_filter
        context['total_units'] = queryset.count()
        context['active_count'] = queryset.filter(is_active=True).count()
        context['inactive_count'] = queryset.filter(is_active=False).count()
        
        return context


class UnitOfMeasureCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new unit of measure
    """
    model = UnitOfMeasure
    template_name = 'erp/frontend/unitofmeasure_form.html'
    fields = ['name', 'code', 'uom_type', 'is_base_unit', 'is_active']
    success_url = reverse_lazy('erp:unitofmeasure_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create'
        context['button_text'] = 'Create'
        return context
    
    def form_valid(self, form):
        # Handle boolean fields
        is_active = self.request.POST.get('is_active', 'False')
        is_base_unit = self.request.POST.get('is_base_unit', 'False')
        form.instance.is_active = (is_active == 'True')
        form.instance.is_base_unit = (is_base_unit == 'True')
        
        response = super().form_valid(form)
        messages.success(self.request, f'Unit of Measure "{self.object.name}" created successfully!')
        return response
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class UnitOfMeasureUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update a unit of measure
    """
    model = UnitOfMeasure
    template_name = 'erp/frontend/unitofmeasure_form.html'
    fields = ['name', 'code', 'uom_type', 'is_base_unit', 'is_active']
    success_url = reverse_lazy('erp:unitofmeasure_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update'
        context['button_text'] = 'Update'
        return context
    
    def form_valid(self, form):
        # Handle boolean fields
        is_active = self.request.POST.get('is_active', 'False')
        is_base_unit = self.request.POST.get('is_base_unit', 'False')
        form.instance.is_active = (is_active == 'True')
        form.instance.is_base_unit = (is_base_unit == 'True')
        
        response = super().form_valid(form)
        messages.success(self.request, f'Unit of Measure "{self.object.name}" updated successfully!')
        return response
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class UnitOfMeasureDetailView(LoginRequiredMixin, DetailView):
    """
    Display details of a unit of measure
    """
    model = UnitOfMeasure
    template_name = 'erp/frontend/unitofmeasure_detail.html'
    context_object_name = 'unitofmeasure'


class UnitOfMeasureDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a unit of measure
    """
    model = UnitOfMeasure
    success_url = reverse_lazy('erp:unitofmeasure_list')
    
    def get(self, request, *args, **kwargs):
        return redirect('erp:unitofmeasure_list')
    
    def post(self, request, *args, **kwargs):
        unitofmeasure = self.get_object()
        unitofmeasure_name = unitofmeasure.name
        
        try:
            self.object = unitofmeasure
            self.object.delete()
            messages.success(request, f'Unit of Measure "{unitofmeasure_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting unit of measure: {str(e)}')
        
        return redirect(self.success_url)
