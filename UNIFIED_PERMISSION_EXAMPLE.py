# 🎯 UNIFIED PERMISSION SYSTEM - USAGE EXAMPLES

"""
এখন আপনার সব API views এভাবে লিখতে পারবেন - super simple!
"""

from auth_tenants.permissions import TenantAPIView, IsTenantAdmin, RequirePermission

# ═══════════════════════════════════════════════════════════════════════════════
# 📝 EXAMPLE 1: Simple API View
# ═══════════════════════════════════════════════════════════════════════════════

class ProductListView(TenantAPIView):
    """
    🎯 SUPER SIMPLE API VIEW
    - Automatically checks tenant access
    - Automatically checks module subscription
    - Automatically checks permissions
    """
    
    module_code = "inventory"                    # Auto-check inventory module access
    required_permission = "inventory.view"       # Auto-check specific permission
    
    def get(self, request):
        tenant = self.get_tenant()  # Always available, already validated
        
        # Your business logic here
        products = Product.objects.filter(tenant=tenant)
        
        return self.success_response({
            "products": [{"id": p.id, "name": p.name} for p in products],
            "count": products.count()
        })

# ═══════════════════════════════════════════════════════════════════════════════
# 📝 EXAMPLE 2: Admin-only API View
# ═══════════════════════════════════════════════════════════════════════════════

class TenantSettingsView(TenantAPIView):
    """Only tenant admins can access"""
    
    permission_classes = [IsTenantAdmin]  # Auto-check admin role
    
    def get(self, request):
        tenant = self.get_tenant()
        
        return self.success_response({
            "tenant_name": tenant.name,
            "subscription": tenant.get_subscription().plan.name,
            "users_count": tenant.members.count()
        })

# ═══════════════════════════════════════════════════════════════════════════════
# 📝 EXAMPLE 3: Multiple Permission Checks
# ═══════════════════════════════════════════════════════════════════════════════

class InventoryManageView(TenantAPIView):
    """Complex permission checking"""
    
    module_code = "inventory"                    # Must have inventory module
    required_permission = "inventory.manage"     # Must have manage permission
    
    def post(self, request):
        tenant = self.get_tenant()
        
        # Create new product
        product = Product.objects.create(
            tenant=tenant,
            name=request.data.get('name'),
            created_by=request.user
        )
        
        return self.success_response({
            "message": "Product created successfully",
            "product_id": product.id
        })

# ═══════════════════════════════════════════════════════════════════════════════
# 📝 EXAMPLE 4: No Restrictions (Public API)
# ═══════════════════════════════════════════════════════════════════════════════

class PublicInfoView(TenantAPIView):
    """No module or permission restrictions"""
    
    def get(self, request):
        tenant = self.get_tenant()
        
        return self.success_response({
            "tenant_name": tenant.name,
            "public_info": "This is public data"
        })

# ═══════════════════════════════════════════════════════════════════════════════
# 📝 EXAMPLE 5: Using Convenience Functions
# ═══════════════════════════════════════════════════════════════════════════════

from auth_tenants.permissions import get_tenant, has_permission, can_access_module

def my_regular_view(request):
    """Regular Django view using convenience functions"""
    
    tenant = get_tenant(request)
    if not tenant:
        return JsonResponse({"error": "No tenant"}, status=403)
    
    if not can_access_module(request, "inventory"):
        return JsonResponse({"error": "Module not available"}, status=403)
    
    if not has_permission(request, "inventory.view"):
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    # Your logic here
    return JsonResponse({"message": "Success"})

# ═══════════════════════════════════════════════════════════════════════════════
# 📝 EXAMPLE 6: Template Usage
# ═══════════════════════════════════════════════════════════════════════════════

"""
In your templates:

{% load module_flags %}

<!-- Get navigation flags -->
{% workspace_nav as nav %}
{% if nav.inventory %}
    <a href="/inventory/">Inventory</a>
{% endif %}

<!-- Get current tenant -->
{% current_tenant as tenant %}
<h1>Welcome to {{ tenant.name }}</h1>

<!-- Check module access -->
{% if tenant|module_enabled:"inventory" %}
    <p>Inventory module is available</p>
{% endif %}
"""

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 BENEFITS OF THIS SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

"""
✅ SINGLE FILE CONTROLS EVERYTHING
   - No more scattered permission logic
   - One place to understand the system

✅ BEGINNER FRIENDLY
   - Just inherit from TenantAPIView
   - Set module_code and required_permission
   - Everything else is automatic

✅ DYNAMIC MODULE DISCOVERY
   - Add new Django app → automatically appears in navigation
   - No manual configuration needed

✅ SUBSCRIPTION INTEGRATION
   - Module access automatically checks subscription
   - Usage limits enforced automatically

✅ CONSISTENT API RESPONSES
   - success_response() and error_response() 
   - Standard format across all APIs

✅ CLASS-BASED EVERYTHING
   - Easy to extend and customize
   - Object-oriented design

✅ ZERO CONFIGURATION
   - Works out of the box
   - Discovers modules automatically from settings.LOCAL_APPS
"""