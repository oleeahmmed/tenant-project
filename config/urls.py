from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login'), name='home'),
    path('', include('auth_tenants.urls')),
    path('dashboard/hrm/', include('hrm.urls')),
    path('dashboard/foundation/', include('foundation.urls')),
    path('dashboard/inventory/', include('inventory.urls')),
    path('dashboard/finance/', include('finance.urls')),
    path('dashboard/purchase/', include('purchase.urls')),
    path('dashboard/sales/', include('sales.urls')),
    path('dashboard/production/', include('production.urls')),
    path('api/hrm/', include('hrm.api.urls')),
    path('api/auth/', include('auth_tenants.api.urls')),
    path('api/foundation/', include(('foundation.api.urls', 'foundation_api'), namespace='foundation_api')),
    path('api/inventory/', include(('inventory.api.urls', 'inventory_api'), namespace='inventory_api')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
