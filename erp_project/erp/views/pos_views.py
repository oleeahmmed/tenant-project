"""
Modern POS Interface Views
Restaurant-style POS system with product grid and cart
Supports: Sessions, Split Payments, Variants, Returns
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.contrib import admin
from decimal import Decimal

from ..models import (
    Product, Category, QuickSale, QuickSaleItem,
    Customer, Warehouse, UserProfile,
    POSSession, POSReturn, POSReturnItem,
    ProductVariant, PaymentMethod, ShippingArea
)


@method_decorator(staff_member_required, name='dispatch')
class ModernPOSView(View):
    """Modern Restaurant-style POS Interface"""
    
    def get(self, request, sale_id=None, *args, **kwargs):
        """Render POS interface (for both add and edit)"""
        
        # Get user's branch/warehouse
        try:
            user_profile = request.user.profile
            default_warehouse = user_profile.branch
        except (UserProfile.DoesNotExist, AttributeError):
            default_warehouse = Warehouse.objects.first()
        
        # Get or create open session for this user
        open_session = POSSession.objects.filter(
            cashier=request.user,
            status='open'
        ).first()
        
        # Get categories
        categories = Category.objects.filter(is_active=True).order_by('name')
        
        # Get products (active only)
        products = Product.objects.filter(
            is_active=True
        ).select_related('category').prefetch_related('variants').order_by('name')
        
        # Get customers for quick selection
        customers = Customer.objects.filter(is_active=True).order_by('name')[:50]
        
        # Get payment methods
        payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('name')
        
        # Get shipping areas
        shipping_areas = ShippingArea.objects.filter(is_active=True).order_by('area_name')
        
        # Check if editing existing sale
        existing_sale = None
        if sale_id:
            try:
                existing_sale = QuickSale.objects.select_related(
                    'customer', 'payment_method', 'branch'
                ).prefetch_related('items__product').get(id=sale_id)
            except QuickSale.DoesNotExist:
                pass
        
        context = {
            'title': 'Edit Sale' if existing_sale else 'Modern POS',
            'categories': categories,
            'products': products,
            'customers': customers,
            'default_warehouse': default_warehouse,
            'open_session': open_session,
            'payment_methods': payment_methods,
            'shipping_areas': shipping_areas,
            'existing_sale': existing_sale,
            'is_edit_mode': bool(existing_sale),
        }
        
        # Add admin context for sidebar
        context.update(admin.site.each_context(request))
        
        return render(request, 'admin/erp/pos/modern_pos.html', context)


@method_decorator(staff_member_required, name='dispatch')
class POSCreateSaleView(View):
    """Create sale from POS"""
    
    def post(self, request, *args, **kwargs):
        """Create or update sale with split payment support"""
        try:
            import json
            data = json.loads(request.body)
            
            # Check if updating existing sale
            sale_id = data.get('sale_id')
            if sale_id:
                # Update existing sale
                try:
                    sale = QuickSale.objects.get(id=sale_id)
                    
                    # Update sale fields
                    sale.customer_id = data.get('customer_id') if data.get('customer_id') else None
                    sale.customer_name = data.get('customer_name', '')
                    sale.customer_phone = data.get('customer_phone', '')
                    sale.payment_method_id = data.get('payment_method_id')
                    sale.subtotal = Decimal(str(data.get('subtotal', 0)))
                    sale.discount_amount = Decimal(str(data.get('discount', 0)))
                    sale.total_amount = Decimal(str(data.get('total', 0)))
                    sale.amount_received = Decimal(str(data.get('amount_received', 0)))
                    sale.change_amount = Decimal(str(data.get('change', 0)))
                    sale.notes = data.get('notes', '')
                    sale.save()
                    
                    # Delete old items
                    sale.items.all().delete()
                    
                    # Create new items
                    for item_data in data.get('items', []):
                        QuickSaleItem.objects.create(
                            quick_sale=sale,
                            product_id=item_data['product_id'],
                            variant_id=item_data.get('variant_id'),
                            quantity=Decimal(str(item_data['quantity'])),
                            unit_price=Decimal(str(item_data['unit_price'])),
                            discount_amount=Decimal(str(item_data.get('discount', 0))),
                            line_total=Decimal(str(item_data['line_total']))
                        )
                    
                    return JsonResponse({
                        'success': True,
                        'sale_id': sale.id,
                        'sale_number': sale.sale_number,
                        'message': 'Sale updated successfully'
                    })
                    
                except QuickSale.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Sale not found'
                    }, status=404)
            
            # Create new sale (existing code)
            # Get user's branch
            try:
                user_profile = request.user.profile
                branch = user_profile.branch
            except (UserProfile.DoesNotExist, AttributeError):
                branch = Warehouse.objects.first()
            
            # Get session
            session_id = data.get('session_id')
            session = None
            if session_id:
                session = POSSession.objects.filter(id=session_id, status='open').first()
            
            # Get payment method
            payment_method_id = data.get('payment_method_id')
            payment_method = None
            if payment_method_id:
                try:
                    payment_method = PaymentMethod.objects.get(id=payment_method_id, is_active=True)
                except PaymentMethod.DoesNotExist:
                    pass
            
            # Fallback to first active payment method or 'cash'
            if not payment_method:
                payment_method = PaymentMethod.objects.filter(is_active=True).first()
            
            # Create QuickSale
            sale = QuickSale.objects.create(
                user=request.user,
                branch=branch,
                session=session,
                sale_date=timezone.now().date(),
                customer_id=data.get('customer_id') if data.get('customer_id') else None,
                customer_name=data.get('customer_name', ''),
                customer_phone=data.get('customer_phone', ''),
                payment_method=payment_method,
                subtotal=Decimal(str(data.get('subtotal', 0))),
                discount_amount=Decimal(str(data.get('discount', 0))),
                total_amount=Decimal(str(data.get('total', 0))),
                amount_received=Decimal(str(data.get('amount_received', 0))),
                change_amount=Decimal(str(data.get('change', 0))),
                status='completed',
                notes=data.get('notes', '')
            )
            
            # Create items with variant support
            for item_data in data.get('items', []):
                QuickSaleItem.objects.create(
                    quick_sale=sale,
                    product_id=item_data['product_id'],
                    variant_id=item_data.get('variant_id'),
                    quantity=Decimal(str(item_data['quantity'])),
                    unit_price=Decimal(str(item_data['unit_price'])),
                    discount_amount=Decimal(str(item_data.get('discount', 0))),
                    line_total=Decimal(str(item_data['line_total']))
                )
            
            return JsonResponse({
                'success': True,
                'sale_id': sale.id,
                'sale_number': sale.sale_number,
                'message': 'Sale created successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@method_decorator(staff_member_required, name='dispatch')
class POSSearchProductView(View):
    """Search products for POS"""
    
    def get(self, request, *args, **kwargs):
        """Search products by name, SKU, or barcode"""
        query = request.GET.get('q', '').strip()
        category_id = request.GET.get('category')
        
        if not query and not category_id:
            return JsonResponse({'products': []})
        
        products = Product.objects.filter(is_active=True)
        
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(sku__icontains=query)
            )
        
        if category_id:
            products = products.filter(category_id=category_id)
        
        products = products.select_related('category').prefetch_related('variants')[:20]
        
        products_data = [{
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'category': p.category.name if p.category else '',
            'selling_price': float(p.selling_price),
            'variants': [{
                'id': v.id,
                'name': f"{v.size.name if v.size else ''} {v.color.name if v.color else ''}".strip(),
                'sku': v.sku,
            } for v in p.variants.all()] if hasattr(p, 'variants') else []
        } for p in products]
        
        return JsonResponse({'products': products_data})


@method_decorator(staff_member_required, name='dispatch')
class POSGetProductView(View):
    """Get single product details"""
    
    def get(self, request, product_id, *args, **kwargs):
        """Get product by ID"""
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            
            return JsonResponse({
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'category': product.category.name if product.category else '',
                    'selling_price': float(product.selling_price),
                    'variants': [{
                        'id': v.id,
                        'name': f"{v.size.name if v.size else ''} {v.color.name if v.color else ''}".strip(),
                        'sku': v.sku,
                    } for v in product.variants.all()] if hasattr(product, 'variants') else []
                }
            })
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Product not found'
            }, status=404)


@method_decorator(staff_member_required, name='dispatch')
class POSSessionView(View):
    """POS Session Management"""
    
    def post(self, request, *args, **kwargs):
        """Open or close a session"""
        try:
            import json
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'open':
                # Get user's branch
                try:
                    user_profile = request.user.profile
                    branch = user_profile.branch
                except (UserProfile.DoesNotExist, AttributeError):
                    branch = Warehouse.objects.first()
                
                # Check if already has open session
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
                session = POSSession.objects.create(
                    cashier=request.user,
                    branch=branch,
                    opening_cash=Decimal(str(data.get('opening_cash', 0))),
                    notes=data.get('notes', '')
                )
                
                return JsonResponse({
                    'success': True,
                    'session_id': session.id,
                    'session_number': session.session_number,
                    'message': 'Session opened successfully'
                })
            
            elif action == 'close':
                session_id = data.get('session_id')
                closing_cash = Decimal(str(data.get('closing_cash', 0)))
                
                session = POSSession.objects.get(
                    id=session_id,
                    cashier=request.user,
                    status='open'
                )
                
                session.close_session(closing_cash)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Session closed successfully',
                    'cash_difference': float(session.cash_difference)
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action'
                }, status=400)
                
        except POSSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Session not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@method_decorator(staff_member_required, name='dispatch')
class POSReturnView(View):
    """POS Return Management"""
    
    def post(self, request, *args, **kwargs):
        """Create a return"""
        try:
            import json
            data = json.loads(request.body)
            
            # Get user's branch
            try:
                user_profile = request.user.profile
                branch = user_profile.branch
            except (UserProfile.DoesNotExist, AttributeError):
                branch = Warehouse.objects.first()
            
            # Create return
            pos_return = POSReturn.objects.create(
                original_sale_id=data.get('original_sale_id'),
                user=request.user,
                branch=branch,
                return_date=timezone.now().date(),
                customer_name=data.get('customer_name', ''),
                customer_phone=data.get('customer_phone', ''),
                refund_method=data.get('refund_method', 'cash'),
                total_amount=Decimal(str(data.get('total_amount', 0))),
                reason=data.get('reason', ''),
                notes=data.get('notes', ''),
                status='completed'
            )
            
            # Create return items
            for item_data in data.get('items', []):
                POSReturnItem.objects.create(
                    pos_return=pos_return,
                    product_id=item_data['product_id'],
                    variant_id=item_data.get('variant_id'),
                    quantity=Decimal(str(item_data['quantity'])),
                    unit_price=Decimal(str(item_data['unit_price'])),
                    line_total=Decimal(str(item_data['line_total'])),
                    restock=item_data.get('restock', True)
                )
            
            return JsonResponse({
                'success': True,
                'return_id': pos_return.id,
                'return_number': pos_return.return_number,
                'message': 'Return created successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

