"""Rental Management API Views"""

from django.db.models import Sum, Q, Count
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from auth_tenants.permissions import TenantAPIView, RequirePermission
from rental_management.models import (
    Property,
    RentalTenant,
    RentalAgreement,
    Payment,
    DuePayment,
    SMSLog,
)
from .serializers import (
    PropertySerializer,
    RentalTenantSerializer,
    RentalAgreementSerializer,
    PaymentSerializer,
    DuePaymentSerializer,
    SMSLogSerializer,
)


class PropertyViewSet(TenantAPIView, viewsets.ModelViewSet):
    """Property CRUD API"""
    
    module_code = "rental"
    required_permission = "rental.view_property"
    serializer_class = PropertySerializer
    
    def get_queryset(self):
        tenant = self.get_tenant()
        qs = Property.objects.filter(tenant=tenant).select_related("current_tenant")
        
        # Filters
        property_type = self.request.query_params.get("property_type")
        status_filter = self.request.query_params.get("status")
        search = self.request.query_params.get("search")
        
        if property_type:
            qs = qs.filter(property_type=property_type)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if search:
            qs = qs.filter(
                Q(property_number__icontains=search) |
                Q(description__icontains=search)
            )
        
        return qs
    
    def perform_create(self, serializer):
        tenant = self.get_tenant()
        serializer.save(tenant=tenant, created_by=self.request.user)
    
    @action(detail=False, methods=["get"])
    def vacant(self, request):
        """খালি প্রপার্টি লিস্ট"""
        tenant = self.get_tenant()
        properties = Property.objects.filter(tenant=tenant, status="VACANT")
        serializer = self.get_serializer(properties, many=True)
        return self.success_response(serializer.data)



class RentalTenantViewSet(TenantAPIView, viewsets.ModelViewSet):
    """Rental Tenant CRUD API"""
    
    module_code = "rental"
    required_permission = "rental.view_tenant"
    serializer_class = RentalTenantSerializer
    
    def get_queryset(self):
        tenant = self.get_tenant()
        qs = RentalTenant.objects.filter(tenant=tenant)
        
        # Filters
        search = self.request.query_params.get("search")
        is_active = self.request.query_params.get("is_active")
        
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(mobile_number__icontains=search) |
                Q(email__icontains=search)
            )
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        
        return qs
    
    def perform_create(self, serializer):
        tenant = self.get_tenant()
        serializer.save(tenant=tenant, created_by=self.request.user)


class RentalAgreementViewSet(TenantAPIView, viewsets.ModelViewSet):
    """Rental Agreement CRUD API"""
    
    module_code = "rental"
    required_permission = "rental.view_agreement"
    serializer_class = RentalAgreementSerializer
    
    def get_queryset(self):
        tenant = self.get_tenant()
        qs = RentalAgreement.objects.filter(tenant=tenant).select_related(
            "property", "rental_tenant"
        )
        
        # Filters
        status_filter = self.request.query_params.get("status")
        property_id = self.request.query_params.get("property")
        tenant_id = self.request.query_params.get("rental_tenant")
        
        if status_filter:
            qs = qs.filter(status=status_filter)
        if property_id:
            qs = qs.filter(property_id=property_id)
        if tenant_id:
            qs = qs.filter(rental_tenant_id=tenant_id)
        
        return qs
    
    def perform_create(self, serializer):
        tenant = self.get_tenant()
        agreement = serializer.save(tenant=tenant, created_by=self.request.user)
        
        # Update property status and current tenant
        property_obj = agreement.property
        property_obj.status = "OCCUPIED"
        property_obj.current_tenant = agreement.rental_tenant
        property_obj.save()
    
    @action(detail=True, methods=["post"])
    def terminate(self, request, pk=None):
        """চুক্তি বাতিল করা"""
        agreement = self.get_object()
        agreement.status = "TERMINATED"
        agreement.save()
        
        # Update property status
        property_obj = agreement.property
        property_obj.status = "VACANT"
        property_obj.current_tenant = None
        property_obj.save()
        
        return self.success_response({"detail": "চুক্তি বাতিল করা হয়েছে"})


class PaymentViewSet(TenantAPIView, viewsets.ModelViewSet):
    """Payment CRUD API"""
    
    module_code = "rental"
    required_permission = "rental.view_payment"
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        tenant = self.get_tenant()
        qs = Payment.objects.filter(tenant=tenant).select_related(
            "agreement", "agreement__rental_tenant", "agreement__property"
        )
        
        # Filters
        agreement_id = self.request.query_params.get("agreement")
        payment_type = self.request.query_params.get("payment_type")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        
        if agreement_id:
            qs = qs.filter(agreement_id=agreement_id)
        if payment_type:
            qs = qs.filter(payment_type=payment_type)
        if start_date:
            qs = qs.filter(payment_date__gte=start_date)
        if end_date:
            qs = qs.filter(payment_date__lte=end_date)
        
        return qs
    
    def perform_create(self, serializer):
        tenant = self.get_tenant()
        payment = serializer.save(tenant=tenant, created_by=self.request.user)
        
        # If rent payment, mark due payment as paid
        if payment.payment_type == "RENT" and payment.payment_month:
            DuePayment.objects.filter(
                agreement=payment.agreement,
                due_month=payment.payment_month,
                is_paid=False
            ).update(is_paid=True, paid_date=payment.payment_date)


