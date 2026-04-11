"""
ERP Mobile Sales Views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import json
from decimal import Decimal
from erp.models import SalesOrder, SalesOrderItem, Customer, SalesPerson, Product


class SalesOrderListView(LoginRequiredMixin, View):
    template_name = 'erp/mobile_app/sales_list.html'
    login_url = 'erp:erp-mobile-login'
    paginate_by = 20

    def get(self, request):
        # Get all sales orders
        queryset = SalesOrder.objects.select_related('customer').prefetch_related(
            'items'
        )

        # Search functionality
        search = request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search)
                | Q(customer__name__icontains=search)
                | Q(customer__phone__icontains=search)
            )

        # Ordering
        queryset = queryset.order_by('-order_date', '-created_at')

        # Pagination
        paginator = Paginator(queryset, self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'orders': page_obj,
            'search_query': search,
            'total_orders': queryset.count(),
        }

        return render(request, self.template_name, context)


class SalesOrderDetailView(LoginRequiredMixin, View):
    template_name = 'erp/mobile_app/sales_detail.html'
    login_url = 'erp:erp-mobile-login'

    def get(self, request, pk):
        order = get_object_or_404(
            SalesOrder.objects.select_related('customer').prefetch_related(
                'items__product'
            ),
            pk=pk,
        )

        # Check if it's an AJAX request for modal
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return only the modal content
            return render(
                request, self.template_name, {'order': order, 'request': request}
            )

        # Regular page view
        context = {
            'order': order,
        }

        return render(request, self.template_name, context)


class SalesOrderCreateView(LoginRequiredMixin, View):
    template_name = 'erp/mobile_app/sales_form.html'
    login_url = 'erp:erp-mobile-login'

    def get(self, request):
        # Get products as JSON for JavaScript
        products = Product.objects.filter(is_active=True).values(
            'id', 'name', 'sku', 'selling_price'
        )
        products_json = json.dumps(list(products), default=str)

        context = {
            'customers': Customer.objects.filter(is_active=True).order_by('name'),
            'salespersons': SalesPerson.objects.filter(is_active=True).order_by('name'),
            'products_json': products_json,
            'today': timezone.now().date(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            # Create sales order
            order = SalesOrder(
                order_date=request.POST.get('order_date'),
                customer_id=request.POST.get('customer'),
                status=request.POST.get('status', 'draft'),
                discount_amount=Decimal(request.POST.get('discount_amount', 0)),
                tax_rate=Decimal(request.POST.get('tax_rate', 0)),
                notes=request.POST.get('notes', ''),
            )

            # Set salesperson if provided
            salesperson_id = request.POST.get('salesperson')
            if salesperson_id:
                order.salesperson_id = salesperson_id

            order.save()

            # Create order items
            subtotal = Decimal('0.00')
            for key in request.POST:
                if key.startswith('items[') and key.endswith('][product]'):
                    # Extract item index
                    idx = key.split('[')[1].split(']')[0]
                    product_id = request.POST.get(f'items[{idx}][product]')
                    quantity = Decimal(request.POST.get(f'items[{idx}][quantity]', 0))
                    price = Decimal(request.POST.get(f'items[{idx}][price]', 0))

                    if product_id and quantity > 0:
                        line_total = quantity * price
                        SalesOrderItem.objects.create(
                            sales_order=order,
                            product_id=product_id,
                            quantity=quantity,
                            unit_price=price,
                            line_total=line_total,
                        )
                        subtotal += line_total

            # Calculate totals
            order.subtotal = subtotal
            tax_amount = (subtotal - order.discount_amount) * (
                order.tax_rate / Decimal('100')
            )
            order.tax_amount = tax_amount
            order.total_amount = subtotal - order.discount_amount + tax_amount
            order.save()

            messages.success(
                request, f'Sales Order "{order.order_number}" created successfully!'
            )
            return redirect('erp:erp-mobile-sales')

        except Exception as e:
            messages.error(request, f'Error creating sales order: {str(e)}')
            products = Product.objects.filter(is_active=True).values(
                'id', 'name', 'sku', 'selling_price'
            )
            products_json = json.dumps(list(products), default=str)
            context = {
                'customers': Customer.objects.filter(is_active=True).order_by('name'),
                'salespersons': SalesPerson.objects.filter(is_active=True).order_by(
                    'name'
                ),
                'products_json': products_json,
                'today': timezone.now().date(),
            }
            return render(request, self.template_name, context)


class SalesOrderUpdateView(LoginRequiredMixin, View):
    template_name = 'erp/mobile_app/sales_form.html'
    login_url = 'erp:erp-mobile-login'

    def get(self, request, pk):
        order = get_object_or_404(SalesOrder, pk=pk)
        products = Product.objects.filter(is_active=True).values(
            'id', 'name', 'sku', 'selling_price'
        )
        products_json = json.dumps(list(products), default=str)

        context = {
            'order': order,
            'customers': Customer.objects.filter(is_active=True).order_by('name'),
            'salespersons': SalesPerson.objects.filter(is_active=True).order_by('name'),
            'products_json': products_json,
            'today': timezone.now().date(),
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        order = get_object_or_404(SalesOrder, pk=pk)
        try:
            # Update order
            order.order_date = request.POST.get('order_date')
            order.customer_id = request.POST.get('customer')
            order.status = request.POST.get('status', 'draft')
            order.discount_amount = Decimal(request.POST.get('discount_amount', 0))
            order.tax_rate = Decimal(request.POST.get('tax_rate', 0))
            order.notes = request.POST.get('notes', '')

            # Update salesperson
            salesperson_id = request.POST.get('salesperson')
            order.salesperson_id = salesperson_id if salesperson_id else None

            # Delete existing items
            order.items.all().delete()

            # Create new items
            subtotal = Decimal('0.00')
            for key in request.POST:
                if key.startswith('items[') and key.endswith('][product]'):
                    idx = key.split('[')[1].split(']')[0]
                    product_id = request.POST.get(f'items[{idx}][product]')
                    quantity = Decimal(request.POST.get(f'items[{idx}][quantity]', 0))
                    price = Decimal(request.POST.get(f'items[{idx}][price]', 0))

                    if product_id and quantity > 0:
                        line_total = quantity * price
                        SalesOrderItem.objects.create(
                            sales_order=order,
                            product_id=product_id,
                            quantity=quantity,
                            unit_price=price,
                            line_total=line_total,
                        )
                        subtotal += line_total

            # Calculate totals
            order.subtotal = subtotal
            tax_amount = (subtotal - order.discount_amount) * (
                order.tax_rate / Decimal('100')
            )
            order.tax_amount = tax_amount
            order.total_amount = subtotal - order.discount_amount + tax_amount
            order.save()

            messages.success(
                request, f'Sales Order "{order.order_number}" updated successfully!'
            )
            return redirect('erp:erp-mobile-sales')

        except Exception as e:
            messages.error(request, f'Error updating sales order: {str(e)}')
            products = Product.objects.filter(is_active=True).values(
                'id', 'name', 'sku', 'selling_price'
            )
            products_json = json.dumps(list(products), default=str)
            context = {
                'order': order,
                'customers': Customer.objects.filter(is_active=True).order_by('name'),
                'salespersons': SalesPerson.objects.filter(is_active=True).order_by(
                    'name'
                ),
                'products_json': products_json,
                'today': timezone.now().date(),
            }
            return render(request, self.template_name, context)


class SalesOrderDeleteView(LoginRequiredMixin, View):
    login_url = 'erp:erp-mobile-login'

    def post(self, request, pk):
        order = get_object_or_404(SalesOrder, pk=pk)
        order_number = order.order_number
        try:
            order.delete()
            messages.success(
                request, f'Sales Order "{order_number}" deleted successfully!'
            )
        except Exception as e:
            messages.error(request, f'Error deleting sales order: {str(e)}')
        return redirect('erp:erp-mobile-sales')
