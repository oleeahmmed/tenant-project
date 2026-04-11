"""
Sales Order Frontend Views with Formset
Complete CRUD operations for Sales Orders
"""
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.forms import inlineformset_factory
from erp.models import SalesOrder, SalesOrderItem, Customer, Product, SalesPerson, Warehouse


class SalesOrderListView(LoginRequiredMixin, ListView):
    """List all sales orders"""
    model = SalesOrder
    template_name = 'erp/frontend/sales_order_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = SalesOrder.objects.select_related('customer', 'salesperson', 'branch').prefetch_related('items')
        
        # Search
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(order_number__icontains=search_query) |
                Q(customer__name__icontains=search_query) |
                Q(job_reference__icontains=search_query)
            )
        
        # Status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-order_date', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['status_choices'] = SalesOrder.STATUS_CHOICES
        return context


class SalesOrderDetailView(LoginRequiredMixin, DetailView):
    """View sales order details"""
    model = SalesOrder
    template_name = 'erp/frontend/sales_order_detail.html'
    context_object_name = 'order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('product').all()
        return context


class SalesOrderDeleteView(LoginRequiredMixin, DeleteView):
    """Delete sales order"""
    model = SalesOrder
    success_url = reverse_lazy('erp:salesorder_list')
    
    def get(self, request, *args, **kwargs):
        return redirect('erp:salesorder_list')
    
    def post(self, request, *args, **kwargs):
        order = self.get_object()
        order_number = order.order_number
        
        # Only allow deletion of draft orders
        if order.status != 'draft':
            messages.error(request, f'Cannot delete {order.status} order. Only draft orders can be deleted.')
            return redirect(self.success_url)
        
        try:
            self.object = order
            self.object.delete()
            messages.success(request, f'Sales Order "{order_number}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting order: {str(e)}')
        
        return redirect(self.success_url)


# Formset for Sales Order Items
SalesOrderItemFormSet = inlineformset_factory(
    SalesOrder,
    SalesOrderItem,
    fields=('product', 'quantity', 'unit_price'),
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


@login_required
def salesorder_create(request):
    """Create new sales order with formset"""
    if request.method == 'POST':
        # Create empty order instance
        order = SalesOrder()
        
        # Get form data
        order.customer_id = request.POST.get('customer')
        order.salesperson_id = request.POST.get('salesperson') if request.POST.get('salesperson') else None
        order.branch_id = request.POST.get('branch') if request.POST.get('branch') else None
        order.order_date = request.POST.get('order_date')
        order.delivery_date = request.POST.get('delivery_date') if request.POST.get('delivery_date') else None
        order.job_reference = request.POST.get('job_reference', '')
        order.shipping_method = request.POST.get('shipping_method', 'Standard')
        order.delivery_terms = request.POST.get('delivery_terms', 'FOB')
        order.payment_terms = request.POST.get('payment_terms', 'Net 30')
        order.discount_amount = Decimal(request.POST.get('discount_amount', '0') or '0')
        order.tax_amount = Decimal(request.POST.get('tax_amount', '0') or '0')
        order.notes = request.POST.get('notes', '')
        order.status = request.POST.get('status', 'draft')
        
        # Save order first
        order.save()
        
        # Create formset with saved order
        formset = SalesOrderItemFormSet(request.POST, instance=order)
        
        if formset.is_valid():
            formset.save()
            order.calculate_totals()
            messages.success(request, f'Sales Order "{order.order_number}" created successfully!')
            return redirect('erp:salesorder_detail', pk=order.pk)
        else:
            # Delete order if formset invalid
            order.delete()
            messages.error(request, 'Please correct the errors below.')
    else:
        formset = SalesOrderItemFormSet()
    
    context = {
        'formset': formset,
        'customers': Customer.objects.filter(is_active=True).order_by('name'),
        'salespersons': SalesPerson.objects.filter(is_active=True).order_by('name'),
        'branches': Warehouse.objects.filter(is_active=True).order_by('name'),
        'products': Product.objects.filter(is_active=True).order_by('name'),
        'status_choices': SalesOrder.STATUS_CHOICES,
        'is_edit': False,
    }
    
    return render(request, 'erp/frontend/sales_order_form.html', context)


@login_required
def salesorder_update(request, pk):
    """Update existing sales order with formset"""
    order = get_object_or_404(SalesOrder, pk=pk)
    
    if request.method == 'POST':
        # Update order fields
        order.customer_id = request.POST.get('customer')
        order.salesperson_id = request.POST.get('salesperson') if request.POST.get('salesperson') else None
        order.branch_id = request.POST.get('branch') if request.POST.get('branch') else None
        order.order_date = request.POST.get('order_date')
        order.delivery_date = request.POST.get('delivery_date') if request.POST.get('delivery_date') else None
        order.job_reference = request.POST.get('job_reference', '')
        order.shipping_method = request.POST.get('shipping_method', 'Standard')
        order.delivery_terms = request.POST.get('delivery_terms', 'FOB')
        order.payment_terms = request.POST.get('payment_terms', 'Net 30')
        order.discount_amount = Decimal(request.POST.get('discount_amount', '0') or '0')
        order.tax_amount = Decimal(request.POST.get('tax_amount', '0') or '0')
        order.notes = request.POST.get('notes', '')
        order.status = request.POST.get('status', 'draft')
        
        order.save()
        
        # Process formset
        formset = SalesOrderItemFormSet(request.POST, instance=order)
        
        if formset.is_valid():
            formset.save()
            order.calculate_totals()
            messages.success(request, f'Sales Order "{order.order_number}" updated successfully!')
            return redirect('erp:salesorder_detail', pk=order.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        formset = SalesOrderItemFormSet(instance=order)
    
    context = {
        'formset': formset,
        'order': order,
        'customers': Customer.objects.filter(is_active=True).order_by('name'),
        'salespersons': SalesPerson.objects.filter(is_active=True).order_by('name'),
        'branches': Warehouse.objects.filter(is_active=True).order_by('name'),
        'products': Product.objects.filter(is_active=True).order_by('name'),
        'status_choices': SalesOrder.STATUS_CHOICES,
        'is_edit': True,
    }
    
    return render(request, 'erp/frontend/sales_order_form.html', context)
