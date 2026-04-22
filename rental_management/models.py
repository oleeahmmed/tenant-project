"""Rental Management Models - বাড়ি ভাড়া ম্যানেজমেন্ট সিস্টেম"""

from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Property(models.Model):
    """প্রপার্টি - ফ্ল্যাট, গ্যারেজ, দোকান"""
    
    PROPERTY_TYPES = [
        ("FLAT", "ফ্ল্যাট"),
        ("GARAGE", "গ্যারেজ"),
        ("SHOP", "দোকান"),
    ]
    
    STATUS_CHOICES = [
        ("VACANT", "খালি"),
        ("OCCUPIED", "ভাড়া দেওয়া"),
        ("MAINTENANCE", "মেইনটেনেন্স"),
    ]
    
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="rental_properties",
    )
    property_type = models.CharField(max_length=10, choices=PROPERTY_TYPES)
    property_number = models.CharField(max_length=50, help_text="ইউনিক নম্বর (যেমন: F-101, G-05, S-01)")
    floor_number = models.CharField(max_length=20, blank=True, help_text="ফ্লোর নম্বর")
    size_sqft = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="সাইজ (বর্গফুট)"
    )
    bedrooms = models.PositiveSmallIntegerField(null=True, blank=True, help_text="বেডরুম সংখ্যা")
    bathrooms = models.PositiveSmallIntegerField(null=True, blank=True, help_text="বাথরুম সংখ্যা")
    monthly_rent = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="মাসিক ভাড়া"
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="VACANT")
    description = models.TextField(blank=True, help_text="বিস্তারিত বর্ণনা")
    current_tenant = models.ForeignKey(
        "RentalTenant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_property",
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_properties")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["property_type", "property_number"]
        unique_together = [("tenant", "property_number")]
        verbose_name = "Property"
        verbose_name_plural = "Properties"
    
    def __str__(self):
        return f"{self.get_property_type_display()} - {self.property_number}"



class RentalTenant(models.Model):
    """ভাড়াটিয়া তথ্য"""
    
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="rental_tenants",
    )
    name = models.CharField(max_length=255, help_text="নাম")
    mobile_number = models.CharField(max_length=20, help_text="মোবাইল নম্বর")
    email = models.EmailField(blank=True, help_text="ইমেইল")
    nid_number = models.CharField(max_length=50, blank=True, help_text="জাতীয় পরিচয়পত্র নম্বর")
    permanent_address = models.TextField(blank=True, help_text="স্থায়ী ঠিকানা")
    emergency_contact_name = models.CharField(max_length=255, blank=True, help_text="জরুরি যোগাযোগ - নাম")
    emergency_contact_number = models.CharField(max_length=20, blank=True, help_text="জরুরি যোগাযোগ - নম্বর")
    occupation = models.CharField(max_length=255, blank=True, help_text="পেশা")
    family_members_count = models.PositiveSmallIntegerField(default=1, help_text="পরিবারের সদস্য সংখ্যা")
    profile_photo = models.ImageField(upload_to="rental/tenants/photos/", null=True, blank=True)
    nid_photo_front = models.ImageField(upload_to="rental/tenants/nid/", null=True, blank=True)
    nid_photo_back = models.ImageField(upload_to="rental/tenants/nid/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_rental_tenants")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "mobile_number")]
        verbose_name = "Rental Tenant"
        verbose_name_plural = "Rental Tenants"
    
    def __str__(self):
        return f"{self.name} - {self.mobile_number}"



class RentalAgreement(models.Model):
    """ভাড়া চুক্তি"""
    
    STATUS_CHOICES = [
        ("ACTIVE", "সক্রিয়"),
        ("EXPIRED", "মেয়াদ শেষ"),
        ("TERMINATED", "বাতিল"),
    ]
    
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="rental_agreements",
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="agreements")
    rental_tenant = models.ForeignKey(RentalTenant, on_delete=models.CASCADE, related_name="agreements")
    start_date = models.DateField(help_text="চুক্তি শুরুর তারিখ")
    end_date = models.DateField(help_text="চুক্তি শেষের তারিখ")
    monthly_rent = models.DecimalField(max_digits=12, decimal_places=2, help_text="মাসিক ভাড়া")
    advance_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0"),
        help_text="অ্যাডভান্স টাকা"
    )
    advance_months = models.PositiveSmallIntegerField(default=0, help_text="অ্যাডভান্স কত মাসের")
    service_charge = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0"),
        help_text="সার্ভিস চার্জ"
    )
    rent_due_date = models.PositiveSmallIntegerField(
        default=5,
        help_text="প্রতি মাসে ভাড়া পরিশোধের তারিখ (১-৩১)"
    )
    agreement_document = models.FileField(
        upload_to="rental/agreements/",
        null=True,
        blank=True,
        help_text="চুক্তি ডকুমেন্ট (PDF)"
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="ACTIVE")
    notes = models.TextField(blank=True, help_text="অতিরিক্ত নোট")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_agreements")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-start_date"]
        verbose_name = "Rental Agreement"
        verbose_name_plural = "Rental Agreements"
    
    def __str__(self):
        return f"{self.property} - {self.rental_tenant.name} ({self.start_date})"
    
    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({"end_date": "শেষ তারিখ শুরুর তারিখের পরে হতে হবে"})
        if self.rent_due_date < 1 or self.rent_due_date > 31:
            raise ValidationError({"rent_due_date": "তারিখ ১ থেকে ৩১ এর মধ্যে হতে হবে"})



