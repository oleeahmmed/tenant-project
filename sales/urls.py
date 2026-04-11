from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("", views.SalesDashboardView.as_view(), name="sales_dashboard"),
    path("quotations/", views.SalesQuotationListView.as_view(), name="quotation_list"),
    path("quotations/add/", views.SalesQuotationCreateView.as_view(), name="quotation_create"),
    path("quotations/<int:pk>/", views.SalesQuotationDetailView.as_view(), name="quotation_detail"),
    path("quotations/<int:pk>/edit/", views.SalesQuotationUpdateView.as_view(), name="quotation_edit"),
    path("quotations/<int:pk>/delete/", views.SalesQuotationDeleteView.as_view(), name="quotation_delete"),
    path("quotations/<int:pk>/approve/", views.SalesQuotationApproveView.as_view(), name="quotation_approve"),
    path("orders/", views.SalesOrderListView.as_view(), name="order_list"),
    path("orders/add/", views.SalesOrderCreateView.as_view(), name="order_create"),
    path("orders/<int:pk>/", views.SalesOrderDetailView.as_view(), name="order_detail"),
    path("orders/<int:pk>/edit/", views.SalesOrderUpdateView.as_view(), name="order_edit"),
    path("orders/<int:pk>/delete/", views.SalesOrderDeleteView.as_view(), name="order_delete"),
    path("orders/<int:pk>/approve/", views.SalesOrderApproveView.as_view(), name="order_approve"),
    path("deliveries/", views.DeliveryNoteListView.as_view(), name="delivery_list"),
    path("deliveries/add/", views.DeliveryNoteCreateView.as_view(), name="delivery_create"),
    path("deliveries/<int:pk>/", views.DeliveryNoteDetailView.as_view(), name="delivery_detail"),
    path("deliveries/<int:pk>/edit/", views.DeliveryNoteUpdateView.as_view(), name="delivery_edit"),
    path("deliveries/<int:pk>/delete/", views.DeliveryNoteDeleteView.as_view(), name="delivery_delete"),
    path("deliveries/<int:pk>/post/", views.DeliveryNotePostView.as_view(), name="delivery_post"),
    path("returns/", views.SalesReturnListView.as_view(), name="return_list"),
    path("returns/add/", views.SalesReturnCreateView.as_view(), name="return_create"),
    path("returns/<int:pk>/", views.SalesReturnDetailView.as_view(), name="return_detail"),
    path("returns/<int:pk>/edit/", views.SalesReturnUpdateView.as_view(), name="return_edit"),
    path("returns/<int:pk>/delete/", views.SalesReturnDeleteView.as_view(), name="return_delete"),
    path("returns/<int:pk>/post/", views.SalesReturnPostView.as_view(), name="return_post"),
]

