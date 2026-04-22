# Rental Management System - Quick Start Guide

## সিস্টেম ওভারভিউ

রেন্টাল ম্যানেজমেন্ট সিস্টেম আপনার বাড়ির ফ্ল্যাট, গ্যারেজ, দোকান এবং ভাড়াটিয়াদের সম্পূর্ণ তথ্য ম্যানেজ করতে সাহায্য করবে।

## ইনস্টলেশন সম্পন্ন হয়েছে ✓

সিস্টেম ইতিমধ্যে ইনস্টল করা হয়েছে এবং ডাটাবেস মাইগ্রেশন সম্পন্ন হয়েছে।

## পরবর্তী ধাপসমূহ

### ১. SMS Gateway কনফিগারেশন

`.env` ফাইলে নিচের লাইনগুলো যোগ করুন:

```env
# SMS Gateway Configuration
SMS_GATEWAY_URL=https://api.sslwireless.com/sms/send
SMS_API_KEY=your_api_key_here
SMS_SENDER_ID=8801XXXXXXXXX
```

**জনপ্রিয় SMS Gateway প্রোভাইডার:**
- SSL Wireless: https://sslwireless.com/
- Bulk SMS BD: https://bulksmsbd.com/
- Muthofun: https://muthofun.com/

### ২. Module Activation

Django shell খুলুন:
```bash
python manage.py shell
```

Module enable করুন:
```python
from auth_tenants.models import Tenant, TenantModuleSubscription

# আপনার tenant খুঁজুন
tenant = Tenant.objects.first()  # অথবা specific slug দিয়ে
print(f"Tenant: {tenant.name}")

# Rental module enable করুন
TenantModuleSubscription.objects.get_or_create(
    tenant=tenant,
    module_code="rental",
    defaults={"is_enabled": True}
)

print("✓ Rental module enabled!")
```

### ৩. Permissions Setup

```python
from auth_tenants.services.permission_catalog import sync_default_model_permissions

# Rental permissions sync করুন
sync_default_model_permissions(["rental"])
print("✓ Permissions synced!")
```

### ৪. Sample Data তৈরি করুন (Optional)

Testing এর জন্য sample data তৈরি করতে:

```bash
python manage.py create_sample_rental_data --tenant-slug=your-tenant-slug
```

এটি তৈরি করবে:
- ১০টি ফ্ল্যাট
- ৫টি গ্যারেজ
- ৩টি দোকান
- ৫ জন ভাড়াটিয়া
- ৫টি সক্রিয় চুক্তি

### ৫. Admin Panel Access

Django admin panel এ যান:
```
http://localhost:8000/admin/
```

নিচের মডেলগুলো দেখতে পারবেন:
- Properties (প্রপার্টি)
- Rental Tenants (ভাড়াটিয়া)
- Rental Agreements (চুক্তি)
- Payments (পেমেন্ট)
- Due Payments (বকেয়া)
- SMS Logs (SMS লগ)

## API Testing

### API Documentation

Swagger UI দেখুন:
```
http://localhost:8000/api/schema/swagger-ui/
```

### Dashboard API Test

```bash
curl -X GET "http://localhost:8000/api/rental/dashboard/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create Property

```bash
curl -X POST "http://localhost:8000/api/rental/properties/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "property_type": "FLAT",
    "property_number": "F-101",
    "floor_number": "1st Floor",
    "size_sqft": 1200,
    "bedrooms": 3,
    "bathrooms": 2,
    "monthly_rent": 15000,
    "status": "VACANT",
    "description": "৩ বেডরুম ফ্ল্যাট"
  }'
```

### Get Properties List

```bash
curl -X GET "http://localhost:8000/api/rental/properties/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Vacant Properties

```bash
curl -X GET "http://localhost:8000/api/rental/properties/vacant/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Automated Tasks Setup

### Linux/Mac - Cron Jobs

```bash
crontab -e
```

Add:
```cron
# Create monthly dues on 1st of every month at 1 AM
0 1 1 * * cd /path/to/project && /path/to/venv/bin/python manage.py process_rental_dues --create-dues

