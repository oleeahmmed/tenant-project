from django.urls import path

from . import views

app_name = "rental_management"

urlpatterns = [
    path("", views.RentalDashboardView.as_view(), name="dashboard"),
    path("guide/", views.RentalGuideView.as_view(), name="guide"),
    path("properties/", views.PropertyListView.as_view(), name="property_list"),
    path("properties/add/", views.PropertyCreateView.as_view(), name="property_create"),
    path("properties/<int:pk>/", views.PropertyDetailView.as_view(), name="property_detail"),
    path("properties/<int:pk>/edit/", views.PropertyUpdateView.as_view(), name="property_update"),
    path("tenants/", views.RentalTenantListView.as_view(), name="tenant_list"),
    path("tenants/add/", views.RentalTenantCreateView.as_view(), name="tenant_create"),
    path("tenants/<int:pk>/", views.RentalTenantDetailView.as_view(), name="tenant_detail"),
    path("tenants/<int:pk>/edit/", views.RentalTenantUpdateView.as_view(), name="tenant_update"),
    path("agreements/", views.RentalAgreementListView.as_view(), name="agreement_list"),
    path("agreements/add/", views.RentalAgreementCreateView.as_view(), name="agreement_create"),
    path("agreements/<int:pk>/", views.RentalAgreementDetailView.as_view(), name="agreement_detail"),
    path("agreements/<int:pk>/edit/", views.RentalAgreementUpdateView.as_view(), name="agreement_update"),
    path("agreements/<int:pk>/terminate/", views.RentalAgreementTerminateView.as_view(), name="agreement_terminate"),
    path("payments/", views.PaymentListView.as_view(), name="payment_list"),
    path("payments/add/", views.PaymentCreateView.as_view(), name="payment_create"),
    path("payments/<int:pk>/", views.PaymentDetailView.as_view(), name="payment_detail"),
    path("dues/", views.DuePaymentListView.as_view(), name="due_list"),
    path("sms-logs/", views.SMSLogListView.as_view(), name="sms_log_list"),
]
