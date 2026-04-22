# Rental Management System

বাড়ি ভাড়া ম্যানেজমেন্ট সিস্টেম - ফ্ল্যাট, গ্যারেজ, দোকান ম্যানেজমেন্ট

## Features

- ✅ প্রপার্টি ম্যানেজমেন্ট (ফ্ল্যাট, গ্যারেজ, দোকান)
- ✅ ভাড়াটিয়া তথ্য ম্যানেজমেন্ট
- ✅ ভাড়া চুক্তি ম্যানেজমেন্ট
- ✅ পেমেন্ট ট্র্যাকিং
- ✅ বকেয়া হিসাব
- ✅ SMS নোটিফিকেশন
- ✅ ড্যাশবোর্ড ও রিপোর্ট
- ✅ REST API

## Installation

### 1. Database Migration

```bash
python manage.py migrate
```

### 2. SMS Gateway Configuration

`.env` ফাইলে SMS gateway configuration যোগ করুন:

```env
# SMS Gateway (SSL Wireless / Bulk SMS BD)
SMS_GATEWAY_URL=https://api.sslwireless.com/sms/send
SMS_API_KEY=your_api_key_here
SMS_SENDER_ID=8801XXXXXXXXX
```

### 3. Module Activation

Tenant এর জন্য Rental module enable করুন:

```python
from auth_tenants.models import Tenant, TenantModuleSubscription

tenant = Tenant.objects.get(slug="your-tenant-slug")
TenantModuleSubscription.objects.create(
    tenant=tenant,
    module_code="rental",
    is_enabled=True
)
```

### 4. Permissions Setup

```bash
python manage.py shell
```

```python
from auth_tenants.services.permission_catalog import sync_default_model_permissions

# Sync rental permissions
sync_default_model_permissions(["rental"])
```

## API Endpoints

### Dashboard
```
GET /api/rental/dashboard/
```

### Properties
```
GET    /api/rental/properties/
POST   /api/rental/properties/
GET    /api/rental/properties/{id}/
PUT    /api/rental/properties/{id}/
DELETE /api/rental/properties/{id}/
GET    /api/rental/properties/vacant/
```

### Tenants
```
GET    /api/rental/tenants/
POST   /api/rental/tenants/
GET    /api/rental/tenants/{id}/
PUT    /api/rental/tenants/{id}/
DELETE /api/rental/tenants/{id}/
```

### Agreements
```
GET    /api/rental/agreements/
POST   /api/rental/agreements/
GET    /api/rental/agreements/{id}/
PUT    /api/rental/agreements/{id}/
POST   /api/rental/agreements/{id}/terminate/
```

### Payments
```
GET    /api/rental/payments/
POST   /api/rental/payments/
GET    /api/rental/payments/{id}/
```

### Due Payments
```
GET    /api/rental/dues/
GET    /api/rental/dues/overdue/
```

### SMS Logs
```
GET    /api/rental/sms-logs/
```

## Management Commands

### Create Monthly Dues
```bash
python manage.py process_rental_dues --create-dues
```

### Send SMS Reminders
```bash
python manage.py process_rental_dues --send-sms
```

### Both
```bash
python manage.py process_rental_dues --create-dues --send-sms
```

## Cron Job Setup (Linux)

```bash
crontab -e
```

Add these lines:

```cron
# Create dues on 1st of every month at 1 AM
0 1 1 * * cd /path/to/project && python manage.py process_rental_dues --create-dues

# Send reminders daily at 10 AM
0 10 * * * cd /path/to/project && python manage.py process_rental_dues --send-sms
```

## Windows Task Scheduler

Create a batch file `process_rental_dues.bat`:

```batch
@echo off
cd C:\path\to\project
python manage.py process_rental_dues --create-dues --send-sms
```

Schedule it in Task Scheduler to run daily.

## Usage Examples

### Create Property

