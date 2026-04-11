"""
ERP Mobile Product Views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from erp.models import Product, Category, Warehouse


class ProductListView(LoginRequiredMixin, View):
    template_name = 'erp/mobile_app/product_list.html'
    login_url = 'erp:erp-mobile-login'
    paginate_by = 20

    def get(self, request):
        # Get all active products
        queryset = Product.objects.filter(is_active=True)

        # Search functionality
        search = request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )

        # Ordering
        queryset = queryset.order_by('name')

        # Pagination
        paginator = Paginator(queryset, self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'products': page_obj,
            'search_query': search,
            'total_products': queryset.count(),
        }

        return render(request, self.template_name, context)


class ProductDetailView(LoginRequiredMixin, View):
    template_name = 'erp/mobile_app/product_detail.html'
    login_url = 'erp:erp-mobile-login'

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk, is_active=True)

        # Check if it's an AJAX request for modal
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return only the modal content
            return render(
                request, self.template_name, {'product': product, 'request': request}
            )

        # Regular page view
        context = {
            'product': product,
        }

        return render(request, self.template_name, context)


class ProductCreateView(LoginRequiredMixin, View):
    template_name = 'erp/mobile_app/product_form.html'
    login_url = 'erp:erp-mobile-login'

    def get(self, request):
        context = {
            'categories': Category.objects.filter(is_active=True).order_by('name'),
            'warehouses': Warehouse.objects.filter(is_active=True).order_by('name'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            product = Product(
                name=request.POST.get('name'),
                sku=request.POST.get('sku'),
                unit=request.POST.get('unit', 'PCS'),
                description=request.POST.get('description', ''),
                purchase_price=request.POST.get('purchase_price', 0),
                selling_price=request.POST.get('selling_price', 0),
                min_stock_level=request.POST.get('min_stock_level', 10),
                is_active=request.POST.get('is_active') == 'on',
            )

            # Set category if provided
            category_id = request.POST.get('category')
            if category_id:
                product.category_id = category_id

            # Set warehouse if provided
            warehouse_id = request.POST.get('default_warehouse')
            if warehouse_id:
                product.default_warehouse_id = warehouse_id

            product.save()
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('erp:erp-mobile-products')

        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
            context = {
                'categories': Category.objects.filter(is_active=True).order_by('name'),
                'warehouses': Warehouse.objects.filter(is_active=True).order_by('name'),
            }
            return render(request, self.template_name, context)


class ProductUpdateView(LoginRequiredMixin, View):
    template_name = 'erp/mobile_app/product_form.html'
    login_url = 'erp:erp-mobile-login'

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        context = {
            'product': product,
            'categories': Category.objects.filter(is_active=True).order_by('name'),
            'warehouses': Warehouse.objects.filter(is_active=True).order_by('name'),
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        try:
            product.name = request.POST.get('name')
            product.sku = request.POST.get('sku')
            product.unit = request.POST.get('unit', 'PCS')
            product.description = request.POST.get('description', '')
            product.purchase_price = request.POST.get('purchase_price', 0)
            product.selling_price = request.POST.get('selling_price', 0)
            product.min_stock_level = request.POST.get('min_stock_level', 10)
            product.is_active = request.POST.get('is_active') == 'on'

            # Update category
            category_id = request.POST.get('category')
            product.category_id = category_id if category_id else None

            # Update warehouse
            warehouse_id = request.POST.get('default_warehouse')
            product.default_warehouse_id = warehouse_id if warehouse_id else None

            product.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('erp:erp-mobile-products')

        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
            context = {
                'product': product,
                'categories': Category.objects.filter(is_active=True).order_by('name'),
                'warehouses': Warehouse.objects.filter(is_active=True).order_by('name'),
            }
            return render(request, self.template_name, context)


class ProductDeleteView(LoginRequiredMixin, View):
    login_url = 'erp:erp-mobile-login'

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product_name = product.name
        try:
            product.delete()
            messages.success(request, f'Product "{product_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting product: {str(e)}')
        return redirect('erp:erp-mobile-products')
