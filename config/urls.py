from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="api_schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="api_schema"), name="swagger_ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="api_schema"), name="redoc"),
    # Chrome DevTools optional probe — avoids harmless 404 noise in runserver logs.
    re_path(
        r"^\.well-known/appspecific/com\.chrome\.devtools\.json$",
        lambda request: HttpResponse(status=204),
    ),
    path('', lambda request: redirect('login'), name='home'),
    path('', include('auth_tenants.urls')),
    path('dashboard/hrm/', include('hrm.urls')),
    path('dashboard/foundation/', include('foundation.urls')),
    path('dashboard/inventory/', include('inventory.urls')),
    path('dashboard/finance/', include('finance.urls')),
    path('dashboard/purchase/', include('purchase.urls')),
    path('dashboard/sales/', include('sales.urls')),
    path('dashboard/production/', include('production.urls')),
    path('dashboard/notifications/', include(('notification.urls', 'notification'), namespace='notification')),
    path('dashboard/chat/', include(('chat.urls', 'chat'), namespace='chat')),
    path('dashboard/pos/', include(('pos.urls', 'pos'), namespace='pos')),
    path('dashboard/support/', include(('support.urls', 'support'), namespace='support')),
    path('api/hrm/', include('hrm.api.urls')),
    path('api/auth/', include('auth_tenants.api.urls')),
    path('api/foundation/', include(('foundation.api.urls', 'foundation_api'), namespace='foundation_api')),
    path('api/inventory/', include(('inventory.api.urls', 'inventory_api'), namespace='inventory_api')),
    path('api/chat/', include(('chat.api.urls', 'chat_api'), namespace='chat_api')),
]

# Media: django.conf.urls.static.static only adds routes when DEBUG=True.
# With DEBUG=False, uploads still land in MEDIA_ROOT but /media/ URLs 404 unless nginx or:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif getattr(settings, "FORCE_SERVE_MEDIA", False):
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
