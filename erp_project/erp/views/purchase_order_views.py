"""
Purchase Order Frontend Views with Formset
Complete CRUD operations for Purchase Orders
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
from erp.models import PurchaseOrder, PurchaseOrderItem, Supplier, Product, Warehouse


class PurchaseOrderListView(LoginRequiredMixin, ListView):
    """List all purchase orders"""
    model = PurchaseOrder
    template_name = 'erp/frontend/purchase_order_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = PurchaseOrder.objects.select_related('supplier', 'branch').prefetch_related('items')
        
        # Search
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(order_number__icontains=search_query) |
                Q(supplier__name__icontains=search_query)
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
        context['status_choices'] = PurchaseOrder.STATUS_CHOICES
        return context


class PurchaseOrderDetailView(LoginRequiredMixin, DetailView):
    """View purchase order details"""
    model = PurchaseOrder
    template_name = 'erp/frontend/purchase_order_detail.html'
    context_object_name = 'order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('product').all()
        return context


class PurchaseOrderDeleteView(LoginRequiredMixin, DeleteView):
    """Delete purchase order"""
    model = PurchaseOrder
    success_url = reverse_lazy('erp:purchaseorder_list')
    
    def get(self, request, *args, **kwargs):
        return redirect('erp:purchaseorder_list')
    
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
            messages.success(request, f'Purchase Order "{order_number}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting order: {str(e)}')
        
        return redirect(self.success_url)


# Formset for Purchase Order Items
PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    fields=('product', 'quantity', 'unit_price'),
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


@login_required
def purchaseorder_create(request):
    """Create new purchase order with formset"""
    if request.method == 'POST':
        # Create empty order instance
        order = PurchaseOrder()
        
        # Get form data
        order.supplier_id = request.POST.get('supplier')
        order.branch_id = request.POST.get('branch') if request.POST.get('branch') else None
        order.order_date = request.POST.get('order_date')
        order.expected_date = request.POST.get('expected_date') if request.POST.get('expected_date') else None
        order.discount_amount = Decimal(request.POST.get('discount_amount', '0') or '0')
        order.tax_amount = Decimal(request.POST.get('tax_amount', '0') or '0')
        order.notes = request.POST.get('notes', '')
        order.status = request.POST.get('status', 'draft')
        
        # Save order first
        order.save()
        
        # Create formset with saved order
        formset = PurchaseOrderItemFormSet(request.POST, instance=order)
        
        if formset.is_valid():
            formset.save()
            order.calculate_totals()
            messages.success(request, f'Purchase Order "{order.order_number}" created successfully!')
            return redirect('erp:purchaseorder_detail', pk=order.pk)
        else:
            # Delete order if formset invalid
            order.delete()
            messages.error(request, 'Please correct the errors below.')
    else:
        formset = PurchaseOrderItemFormSet()
    
    context = {
        'formset': formset,
        'suppliers': Supplier.objects.filter(is_active=True).order_by('name'),
        'branches': Warehouse.objects.filter(is_active=True).order_by('name'),
        'products': Product.objects.filter(is_active=True).order_by('name'),
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'is_edit': False,
    }
    
    return render(request, 'erp/frontend/purchase_order_form.html', context)


@login_required
def purchaseorder_update(request, pk):
    """Update existing purchase order with formset"""
    order = get_object_or_404(PurchaseOrder, pk=pk)
    
    if request.method == 'POST':
        # Update order fields
        order.supplier_id = request.POST.get('supplier')
        order.branch_id = request.POST.get('branch') if request.POST.get('branch') else None
        order.order_date = request.POST.get('order_date')
        order.expected_date = request.POST.get('expected_date') if request.POST.get('expected_date') else None
        order.discount_amount = Decimal(request.POST.get('discount_amount', '0') or '0')
        order.tax_amount = Decimal(request.POST.get('tax_amount', '0') or '0')
        order.notes = request.POST.get('notes', '')
        order.status = request.POST.get('status', 'draft')
        
        order.save()
        
        # Process formset
        formset = PurchaseOrderItemFormSet(request.POST, instance=order)
        
        if formset.is_valid():
            formset.save()
            order.calculate_totals()
            messages.success(request, f'Purchase Order "{order.order_number}" updated successfully!')
            return redirect('erp:purchaseorder_detail', pk=order.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        formset = PurchaseOrderItemFormSet(instance=order)
    
    context = {
        'formset': formset,
        'order': order,
        'suppliers': Supplier.objects.filter(is_active=True).order_by('name'),
        'branches': Warehouse.objects.filter(is_active=True).order_by('name'),
        'products': Product.objects.filter(is_active=True).order_by('name'),
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'is_edit': True,
    }
    
    return render(request, 'erp/frontend/purchase_order_form.html', context)
