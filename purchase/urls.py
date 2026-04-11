from django.urls import path

from . import views

app_name = "purchase"

urlpatterns = [
    path("", views.PurchaseDashboardView.as_view(), name="purchase_dashboard"),
    path("requests/", views.PurchaseRequestListView.as_view(), name="purchase_request_list"),
    path("requests/add/", views.PurchaseRequestCreateView.as_view(), name="purchase_request_create"),
    path("requests/<int:pk>/", views.PurchaseRequestDetailView.as_view(), name="purchase_request_detail"),
    path("requests/<int:pk>/print/", views.PurchaseRequestPrintView.as_view(), name="purchase_request_print"),
    path("requests/<int:pk>/pdf/", views.PurchaseRequestPrintView.as_view(), name="purchase_request_pdf"),
    path("requests/<int:pk>/edit/", views.PurchaseRequestUpdateView.as_view(), name="purchase_request_edit"),
    path("requests/<int:pk>/delete/", views.PurchaseRequestDeleteView.as_view(), name="purchase_request_delete"),
    path("requests/<int:pk>/approve/", views.PurchaseRequestApproveView.as_view(), name="purchase_request_approve"),
    path("orders/", views.PurchaseOrderListView.as_view(), name="purchase_order_list"),
    path("orders/add/", views.PurchaseOrderCreateView.as_view(), name="purchase_order_create"),
    path("orders/<int:pk>/", views.PurchaseOrderDetailView.as_view(), name="purchase_order_detail"),
    path("orders/<int:pk>/print/", views.PurchaseOrderPrintView.as_view(), name="purchase_order_print"),
    path("orders/<int:pk>/pdf/", views.PurchaseOrderPrintView.as_view(), name="purchase_order_pdf"),
    path("orders/<int:pk>/edit/", views.PurchaseOrderUpdateView.as_view(), name="purchase_order_edit"),
    path("orders/<int:pk>/delete/", views.PurchaseOrderDeleteView.as_view(), name="purchase_order_delete"),
    path("orders/<int:pk>/approve/", views.PurchaseOrderApproveView.as_view(), name="purchase_order_approve"),
    path("receipts/", views.GoodsReceiptListView.as_view(), name="goods_receipt_list"),
    path("receipts/add/", views.GoodsReceiptCreateView.as_view(), name="goods_receipt_create"),
    path("receipts/<int:pk>/", views.GoodsReceiptDetailView.as_view(), name="goods_receipt_detail"),
    path("receipts/<int:pk>/print/", views.GoodsReceiptPrintView.as_view(), name="goods_receipt_print"),
    path("receipts/<int:pk>/pdf/", views.GoodsReceiptPrintView.as_view(), name="goods_receipt_pdf"),
    path("receipts/<int:pk>/edit/", views.GoodsReceiptUpdateView.as_view(), name="goods_receipt_edit"),
    path("receipts/<int:pk>/delete/", views.GoodsReceiptDeleteView.as_view(), name="goods_receipt_delete"),
    path("receipts/<int:pk>/post/", views.GoodsReceiptPostView.as_view(), name="goods_receipt_post"),
    path("returns/", views.PurchaseReturnListView.as_view(), name="purchase_return_list"),
    path("returns/add/", views.PurchaseReturnCreateView.as_view(), name="purchase_return_create"),
    path("returns/<int:pk>/", views.PurchaseReturnDetailView.as_view(), name="purchase_return_detail"),
    path("returns/<int:pk>/print/", views.PurchaseReturnPrintView.as_view(), name="purchase_return_print"),
    path("returns/<int:pk>/pdf/", views.PurchaseReturnPrintView.as_view(), name="purchase_return_pdf"),
    path("returns/<int:pk>/edit/", views.PurchaseReturnUpdateView.as_view(), name="purchase_return_edit"),
    path("returns/<int:pk>/delete/", views.PurchaseReturnDeleteView.as_view(), name="purchase_return_delete"),
    path("returns/<int:pk>/post/", views.PurchaseReturnPostView.as_view(), name="purchase_return_post"),
    path("guide/", views.PurchaseGuideView.as_view(), name="purchase_guide"),
]

