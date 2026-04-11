from django.urls import path

from . import views

app_name = "production"

urlpatterns = [
    path("", views.ProductionDashboardView.as_view(), name="production_dashboard"),
    path("bom/", views.BillOfMaterialListView.as_view(), name="bom_list"),
    path("bom/add/", views.BillOfMaterialCreateView.as_view(), name="bom_create"),
    path("bom/<int:pk>/", views.BillOfMaterialDetailView.as_view(), name="bom_detail"),
    path("bom/<int:pk>/edit/", views.BillOfMaterialUpdateView.as_view(), name="bom_edit"),
    path("bom/<int:pk>/delete/", views.BillOfMaterialDeleteView.as_view(), name="bom_delete"),
    path("bom/<int:pk>/activate/", views.BillOfMaterialActivateView.as_view(), name="bom_activate"),
    path("orders/", views.ProductionOrderListView.as_view(), name="order_list"),
    path("orders/add/", views.ProductionOrderCreateView.as_view(), name="order_create"),
    path("orders/<int:pk>/", views.ProductionOrderDetailView.as_view(), name="order_detail"),
    path("orders/<int:pk>/edit/", views.ProductionOrderUpdateView.as_view(), name="order_edit"),
    path("orders/<int:pk>/delete/", views.ProductionOrderDeleteView.as_view(), name="order_delete"),
    path("orders/<int:pk>/release/", views.ProductionOrderReleaseView.as_view(), name="order_release"),
    path("issues/", views.IssueForProductionListView.as_view(), name="issue_list"),
    path("issues/add/", views.IssueForProductionCreateView.as_view(), name="issue_create"),
    path("issues/<int:pk>/", views.IssueForProductionDetailView.as_view(), name="issue_detail"),
    path("issues/<int:pk>/edit/", views.IssueForProductionUpdateView.as_view(), name="issue_edit"),
    path("issues/<int:pk>/delete/", views.IssueForProductionDeleteView.as_view(), name="issue_delete"),
    path("issues/<int:pk>/post/", views.IssueForProductionPostView.as_view(), name="issue_post"),
    path("receipts/", views.ReceiptFromProductionListView.as_view(), name="receipt_list"),
    path("receipts/add/", views.ReceiptFromProductionCreateView.as_view(), name="receipt_create"),
    path("receipts/<int:pk>/", views.ReceiptFromProductionDetailView.as_view(), name="receipt_detail"),
    path("receipts/<int:pk>/edit/", views.ReceiptFromProductionUpdateView.as_view(), name="receipt_edit"),
    path("receipts/<int:pk>/delete/", views.ReceiptFromProductionDeleteView.as_view(), name="receipt_delete"),
    path("receipts/<int:pk>/post/", views.ReceiptFromProductionPostView.as_view(), name="receipt_post"),
]

