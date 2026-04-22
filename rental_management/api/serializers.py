"""Rental Management API Serializers"""

from rest_framework import serializers
from rental_management.models import (
    Property,
    RentalTenant,
    RentalAgreement,
    Payment,
    DuePayment,
    SMSLog,
)


class PropertySerializer(serializers.ModelSerializer):
    """Property serializer"""
    
    property_type_display = serializers.CharField(source="get_property_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    current_tenant_name = serializers.CharField(source="current_tenant.name", read_only=True, allow_null=True)
    
    class Meta:
        model = Property
        fields = [
            "id", "property_type", "property_type_display", "property_number",
            "floor_number", "size_sqft", "bedrooms", "bathrooms", "monthly_rent",
            "status", "status_display", "description", "current_tenant", 
            "current_tenant_name", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RentalTenantSerializer(serializers.ModelSerializer):
    """Rental Tenant serializer"""
    
    active_agreements_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RentalTenant
        fields = [
            "id", "name", "mobile_number", "email", "nid_number",
            "permanent_address", "emergency_contact_name", "emergency_contact_number",
            "occupation", "family_members_count", "profile_photo", "nid_photo_front",
            "nid_photo_back", "is_active", "active_agreements_count",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_active_agreements_count(self, obj):
        return obj.agreements.filter(status="ACTIVE").count()



class RentalAgreementSerializer(serializers.ModelSerializer):
    """Rental Agreement serializer"""
    
    property_display = serializers.CharField(source="property.__str__", read_only=True)
    tenant_name = serializers.CharField(source="rental_tenant.name", read_only=True)
    tenant_mobile = serializers.CharField(source="rental_tenant.mobile_number", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_paid = serializers.SerializerMethodField()
    total_due = serializers.SerializerMethodField()
    
    class Meta:
        model = RentalAgreement
        fields = [
            "id", "property", "property_display", "rental_tenant", "tenant_name",
            "tenant_mobile", "start_date", "end_date", "monthly_rent", "advance_amount",
            "advance_months", "service_charge", "rent_due_date", "agreement_document",
            "status", "status_display", "notes", "total_paid", "total_due",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_total_paid(self, obj):
        return obj.payments.filter(payment_type="RENT").aggregate(
            total=serializers.models.Sum("amount")
        )["total"] or 0
    
    def get_total_due(self, obj):
        return obj.due_payments.filter(is_paid=False).aggregate(
            total=serializers.models.Sum("due_amount")
        )["total"] or 0


class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer"""
    
    agreement_display = serializers.CharField(source="agreement.__str__", read_only=True)
    payment_type_display = serializers.CharField(source="get_payment_type_display", read_only=True)
    payment_method_display = serializers.CharField(source="get_payment_method_display", read_only=True)
    tenant_name = serializers.CharField(source="agreement.rental_tenant.name", read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            "id", "agreement", "agreement_display", "tenant_name", "payment_type",
            "payment_type_display", "payment_month", "amount", "payment_date",
            "payment_method", "payment_method_display", "transaction_reference",
            "receipt_number", "notes", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "receipt_number", "created_at", "updated_at"]


class DuePaymentSerializer(serializers.ModelSerializer):
    """Due Payment serializer"""
    
    agreement_display = serializers.CharField(source="agreement.__str__", read_only=True)
    tenant_name = serializers.CharField(source="agreement.rental_tenant.name", read_only=True)
    tenant_mobile = serializers.CharField(source="agreement.rental_tenant.mobile_number", read_only=True)
    property_display = serializers.CharField(source="agreement.property.__str__", read_only=True)
    
    class Meta:
        model = DuePayment
        fields = [
            "id", "agreement", "agreement_display", "tenant_name", "tenant_mobile",
            "property_display", "due_month", "due_amount", "due_date", "is_paid",
            "paid_date", "reminder_sent", "reminder_count", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SMSLogSerializer(serializers.ModelSerializer):
    """SMS Log serializer"""
    
    tenant_name = serializers.CharField(source="rental_tenant.name", read_only=True, allow_null=True)
    message_type_display = serializers.CharField(source="get_message_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    
    class Meta:
        model = SMSLog
        fields = [
            "id", "rental_tenant", "tenant_name", "mobile_number", "message_text",
            "message_type", "message_type_display", "status", "status_display",
            "sent_at", "error_message", "created_at"
        ]
        read_only_fields = ["id", "sent_at", "created_at"]
