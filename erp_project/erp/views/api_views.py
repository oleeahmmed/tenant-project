"""
API Views - JSON endpoints for AJAX requests
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required

from ..models import Product, SalesOrder, PurchaseOrder, SalesQuotation, PurchaseQuotation


@require_http_methods(["GET"])
@staff_member_required
def get_product_price(request, product_id):
    """API endpoint to get product selling price"""
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({
            'success': True,
            'product_id': product.id,
            'product_name': product.name,
            'selling_price': str(product.selling_price),
            'purchase_price': str(product.purchase_price),
            'unit': product.unit,
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)


@require_http_methods(["GET"])
@staff_member_required
def get_sales_order_details(request, sales_order_id):
    """API endpoint to get sales order details for auto-filling"""
    try:
        sales_order = SalesOrder.objects.select_related('customer', 'salesperson').get(id=sales_order_id)
        return JsonResponse({
            'success': True,
            'sales_order_id': sales_order.id,
            'order_number': sales_order.order_number,
            'customer_id': sales_order.customer.id,
            'customer_name': sales_order.customer.name,
            'salesperson_id': sales_order.salesperson.id if sales_order.salesperson else None,
            'salesperson_name': sales_order.salesperson.name if sales_order.salesperson else None,
        })
    except SalesOrder.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Sales Order not found'
        }, status=404)


@require_http_methods(["GET"])
@staff_member_required
def get_purchase_order_details(request, purchase_order_id):
    """API endpoint to get purchase order details for auto-filling"""
    try:
        purchase_order = PurchaseOrder.objects.select_related('supplier').get(id=purchase_order_id)
        return JsonResponse({
            'success': True,
            'purchase_order_id': purchase_order.id,
            'order_number': purchase_order.order_number,
            'supplier_id': purchase_order.supplier.id,
            'supplier_name': purchase_order.supplier.name,
        })
    except PurchaseOrder.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Purchase Order not found'
        }, status=404)


@require_http_methods(["GET"])
@staff_member_required
def get_sales_quotation_details(request, sales_quotation_id):
    """API endpoint to get sales quotation details for auto-filling"""
    try:
        sales_quotation = SalesQuotation.objects.select_related('customer', 'salesperson').get(id=sales_quotation_id)
        return JsonResponse({
            'success': True,
            'sales_quotation_id': sales_quotation.id,
            'quotation_number': sales_quotation.quotation_number,
            'customer_id': sales_quotation.customer.id,
            'customer_name': sales_quotation.customer.name,
            'salesperson_id': sales_quotation.salesperson.id if sales_quotation.salesperson else None,
            'salesperson_name': sales_quotation.salesperson.name if sales_quotation.salesperson else None,
        })
    except:
        return JsonResponse({
            'success': False,
            'error': 'Sales Quotation not found'
        }, status=404)


@require_http_methods(["GET"])
@staff_member_required
def get_purchase_quotation_details(request, purchase_quotation_id):
    """API endpoint to get purchase quotation details for auto-filling"""
    try:
        purchase_quotation = PurchaseQuotation.objects.select_related('supplier').get(id=purchase_quotation_id)
        return JsonResponse({
            'success': True,
            'purchase_quotation_id': purchase_quotation.id,
            'quotation_number': purchase_quotation.quotation_number,
            'supplier_id': purchase_quotation.supplier.id,
            'supplier_name': purchase_quotation.supplier.name,
        })
    except:
        return JsonResponse({
            'success': False,
            'error': 'Purchase Quotation not found'
        }, status=404)



@require_http_methods(["GET"])
@staff_member_required
def get_product_by_sku(request):
    """API endpoint to get product by SKU/Barcode - for POS scanning"""
    sku = request.GET.get('sku', '').strip()
    
    if not sku:
        return JsonResponse({
            'success': False,
            'error': 'SKU is required'
        }, status=400)
    
    try:
        # Try exact match first (case-insensitive)
        product = Product.objects.filter(sku__iexact=sku, is_active=True).first()
        
        if product:
            return JsonResponse({
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'selling_price': str(product.selling_price),
                    'purchase_price': str(product.purchase_price),
                    'unit': product.unit,
                    'current_stock': str(product.current_stock),
                    'category': product.category.name if product.category else None,
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Product not found with SKU: {sku}'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


from ..models import ProductionOrder


@require_http_methods(["GET"])
@staff_member_required
def get_production_order_components(request, production_order_id):
    """API endpoint to get production order components for Production Receipt"""
    try:
        production_order = ProductionOrder.objects.prefetch_related('components__product').get(id=production_order_id)
        
        components = []
        for comp in production_order.components.all():
            components.append({
                'product_id': comp.product.id,
                'product_name': comp.product.name,
                'product_sku': comp.product.sku,
                'quantity_required': str(comp.quantity_required),
                'quantity_consumed': str(comp.quantity_consumed),
                'unit_cost': str(comp.unit_cost),
                'unit': comp.product.unit,
            })
        
        return JsonResponse({
            'success': True,
            'production_order_id': production_order.id,
            'order_number': production_order.order_number,
            'product_id': production_order.product.id,
            'product_name': production_order.product.name,
            'warehouse_id': production_order.warehouse.id,
            'warehouse_name': production_order.warehouse.name,
            'components': components,
        })
    except ProductionOrder.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Production Order not found'
        }, status=404)

# Additional Autocomplete API endpoints for Admin forms


@require_http_methods(["GET"])
@staff_member_required
def get_customer_details(request, customer_id):
    """API endpoint to get customer details by ID"""
    try:
        from ..models import Customer
        customer = Customer.objects.get(id=customer_id)
        return JsonResponse({
            'success': True,
            'id': customer.id,
            'name': customer.name,
            'email': customer.email or '',
            'phone': customer.phone or '',
            'address': customer.address or '',
        })
    except Customer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Customer not found'
        }, status=404)


@require_http_methods(["GET"])
@staff_member_required
def get_customer_by_phone(request):
    """API endpoint to search customer by phone number"""
    phone = request.GET.get('phone', '').strip()
    
    if not phone:
        return JsonResponse({
            'success': False,
            'error': 'Phone number is required'
        }, status=400)
    
    try:
        from ..models import Customer
        # Try exact match first
        customer = Customer.objects.filter(phone__iexact=phone, is_active=True).first()
        
        # If not found, try partial match
        if not customer:
            customer = Customer.objects.filter(phone__icontains=phone, is_active=True).first()
        
        if customer:
            return JsonResponse({
                'success': True,
                'id': customer.id,
                'name': customer.name,
                'email': customer.email or '',
                'phone': customer.phone or '',
                'address': customer.address or '',
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Customer not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

