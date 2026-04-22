from django.http import JsonResponse
from django.urls import resolve
from django.shortcuts import redirect
from django.contrib import messages
from auth_tenants.permissions import get_tenant, can_access_module

class SubscriptionMiddleware:
    """
    🎯 UNIFIED SUBSCRIPTION MIDDLEWARE
    Automatically checks module access for all requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for anonymous users, superusers and system paths
        if (request.user.is_anonymous or 
            getattr(request.user, 'role', None) == 'super_admin' or
            request.path.startswith('/api/auth/') or
            request.path.startswith('/admin/') or
            request.path.startswith('/static/') or
            request.path.startswith('/media/')):
            return self.get_response(request)
        
        # Get module from URL
        try:
            resolved = resolve(request.path_info)
            app_name = resolved.app_name
        except:
            return self.get_response(request)
        
        # Check module access for tenant users
        if app_name and hasattr(request.user, 'tenant') and request.user.tenant:
            if not can_access_module(request, app_name):
                tenant = get_tenant(request)
                current_plan = tenant.get_subscription().plan.name if tenant and tenant.get_subscription() else 'No Plan'
                
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        'ok': False,
                        'error': f'Module "{app_name}" not available in your subscription plan',
                        'module': app_name,
                        'upgrade_required': True,
                        'current_plan': current_plan
                    }, status=403)
                else:
                    # For web requests, redirect to subscription page
                    messages.error(
                        request, 
                        f'The {app_name.title()} module is not available in your current plan ({current_plan}). Please upgrade to access this feature.'
                    )
                    return redirect('/auth_tenants/dashboard/subscription/')
        
        return self.get_response(request)