class Payment(models.Model):
    """পেমেন্ট রেকর্ড"""
    
    PAYMENT_TYPES = [
        ("RENT", "ভাড়া"),
        ("ADVANCE", "অ্যাডভান্স"),
        ("SERVICE_CHARGE", "সার্ভিস চার্জ"),
        ("OTHER", "অন্যান্য"),
    ]
    
    PAYMENT_METHODS = [
        ("CASH", "ক্যাশ"),
        ("BANK_TRANSFER", "ব্যাংক ট্রান্সফার"),
        ("CHEQUE", "চেক"),
        ("MOBILE_BANKING", "মোবাইল ব্যাংকিং"),
    ]
    
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="rental_payments",
    )
    agreement = models.ForeignKey(RentalAgreement, on_delete=models.CASCADE, related_name="payments")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    payment_month = models.DateField(
        null=True, 
        blank=True,
        help_text="যে মাসের জন্য পেমেন্ট (শুধু RENT এর জন্য)"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="পরিমাণ")
    payment_date = models.DateField(help_text="পেমেন্ট তারিখ")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_reference = models.CharField(max_length=255, blank=True, help_text="ট্রানজেকশন রেফারেন্স")
    receipt_number = models.CharField(max_length=50, unique=True, help_text="রিসিপ্ট নম্বর")
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_payments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-payment_date"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
    
    def __str__(self):
        return f"{self.receipt_number} - {self.amount} ({self.payment_date})"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Auto-generate receipt number
            last_payment = Payment.objects.filter(tenant=self.tenant).order_by("-id").first()
            if last_payment and last_payment.receipt_number.startswith("RCP"):
                try:
                    last_num = int(last_payment.receipt_number[3:])
                    self.receipt_number = f"RCP{last_num + 1:06d}"
                except ValueError:
                    self.receipt_number = f"RCP{timezone.now().strftime('%Y%m%d%H%M%S')}"
            else:
                self.receipt_number = f"RCP{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)



class DuePayment(models.Model):
    """বকেয়া পেমেন্ট ট্র্যাকিং"""
    
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="rental_due_payments",
    )
    agreement = models.ForeignKey(RentalAgreement, on_delete=models.CASCADE, related_name="due_payments")
    due_month = models.DateField(help_text="বকেয়া মাস")
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="বকেয়া পরিমাণ")
    due_date = models.DateField(help_text="বকেয়া তারিখ")
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False, help_text="SMS রিমাইন্ডার পাঠানো হয়েছে")
    reminder_count = models.PositiveSmallIntegerField(default=0, help_text="কতবার রিমাইন্ডার পাঠানো হয়েছে")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-due_month"]
        unique_together = [("agreement", "due_month")]
        verbose_name = "Due Payment"
        verbose_name_plural = "Due Payments"
    
    def __str__(self):
        status = "পরিশোধিত" if self.is_paid else "বকেয়া"
        return f"{self.agreement.rental_tenant.name} - {self.due_month.strftime('%B %Y')} ({status})"



class SMSLog(models.Model):
    """SMS লগ - নোটিফিকেশন ট্র্যাকিং"""
    
    MESSAGE_TYPES = [
        ("REMINDER", "পেমেন্ট রিমাইন্ডার"),
        ("DUE_NOTICE", "বকেয়া নোটিশ"),
        ("CONTRACT_EXPIRY", "চুক্তি শেষ হওয়ার নোটিশ"),
        ("PAYMENT_RECEIVED", "পেমেন্ট প্রাপ্তি"),
        ("CUSTOM", "কাস্টম মেসেজ"),
    ]
    
    STATUS_CHOICES = [
        ("PENDING", "পেন্ডিং"),
        ("SENT", "পাঠানো হয়েছে"),
        ("FAILED", "ব্যর্থ"),
    ]
    
    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="rental_sms_logs",
    )
    rental_tenant = models.ForeignKey(
        RentalTenant,
        on_delete=models.CASCADE,
        related_name="sms_logs",
        null=True,
        blank=True,
    )
    mobile_number = models.CharField(max_length=20)
    message_text = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "SMS Log"
        verbose_name_plural = "SMS Logs"
    
    def __str__(self):
        return f"{self.mobile_number} - {self.get_message_type_display()} ({self.status})"