# Send SMS reminders daily at 10 AM
0 10 * * * cd /path/to/project && /path/to/venv/bin/python manage.py process_rental_dues --send-sms
```

### Windows - Task Scheduler

1. Create `process_dues.bat`:
```batch
@echo off
cd C:\path\to\project
.venv\Scripts\python.exe manage.py process_rental_dues --create-dues --send-sms
```

2. Open Task Scheduler
3. Create Basic Task
4. Set trigger: Daily at 10:00 AM
5. Action: Start a program
6. Program: `C:\path\to\project\process_dues.bat`

## Common Workflows

### ১. নতুন প্রপার্টি যোগ করা

Admin Panel → Properties → Add Property
- Property Type সিলেক্ট করুন
- Property Number দিন (যেমন: F-101)
- Monthly Rent দিন
- Status: VACANT রাখুন

### ২. নতুন ভাড়াটিয়া যোগ করা

Admin Panel → Rental Tenants → Add Rental Tenant
- নাম, মোবাইল নম্বর দিন
- NID নম্বর দিন
- ছবি আপলোড করুন (optional)

### ৩. চুক্তি তৈরি করা

Admin Panel → Rental Agreements → Add Rental Agreement
- Property সিলেক্ট করুন
- Rental Tenant সিলেক্ট করুন
- Start Date ও End Date দিন
- Monthly Rent, Advance Amount দিন
- Status: ACTIVE রাখুন

সেভ করার পর:
- Property এর status automatically "OCCUPIED" হবে
- Current Tenant সেট হবে

### ৪. পেমেন্ট রেকর্ড করা

Admin Panel → Payments → Add Payment
- Agreement সিলেক্ট করুন
- Payment Type সিলেক্ট করুন (RENT/ADVANCE)
- Amount ও Payment Date দিন
- Payment Method সিলেক্ট করুন
- Receipt Number automatically generate হবে

### ৫. বকেয়া দেখা

Admin Panel → Due Payments
- Filter by "Is paid: No" দিয়ে বকেয়া দেখুন
- Reminder sent দেখুন কতবার SMS পাঠানো হয়েছে

### ৬. SMS পাঠানো

Terminal এ:
```bash
# সব বকেয়া ভাড়াটিয়াদের SMS পাঠান
python manage.py process_rental_dues --send-sms
```

অথবা Python code এ:
```python
from rental_management.services import SMSService
from rental_management.models import DuePayment

# একটি specific due এর জন্য SMS পাঠান
due = DuePayment.objects.filter(is_paid=False).first()
result = SMSService.send_due_reminder(due)
print(result)
```

## Troubleshooting

### SMS পাঠানো যাচ্ছে না

1. `.env` ফাইলে SMS configuration চেক করুন
2. SMS Gateway API key valid কিনা চেক করুন
3. SMS Log দেখুন error message এর জন্য:
   ```python
   from rental_management.models import SMSLog
   SMSLog.objects.filter(status="FAILED").values("error_message")
   ```

### Permission Error

1. Permission sync করুন:
   ```bash
   python manage.py shell
   ```
   ```python
   from auth_tenants.services.permission_catalog import sync_default_model_permissions
   sync_default_model_permissions(["rental"])
   ```

2. User এর role চেক করুন
3. TenantPermissionGrant চেক করুন

### Module দেখা যাচ্ছে না

1. Module enabled কিনা চেক করুন:
   ```python
   from auth_tenants.models import TenantModuleSubscription
   TenantModuleSubscription.objects.filter(module_code="rental")
   ```

2. INSTALLED_APPS এ `rental_management` আছে কিনা চেক করুন

## Next Steps

1. Frontend UI তৈরি করুন (React/Vue/Angular)
2. PDF receipt generation implement করুন
3. Excel export functionality যোগ করুন
4. Advanced reporting তৈরি করুন
5. Mobile app তৈরি করুন

## Support

সমস্যা হলে:
1. `rental_management/README.md` দেখুন
2. API documentation দেখুন: `/api/schema/swagger-ui/`
3. Development team এর সাথে যোগাযোগ করুন

---

**সিস্টেম সফলভাবে ইনস্টল হয়েছে! 🎉**
