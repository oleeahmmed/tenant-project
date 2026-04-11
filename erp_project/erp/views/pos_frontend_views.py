"""
POS Frontend Views for QuickSale
Professional Point of Sale System with CRUD Operations
"""
from decimal import Decimal
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from erp.models import QuickSale, QuickSaleItem, Product, Customer, PaymentMethod, Warehouse, ProductVariant, ShippingArea


class QuickSaleListView(LoginRequiredMixin, ListView):
    """
    Display list of all quick sales with search and pagination
    """
    model = QuickSale
    template_name = 'erp/frontend/pos/quicksale_list.html'
    context_object_name = 'page_obj'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = QuickSale.objects.select_related('user', 'customer', 'branch', 'payment_method').prefetch_related('items')
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(sale_number__icontains=search_query) | 
                Q(customer_name__icontains=search_query) |
                Q(customer_phone__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        queryset = QuickSale.objects.all()
        if search_query:
            queryset = queryset.filter(
                Q(sale_number__icontains=search_query) | 
                Q(customer_name__icontains=search_query) |
                Q(customer_phone__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )
        
        context['search_query'] = search_query
        context['status_filter'] = status_filter
        context['total_sales'] = queryset.count()
        context['completed_count'] = queryset.filter(status='completed').count()
        context['draft_count'] = queryset.filter(status='draft').count()
        context['cancelled_count'] = queryset.filter(status='cancelled').count()
        context['refunded_count'] = queryset.filter(status='refunded').count()
        
        # Calculate total revenue
        context['total_revenue'] = queryset.filter(status='completed').aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        return context


class QuickSaleDetailView(LoginRequiredMixin, DetailView):
    """
    View quick sale details
    """
    model = QuickSale
    template_name = 'erp/frontend/pos/quicksale_detail.html'
    context_object_name = 'sale'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get sale items
        items = self.object.items.select_related('product', 'variant').all()
        
        context['items'] = items
        context['total_items'] = items.count()
        context['total_quantity'] = sum(item.quantity for item in items)
        
        return context


class QuickSaleDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a quick sale
    """
    model = QuickSale
    success_url = reverse_lazy('erp:quicksale_list')
    
    def get(self, request, *args, **kwargs):
        return redirect('erp:quicksale_list')
    
    def post(self, request, *args, **kwargs):
        sale = self.get_object()
        sale_number = sale.sale_number
        
        # Only allow deletion of draft or cancelled sales
        if sale.status in ['completed', 'refunded']:
            messages.error(request, f'Cannot delete {sale.status} sale. Please cancel it first.')
            return redirect(self.success_url)
        
        try:
            self.object = sale
            self.object.delete()
            messages.success(request, f'Sale "{sale_number}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting sale: {str(e)}')
        
        return redirect(self.success_url)


@login_required
def pos_entry_view(request):
    """
    Professional POS Entry Interface
    Modern retail POS system for quick sales
    """
    from erp.models import Category, POSSession
    
    # Get active products with stock
    products = Product.objects.filter(is_active=True).select_related('category', 'default_warehouse')
    
    # Get categories
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    # Get customers
    customers = Customer.objects.filter(is_active=True).order_by('name')
    
    # Get payment methods
    payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('name')
    
    # Get shipping areas
    shipping_areas = ShippingArea.objects.filter(is_active=True).order_by('area_name')
    
    # Get user's default warehouse
    default_warehouse = None
    try:
        if hasattr(request.user, 'profile') and request.user.profile.branch:
            default_warehouse = request.user.profile.branch
    except:
        pass
    
    # Get open POS session for current user
    open_session = None
    try:
        open_session = POSSession.objects.filter(
            cashier=request.user,
            status='open'
        ).first()
    except:
        pass
    
    context = {
        'products': products,
        'categories': categories,
        'customers': customers,
        'payment_methods': payment_methods,
        'shipping_areas': shipping_areas,
        'default_warehouse': default_warehouse,
        'open_session': open_session,
        'is_edit_mode': False,
    }
    
    return render(request, 'erp/frontend/pos/quicksale_pos.html', context)


@login_required
@require_http_methods(["POST"])
def pos_create_sale(request):
    """
    Create a new quick sale from POS
    """
    try:
        import json
        data = json.loads(request.body)
        
        # Create QuickSale
        sale = QuickSale()
        sale.user = request.user
        
        # Customer info
        customer_id = data.get('customer_id')
        if customer_id:
            sale.customer_id = customer_id
        sale.customer_name = data.get('customer_name', '')
        sale.customer_phone = data.get('customer_phone', '')
        
        # Get user's branch if not provided
        if hasattr(request.user, 'profile') and request.user.profile.branch:
            sale.branch = request.user.profile.branch
        
        # Amounts - match template field names
        sale.subtotal = Decimal(str(data.get('subtotal', 0)))
        sale.discount_amount = Decimal(str(data.get('discount', 0)))
        
        # Calculate tax from subtotal and discount
        subtotal_after_discount = sale.subtotal - sale.discount_amount
        # Assuming VAT is included in total, we'll calculate it
        total = Decimal(str(data.get('total', 0)))
        sale.tax_amount = total - subtotal_after_discount
        sale.tax_percentage = Decimal('0.00')  # Can be calculated if needed
        
        # Shipping - get from shipping area if selected
        shipping_area_id = data.get('shipping_area_id')
        if shipping_area_id:
            try:
                shipping_area = ShippingArea.objects.get(id=shipping_area_id)
                sale.shipping_area = shipping_area
                sale.shipping_charge = shipping_area.shipping_charge
            except ShippingArea.DoesNotExist:
                sale.shipping_charge = Decimal('0.00')
        else:
            sale.shipping_charge = Decimal('0.00')
        
        sale.total_amount = total
        
        # Payment
        payment_method_id = data.get('payment_method_id')
        if payment_method_id:
            sale.payment_method_id = payment_method_id
        sale.amount_received = Decimal(str(data.get('amount_received', 0)))
        
        # Calculate change and due
        change = Decimal(str(data.get('change', 0)))
        if change > 0:
            sale.change_amount = change
            sale.due_amount = Decimal('0.00')
        else:
            sale.change_amount = Decimal('0.00')
            # Due is when amount received is less than total
            if sale.amount_received < sale.total_amount:
                sale.due_amount = sale.total_amount - sale.amount_received
            else:
                sale.due_amount = Decimal('0.00')
        
        # Session
        session_id = data.get('session_id')
        if session_id:
            try:
                from erp.models import POSSession
                session = POSSession.objects.get(id=session_id, status='open')
                sale.pos_session = session
            except:
                pass
        
        sale.status = 'completed'  # Mark as completed by default
        sale.notes = data.get('notes', '')
        
        sale.save()
        
        # Create sale items
        items = data.get('items', [])
        for item_data in items:
            item = QuickSaleItem()
            item.quick_sale = sale
            item.product_id = item_data['product_id']
            
            variant_id = item_data.get('variant_id')
            if variant_id:
                item.variant_id = variant_id
            
            item.quantity = Decimal(str(item_data['quantity']))
            item.unit_price = Decimal(str(item_data['unit_price']))
            item.discount_amount = Decimal('0.00')
            item.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Sale {sale.sale_number} created successfully!',
            'sale_id': sale.id,
            'sale_number': sale.sale_number
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Error creating sale: {str(e)}'
        }, status=400)


@login_required
@require_http_methods(["GET"])
def pos_search_product(request):
    """
    Search products for POS
    """
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'products': []})
    
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query),
        is_active=True
    ).select_related('category')[:20]
    
    results = []
    for product in products:
        results.append({
            'id': str(product.id),
            'name': product.name,
            'sku': product.sku or '',
            'selling_price': str(product.selling_price),
            'stock': str(product.current_stock),
            'category': product.category.name if product.category else ''
        })
    
    return JsonResponse({'products': results})


@login_required
@require_http_methods(["GET"])
def pos_get_product(request, product_id):
    """
    Get product details for POS
    """
    try:
        product = Product.objects.select_related('category').get(id=product_id, is_active=True)
        
        # Get variants if available
        variants = []
        if hasattr(product, 'variants'):
            for variant in product.variants.filter(is_active=True):
                variants.append({
                    'id': variant.id,
                    'name': str(variant),
                    'price': str(variant.effective_selling_price),
                    'stock': str(variant.current_stock)
                })
        
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'price': str(product.selling_price),
                'stock': str(product.current_stock),
                'category': product.category.name if product.category else '',
                'variants': variants
            }
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        }, status=404)


@login_required
@require_http_methods(["POST"])
def pos_session_management(request):
    """
    Manage POS sessions (open/close)
    """
    from erp.models import POSSession
    import json
    
    try:
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'open':
            # Check if user already has an open session
            existing = POSSession.objects.filter(
                cashier=request.user,
                status='open'
            ).first()
            
            if existing:
                return JsonResponse({
                    'success': False,
                    'error': 'You already have an open session'
                }, status=400)
            
            # Create new session
            session = POSSession()
            session.cashier = request.user
            
            # Get user's branch
            if hasattr(request.user, 'profile') and request.user.profile.branch:
                session.branch = request.user.profile.branch
            
            session.opening_cash = Decimal(str(data.get('opening_cash', 0)))
            session.notes = data.get('notes', '')
            session.status = 'open'
            session.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Session {session.session_number} opened successfully!',
                'session_id': session.id,
                'session_number': session.session_number
            })
        
        elif action == 'close':
            session_id = data.get('session_id')
            if not session_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Session ID required'
                }, status=400)
            
            session = get_object_or_404(POSSession, id=session_id, cashier=request.user, status='open')
            
            closing_cash = Decimal(str(data.get('closing_cash', 0)))
            session.closing_cash = closing_cash
            session.status = 'closed'
            session.save()
            
            # Calculate cash difference
            expected_cash = session.opening_cash + session.total_cash_sales
            cash_difference = closing_cash - expected_cash
            
            return JsonResponse({
                'success': True,
                'message': f'Session {session.session_number} closed successfully!',
                'cash_difference': str(cash_difference),
                'expected_cash': str(expected_cash),
                'closing_cash': str(closing_cash)
            })
        
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid action'
            }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
