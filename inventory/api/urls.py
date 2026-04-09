from django.urls import path

from . import views

app_name = "inventory_api"

urlpatterns = [
    path(
        "product-warehouse/",
        views.ProductWarehouseContextView.as_view(),
        name="product_warehouse_context",
    ),
]