class DuePaymentViewSet(TenantAPIView, viewsets.ModelViewSet):
    """Due Payment API"""
    
    module_code = "rental"
    required_permission = "rental.view_payment"
    serializer_class = DuePaymentSerializer
    
    def get_queryset(self):
        tenant = self.get_tenant()
        qs = DuePayment.objects.filter(tenant=tenant).select_related(
            "agreement", "agreement__rental_tenant", "agreement__property"
        )
        
        # Filters
        is_paid = self.request.query_params.get("is_paid")
        agreement_id = self.request.query_params.get("agreement")
        
        if is_paid is not None:
            qs = qs.filter(is_paid=is_paid.lower() == "true")
        if agreement_id:
            qs = qs.filter(agreement_id=agreement_id)
        
        return qs
    
    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """বকেয়া লিস্ট"""
        tenant = self.get_tenant()
        dues = DuePayment.objects.filter(
            tenant=tenant,
            is_paid=False,
            due_date__lt=timezone.now().date()
        ).select_related("agreement", "agreement__rental_tenant", "agreement__property")
        
        serializer = self.get_serializer(dues, many=True)
        return self.success_response(serializer.data)


class SMSLogViewSet(TenantAPIView, viewsets.ReadOnlyModelViewSet):
    """SMS Log API (Read-only)"""
    
    module_code = "rental"
    required_permission = "rental.send_sms"
    serializer_class = SMSLogSerializer
    
    def get_queryset(self):
        tenant = self.get_tenant()
        qs = SMSLog.objects.filter(tenant=tenant).select_related("rental_tenant")
        
        # Filters
        message_type = self.request.query_params.get("message_type")
        status_filter = self.request.query_params.get("status")
        
        if message_type:
            qs = qs.filter(message_type=message_type)
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        return qs


class DashboardAPIView(TenantAPIView):
    """Dashboard statistics API"""
    
    module_code = "rental"
    required_permission = "rental.view_property"
    
    def get(self, request):
        tenant = self.get_tenant()
        
        # Property statistics
        total_properties = Property.objects.filter(tenant=tenant).count()
        vacant_properties = Property.objects.filter(tenant=tenant, status="VACANT").count()
        occupied_properties = Property.objects.filter(tenant=tenant, status="OCCUPIED").count()
        
        properties_by_type = Property.objects.filter(tenant=tenant).values("property_type").annotate(
            count=Count("id")
        )
        
        # Tenant statistics
        total_tenants = RentalTenant.objects.filter(tenant=tenant, is_active=True).count()
        
        # Financial statistics
        today = date.today()
        current_month_start = today.replace(day=1)
        current_month_end = (current_month_start + relativedelta(months=1)) - timedelta(days=1)
        
        monthly_income = Payment.objects.filter(
            tenant=tenant,
            payment_type="RENT",
            payment_date__gte=current_month_start,
            payment_date__lte=current_month_end
        ).aggregate(total=Sum("amount"))["total"] or 0
        
        total_due = DuePayment.objects.filter(
            tenant=tenant,
            is_paid=False
        ).aggregate(total=Sum("due_amount"))["total"] or 0
        
        overdue_count = DuePayment.objects.filter(
            tenant=tenant,
            is_paid=False,
            due_date__lt=today
        ).count()
        
        # Active agreements
        active_agreements = RentalAgreement.objects.filter(
            tenant=tenant,
            status="ACTIVE"
        ).count()
        
        # Expiring soon (within 30 days)
        expiring_soon = RentalAgreement.objects.filter(
            tenant=tenant,
            status="ACTIVE",
            end_date__lte=today + timedelta(days=30),
            end_date__gte=today
        ).count()
        
        # Recent payments (last 5)
        recent_payments = Payment.objects.filter(tenant=tenant).order_by("-payment_date")[:5]
        recent_payments_data = PaymentSerializer(recent_payments, many=True).data
        
        # Overdue list (top 10)
        overdue_list = DuePayment.objects.filter(
            tenant=tenant,
            is_paid=False,
            due_date__lt=today
        ).select_related("agreement", "agreement__rental_tenant", "agreement__property").order_by("due_date")[:10]
        overdue_list_data = DuePaymentSerializer(overdue_list, many=True).data
        
        data = {
            "properties": {
                "total": total_properties,
                "vacant": vacant_properties,
                "occupied": occupied_properties,
                "by_type": list(properties_by_type),
            },
            "tenants": {
                "total": total_tenants,
            },
            "financial": {
                "monthly_income": float(monthly_income),
                "total_due": float(total_due),
                "overdue_count": overdue_count,
            },
            "agreements": {
                "active": active_agreements,
                "expiring_soon": expiring_soon,
            },
            "recent_payments": recent_payments_data,
            "overdue_list": overdue_list_data,
        }
        
        return self.success_response(data)