```python
from rental_management.models import Property

property = Property.objects.create(
    tenant=tenant,
    property_type="FLAT",
    property_number="F-101",
    floor_number="1st Floor",
    size_sqft=1200,
    bedrooms=3,
    bathrooms=2,
    monthly_rent=15000,
    status="VACANT",
    created_by=user
)
```

### Create Rental Tenant

```python
from rental_management.models import RentalTenant

rental_tenant = RentalTenant.objects.create(
    tenant=tenant,
    name="আব্দুল করিম",
    mobile_number="01712345678",
    email="karim@example.com",
    nid_number="1234567890",
    occupation="ব্যবসা",
    family_members_count=4,
    created_by=user
)
```

### Create Agreement

```python
from rental_management.models import RentalAgreement
from datetime import date
from dateutil.relativedelta import relativedelta

agreement = RentalAgreement.objects.create(
    tenant=tenant,
    property=property,
    rental_tenant=rental_tenant,
    start_date=date.today(),
    end_date=date.today() + relativedelta(years=1),
    monthly_rent=15000,
    advance_amount=45000,
    advance_months=3,
    service_charge=500,
    rent_due_date=5,
    status="ACTIVE",
    created_by=user
)

# Update property status
property.status = "OCCUPIED"
property.current_tenant = rental_tenant
property.save()
```

### Record Payment

```python
from rental_management.models import Payment

payment = Payment.objects.create(
    tenant=tenant,
    agreement=agreement,
    payment_type="RENT",
    payment_month=date.today().replace(day=1),
    amount=15500,
    payment_date=date.today(),
    payment_method="CASH",
    created_by=user
)
```

### Send SMS

```python
from rental_management.services import SMSService

result = SMSService.send_sms(
    mobile_number="01712345678",
    message="আপনার ভাড়া পেমেন্ট সফল হয়েছে। ধন্যবাদ।",
    tenant_id=tenant.id,
    rental_tenant_id=rental_tenant.id,
    message_type="PAYMENT_RECEIVED"
)

print(result)  # {"success": True, "message": "SMS sent successfully", "log_id": 1}
```

## Permissions

Required permissions for different operations:

- `rental.view_property` - View properties
- `rental.add_property` - Add new property
- `rental.change_property` - Edit property
- `rental.delete_property` - Delete property
- `rental.view_tenant` - View tenants
- `rental.add_tenant` - Add new tenant
- `rental.change_tenant` - Edit tenant
- `rental.view_agreement` - View agreements
- `rental.add_agreement` - Create agreement
- `rental.change_agreement` - Edit agreement
- `rental.view_payment` - View payments
- `rental.add_payment` - Record payment
- `rental.send_sms` - Send SMS

## Models

### Property
- প্রপার্টি টাইপ (ফ্ল্যাট/গ্যারেজ/দোকান)
- প্রপার্টি নম্বর
- মাসিক ভাড়া
- স্ট্যাটাস (খালি/ভাড়া দেওয়া)

### RentalTenant
- নাম, মোবাইল, ইমেইল
- NID নম্বর
- পরিবারের সদস্য সংখ্যা
- ডকুমেন্ট (ছবি, NID)

### RentalAgreement
- প্রপার্টি ও ভাড়াটিয়া
- চুক্তির মেয়াদ
- মাসিক ভাড়া ও অ্যাডভান্স
- স্ট্যাটাস

### Payment
- পেমেন্ট টাইপ (ভাড়া/অ্যাডভান্স)
- পরিমাণ ও তারিখ
- পেমেন্ট মেথড
- রিসিপ্ট নম্বর

### DuePayment
- বকেয়া মাস ও পরিমাণ
- পরিশোধ স্ট্যাটাস
- রিমাইন্ডার কাউন্ট

### SMSLog
- মোবাইল নম্বর
- মেসেজ টেক্সট
- স্ট্যাটাস (পাঠানো/ব্যর্থ)

## Support

For issues or questions, contact the development team.
