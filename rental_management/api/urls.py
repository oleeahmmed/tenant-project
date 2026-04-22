"""Rental Management API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PropertyViewSet,
    RentalTenantViewSet,
    RentalAgreementViewSet,
    PaymentViewSet,
    DuePaymentViewSet,
    SMSLogViewSet,
    DashboardAPIView,
)

router = DefaultRouter()
router.register(r"properties", PropertyViewSet, basename="property")
router.register(r"tenants", RentalTenantViewSet, basename="rental-tenant")
router.register(r"agreements", RentalAgreementViewSet, basename="agreement")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"dues", DuePaymentViewSet, basename="due-payment")
router.register(r"sms-logs", SMSLogViewSet, basename="sms-log")

urlpatterns = [
    path("dashboard/", DashboardAPIView.as_view(), name="dashboard"),
    path("", include(router.urls)),
]
