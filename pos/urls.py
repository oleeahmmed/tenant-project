from django.urls import path

from . import views

app_name = "pos"

urlpatterns = [
    path("", views.POSDashboardView.as_view(), name="dashboard"),
    path("guide/", views.POSGuideView.as_view(), name="pos_guide"),
    path("registers/", views.POSRegisterListView.as_view(), name="register_list"),
    path("registers/create/", views.POSRegisterCreateView.as_view(), name="register_create"),
    path("registers/<int:pk>/edit/", views.POSRegisterUpdateView.as_view(), name="register_edit"),
    path("session/open/", views.OpenSessionView.as_view(), name="open_session"),
    path("session/close/", views.CloseSessionView.as_view(), name="close_session"),
    path("cashier/", views.CashierView.as_view(), name="cashier"),
    path("cashier/checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("sales/", views.POSSaleListView.as_view(), name="sale_list"),
    path("sales/<int:pk>/", views.POSSaleDetailView.as_view(), name="sale_detail"),
    path("sales/<int:pk>/receipt/", views.SaleReceiptPrintView.as_view(), name="sale_receipt"),
    path("sales/<int:pk>/void/", views.VoidSaleView.as_view(), name="sale_void"),
    path("sessions/", views.POSSessionListView.as_view(), name="session_list"),
]
