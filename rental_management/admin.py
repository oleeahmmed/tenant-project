"""Rental Management Admin Configuration"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Property, RentalTenant, RentalAgreement, Payment, DuePayment, SMSLog


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ["property_number", "property_type", "floor_number", "monthly_rent", "status", "current_tenant"]
    list_filter = ["property_type", "status", "tenant"]
    search_fields = ["property_number", "description"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("tenant", "property_type", "property_number", "floor_number")
        }),
        ("Details", {
            "fields": ("size_sqft", "bedrooms", "bathrooms", "monthly_rent", "description")
        }),
        ("Status", {
            "fields": ("status", "current_tenant")
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(RentalTenant)
class RentalTenantAdmin(admin.ModelAdmin):
    list_display = ["name", "mobile_number", "email", "occupation", "family_members_count", "is_active"]
    list_filter = ["is_active", "tenant"]
    search_fields = ["name", "mobile_number", "email", "nid_number"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("tenant", "name", "mobile_number", "email", "nid_number")
        }),
        ("Address & Contact", {
            "fields": ("permanent_address", "emergency_contact_name", "emergency_contact_number")
        }),
        ("Additional Info", {
            "fields": ("occupation", "family_members_count")
        }),
        ("Documents", {
            "fields": ("profile_photo", "nid_photo_front", "nid_photo_back")
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(RentalAgreement)
class RentalAgreementAdmin(admin.ModelAdmin):
    list_display = ["property", "rental_tenant", "start_date", "end_date", "monthly_rent", "status"]
    list_filter = ["status", "tenant", "start_date"]
    search_fields = ["property__property_number", "rental_tenant__name"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "start_date"
    
    fieldsets = (
        ("Agreement Details", {
            "fields": ("tenant", "property", "rental_tenant", "start_date", "end_date", "status")
        }),
        ("Financial Terms", {
            "fields": ("monthly_rent", "advance_amount", "advance_months", "service_charge", "rent_due_date")
        }),
        ("Documents & Notes", {
            "fields": ("agreement_document", "notes")
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["receipt_number", "agreement", "payment_type", "amount", "payment_date", "payment_method"]
    list_filter = ["payment_type", "payment_method", "tenant", "payment_date"]
    search_fields = ["receipt_number", "agreement__rental_tenant__name", "transaction_reference"]
    readonly_fields = ["receipt_number", "created_at", "updated_at"]
    date_hierarchy = "payment_date"
    
    fieldsets = (
        ("Payment Information", {
            "fields": ("tenant", "agreement", "payment_type", "payment_month", "amount")
        }),
        ("Payment Details", {
            "fields": ("payment_date", "payment_method", "transaction_reference", "receipt_number")
        }),
        ("Notes", {
            "fields": ("notes",)
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(DuePayment)
class DuePaymentAdmin(admin.ModelAdmin):
    list_display = ["agreement", "due_month", "due_amount", "due_date", "is_paid_display", "reminder_count"]
    list_filter = ["is_paid", "tenant", "due_date"]
    search_fields = ["agreement__rental_tenant__name", "agreement__property__property_number"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "due_date"
    
    def is_paid_display(self, obj):
        if obj.is_paid:
            return format_html('<span style="color: green;">✓ পরিশোধিত</span>')
        return format_html('<span style="color: red;">✗ বকেয়া</span>')
    is_paid_display.short_description = "Status"
    
    fieldsets = (
        ("Due Information", {
            "fields": ("tenant", "agreement", "due_month", "due_amount", "due_date")
        }),
        ("Payment Status", {
            "fields": ("is_paid", "paid_date")
        }),
        ("Reminders", {
            "fields": ("reminder_sent", "reminder_count")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ["mobile_number", "message_type", "status", "sent_at", "created_at"]
    list_filter = ["message_type", "status", "tenant", "created_at"]
    search_fields = ["mobile_number", "message_text", "rental_tenant__name"]
    readonly_fields = ["sent_at", "created_at"]
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("SMS Information", {
            "fields": ("tenant", "rental_tenant", "mobile_number", "message_type")
        }),
        ("Message", {
            "fields": ("message_text",)
        }),
        ("Status", {
            "fields": ("status", "sent_at", "error_message")
        }),
        ("Metadata", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )
