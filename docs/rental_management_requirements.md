# রেন্টাল ম্যানেজমেন্ট সিস্টেম - রিকোয়ারমেন্ট ডকুমেন্ট

## প্রজেক্ট ওভারভিউ
একটি সম্পূর্ণ বাড়ি ভাড়া ম্যানেজমেন্ট সিস্টেম যেখানে বাড়িওয়ালা তার ফ্ল্যাট, দোকান, গ্যারেজ এবং ভাড়াটিয়াদের সম্পূর্ণ তথ্য ম্যানেজ করতে পারবেন।

## বিজনেস রিকোয়ারমেন্ট

### ১. প্রপার্টি ম্যানেজমেন্ট
- **ফ্ল্যাট ম্যানেজমেন্ট**: ৪০টি ফ্ল্যাট
- **গ্যারেজ ম্যানেজমেন্ট**: ৪০টি গ্যারেজ
- **দোকান ম্যানেজমেন্ট**: ১০টি দোকান

প্রতিটি প্রপার্টির জন্য:
- ইউনিক নম্বর/আইডি
- ফ্লোর নম্বর
- সাইজ (বর্গফুট)
- ভাড়ার পরিমাণ
- বর্তমান স্ট্যাটাস (খালি/ভাড়া দেওয়া)
- সুবিধা (বেডরুম, বাথরুম সংখ্যা ইত্যাদি)

### ২. ভাড়াটিয়া ম্যানেজমেন্ট
- নাম, মোবাইল নম্বর, ইমেইল
- জাতীয় পরিচয়পত্র নম্বর
- স্থায়ী ঠিকানা
- জরুরি যোগাযোগের তথ্য
- পরিবারের সদস্য সংখ্যা
- পেশা/ব্যবসার তথ্য
- ছবি (প্রোফাইল ও ডকুমেন্ট)

### ৩. ভাড়া চুক্তি ম্যানেজমেন্ট
- চুক্তি শুরুর তারিখ
- চুক্তির মেয়াদ
- মাসিক ভাড়ার পরিমাণ
- অ্যাডভান্স টাকার পরিমাণ
- অ্যাডভান্স কত মাসের
- সার্ভিস চার্জ (যদি থাকে)
- ইউটিলিটি বিল কে দিবে
- ভাড়া পরিশোধের তারিখ (প্রতি মাসে)
- চুক্তি নবায়নের তথ্য

### ৪. পেমেন্ট ম্যানেজমেন্ট
- মাসিক ভাড়া পেমেন্ট রেকর্ড
- অ্যাডভান্স পেমেন্ট রেকর্ড
- বকেয়া হিসাব
- পেমেন্ট মেথড (ক্যাশ/ব্যাংক ট্রান্সফার/চেক)
- পেমেন্ট রিসিপ্ট জেনারেশন
- পেমেন্ট হিস্ট্রি

### ৫. নোটিফিকেশন সিস্টেম
- **SMS নোটিফিকেশন**:
  - ভাড়া বকেয়া হলে অটোমেটিক SMS
  - ভাড়া পরিশোধের ৩ দিন আগে রিমাইন্ডার
  - চুক্তি শেষ হওয়ার ১ মাস আগে নোটিফিকেশন
- **ইমেইল নোটিফিকেশন** (অপশনাল)
- **ইন-অ্যাপ নোটিফিকেশন**

### ৬. রিপোর্ট ও ড্যাশবোর্ড
- মোট ভাড়া আয় (মাসিক/বার্ষিক)
- বকেয়া ভাড়ার তালিকা
- খালি প্রপার্টির তালিকা
- ভাড়াটিয়াদের তালিকা
- পেমেন্ট হিস্ট্রি রিপোর্ট
- প্রপার্টি অকুপেন্সি রেট

---

## টেকনিক্যাল রিকোয়ারমেন্ট

### ১. ডাটাবেস মডেল স্ট্রাকচার

#### Property (প্রপার্টি)
```python
- id (PK)
- property_type (FLAT/GARAGE/SHOP)
- property_number (ইউনিক)
- floor_number
- size_sqft
- bedrooms (ফ্ল্যাটের জন্য)
- bathrooms (ফ্ল্যাটের জন্য)
- monthly_rent
- status (VACANT/OCCUPIED/MAINTENANCE)
- description
- tenant (FK - বর্তমান ভাড়াটিয়া)
- created_at
- updated_at
```

#### Tenant (ভাড়াটিয়া)
```python
- id (PK)
- name
- mobile_number (ইউনিক)
- email
- nid_number
- permanent_address
- emergency_contact_name
- emergency_contact_number
- occupation
- family_members_count
- profile_photo
- nid_photo_front
- nid_photo_back
- tenant (FK - auth_tenants.Tenant)
- created_by (FK - User)
- created_at
- updated_at
```

#### RentalAgreement (ভাড়া চুক্তি)
```python
- id (PK)
- property (FK)
- tenant (FK)
- start_date
- end_date
- monthly_rent
- advance_amount
- advance_months
- service_charge
- rent_due_date (প্রতি মাসে কত তারিখে)
- agreement_document (PDF upload)
- status (ACTIVE/EXPIRED/TERMINATED)
- notes
- created_by (FK - User)
- created_at
- updated_at
```

#### Payment (পেমেন্ট)
```python
- id (PK)
- agreement (FK)
- payment_type (RENT/ADVANCE/SERVICE_CHARGE)
- payment_month (যে মাসের জন্য)
- amount
- payment_date
- payment_method (CASH/BANK_TRANSFER/CHEQUE)
- transaction_reference
- receipt_number (অটো জেনারেট)
- notes
- created_by (FK - User)
- created_at
```

#### DuePayment (বকেয়া)
```python
- id (PK)
- agreement (FK)
- due_month
- due_amount
- due_date
- is_paid
- paid_date
- reminder_sent (SMS পাঠানো হয়েছে কিনা)
- reminder_count
- created_at
- updated_at
```

#### SMSLog (SMS লগ)
```python
- id (PK)
- tenant (FK)
- mobile_number
- message_text
- message_type (REMINDER/DUE_NOTICE/CONTRACT_EXPIRY)
- status (SENT/FAILED/PENDING)
- sent_at
- error_message
```

### ২. প্রয়োজনীয় ফিচার লিস্ট

#### ড্যাশবোর্ড
- [ ] মোট প্রপার্টি সংখ্যা (ফ্ল্যাট/গ্যারেজ/দোকান)
- [ ] খালি প্রপার্টি সংখ্যা
- [ ] মোট ভাড়াটিয়া সংখ্যা
- [ ] এই মাসের মোট আয়
- [ ] মোট বকেয়া টাকা
- [ ] আজকের পেমেন্ট লিস্ট
- [ ] বকেয়া ভাড়াটিয়াদের লিস্ট
- [ ] চুক্তি শেষ হতে যাচ্ছে এমন লিস্ট

#### প্রপার্টি ম্যানেজমেন্ট
- [ ] নতুন প্রপার্টি যোগ করা
- [ ] প্রপার্টি এডিট করা
- [ ] প্রপার্টি ডিলিট করা
- [ ] প্রপার্টি লিস্ট দেখা (ফিল্টার: টাইপ, স্ট্যাটাস)
- [ ] প্রপার্টি সার্চ করা
- [ ] খালি প্রপার্টি দেখা

#### ভাড়াটিয়া ম্যানেজমেন্ট
- [ ] নতুন ভাড়াটিয়া যোগ করা
- [ ] ভাড়াটিয়া তথ্য এডিট করা
- [ ] ভাড়াটিয়া প্রোফাইল দেখা
- [ ] ভাড়াটিয়া লিস্ট দেখা
- [ ] ভাড়াটিয়া সার্চ করা
- [ ] ভাড়াটিয়ার পেমেন্ট হিস্ট্রি দেখা

#### চুক্তি ম্যানেজমেন্ট
- [ ] নতুন চুক্তি তৈরি করা
- [ ] চুক্তি এডিট করা
- [ ] চুক্তি রিনিউ করা
- [ ] চুক্তি টার্মিনেট করা
- [ ] চুক্তি লিস্ট দেখা
- [ ] চুক্তি ডিটেইলস দেখা
- [ ] চুক্তি ডকুমেন্ট আপলোড/ডাউনলোড

#### পেমেন্ট ম্যানেজমেন্ট
- [ ] পেমেন্ট রেকর্ড করা
- [ ] পেমেন্ট এডিট করা
- [ ] পেমেন্ট রিসিপ্ট জেনারেট করা (PDF)
- [ ] পেমেন্ট হিস্ট্রি দেখা
- [ ] বকেয়া পেমেন্ট লিস্ট দেখা
- [ ] মাসিক পেমেন্ট রিপোর্ট

#### SMS নোটিফিকেশন
- [ ] বকেয়া রিমাইন্ডার SMS পাঠানো
- [ ] পেমেন্ট রিমাইন্ডার SMS পাঠানো
- [ ] চুক্তি শেষ হওয়ার নোটিফিকেশন
- [ ] SMS টেমপ্লেট কাস্টমাইজ করা
- [ ] SMS লগ দেখা
- [ ] ম্যানুয়াল SMS পাঠানো

#### রিপোর্ট
- [ ] মাসিক আয় রিপোর্ট
- [ ] বার্ষিক আয় রিপোর্ট
- [ ] বকেয়া রিপোর্ট
- [ ] প্রপার্টি অকুপেন্সি রিপোর্ট
- [ ] ভাড়াটিয়া রিপোর্ট
- [ ] পেমেন্ট হিস্ট্রি রিপোর্ট
- [ ] রিপোর্ট এক্সপোর্ট (PDF/Excel)

### ৩. SMS সার্ভিস ইন্টিগ্রেশন

বাংলাদেশের জনপ্রিয় SMS গেটওয়ে সার্ভিস:
- **SSL Wireless** (https://sslwireless.com/)
- **Bulk SMS BD** (https://bulksmsbd.com/)
- **Muthofun** (https://muthofun.com/)
- **Banglalink SMS API**
- **Grameenphone SMS API**

প্রয়োজনীয় কনফিগারেশন:
```python
SMS_GATEWAY_URL = "https://api.sslwireless.com/sms/send"
SMS_API_KEY = "your_api_key"
SMS_SENDER_ID = "8801XXXXXXXXX"
```

### ৪. প্রয়োজনীয় Python প্যাকেজ

```txt
# বিদ্যমান প্যাকেজের সাথে যোগ করতে হবে:
django-phonenumber-field==7.3.0  # মোবাইল নম্বর ভ্যালিডেশন
phonenumbers==8.13.29
pillow==10.2.0  # ইমেজ প্রসেসিং (ইতিমধ্যে থাকতে পারে)
reportlab==4.0.9  # PDF রিসিপ্ট জেনারেশন
celery==5.3.6  # ব্যাকগ্রাউন্ড টাস্ক (SMS পাঠানো)
redis==5.0.1  # Celery ব্রোকার
requests==2.31.0  # SMS API কল
openpyxl==3.1.2  # Excel এক্সপোর্ট
```

### ৫. ইউজার রোল ও পারমিশন

আপনার বিদ্যমান সিস্টেমে যোগ করতে হবে:

```python
# Permission categories এ যোগ করুন:
("rental", "Rental Management"),

# নতুন Permissions:
- rental.view_property
- rental.add_property
- rental.change_property
- rental.delete_property
- rental.view_tenant
- rental.add_tenant
- rental.change_tenant
- rental.delete_tenant
- rental.view_agreement
- rental.add_agreement
- rental.change_agreement
- rental.terminate_agreement
- rental.view_payment
- rental.add_payment
- rental.change_payment
- rental.delete_payment
- rental.send_sms
- rental.view_reports
- rental.export_reports
```

### ৬. API এন্ডপয়েন্ট (REST API)

```
# Properties
GET    /api/rental/properties/
POST   /api/rental/properties/
GET    /api/rental/properties/{id}/
PUT    /api/rental/properties/{id}/
DELETE /api/rental/properties/{id}/
GET    /api/rental/properties/vacant/

# Tenants
GET    /api/rental/tenants/
POST   /api/rental/tenants/
GET    /api/rental/tenants/{id}/
PUT    /api/rental/tenants/{id}/
DELETE /api/rental/tenants/{id}/

# Agreements
GET    /api/rental/agreements/
POST   /api/rental/agreements/
GET    /api/rental/agreements/{id}/
PUT    /api/rental/agreements/{id}/
POST   /api/rental/agreements/{id}/renew/
POST   /api/rental/agreements/{id}/terminate/

# Payments
GET    /api/rental/payments/
POST   /api/rental/payments/
GET    /api/rental/payments/{id}/
GET    /api/rental/payments/{id}/receipt/
GET    /api/rental/payments/due/

# SMS
POST   /api/rental/sms/send/
POST   /api/rental/sms/send-reminder/
GET    /api/rental/sms/logs/

# Reports
GET    /api/rental/reports/dashboard/
GET    /api/rental/reports/monthly-income/
GET    /api/rental/reports/due-list/
GET    /api/rental/reports/occupancy/
```

### ৭. ফ্রন্টএন্ড পেজ স্ট্রাকচার

```
/rental/
  ├── dashboard/              # ড্যাশবোর্ড
  ├── properties/             # প্রপার্টি লিস্ট
  │   ├── add/               # নতুন প্রপার্টি
  │   ├── {id}/edit/         # এডিট
  │   └── {id}/              # ডিটেইলস
  ├── tenants/               # ভাড়াটিয়া লিস্ট
  │   ├── add/
  │   ├── {id}/edit/
  │   └── {id}/              # প্রোফাইল
  ├── agreements/            # চুক্তি লিস্ট
  │   ├── add/
  │   ├── {id}/edit/
  │   └── {id}/              # ডিটেইলস
  ├── payments/              # পেমেন্ট লিস্ট
  │   ├── add/
  │   └── due/               # বকেয়া লিস্ট
  ├── sms/                   # SMS ম্যানেজমেন্ট
  │   ├── send/
  │   └── logs/
  └── reports/               # রিপোর্ট
      ├── income/
      ├── due/
      └── occupancy/
```

---

## ইমপ্লিমেন্টেশন স্টেপ

### Phase 1: কোর মডেল ও বেসিক CRUD (১-২ সপ্তাহ)
1. Django অ্যাপ তৈরি করা (`rental`)
2. মডেল তৈরি করা (Property, Tenant, RentalAgreement, Payment)
3. Admin প্যানেল সেটআপ
4. বেসিক API এন্ডপয়েন্ট তৈরি
5. সিরিয়ালাইজার ও ভিউ তৈরি

### Phase 2: পেমেন্ট ও বকেয়া সিস্টেম (১ সপ্তাহ)
1. Payment মডেল ইমপ্লিমেন্ট
2. DuePayment মডেল ও অটো ক্যালকুলেশন
3. পেমেন্ট রিসিপ্ট জেনারেশন (PDF)
4. বকেয়া ট্র্যাকিং সিস্টেম

### Phase 3: SMS নোটিফিকেশন (১ সপ্তাহ)
1. SMS গেটওয়ে ইন্টিগ্রেশন
2. Celery সেটআপ (ব্যাকগ্রাউন্ড টাস্ক)
3. অটোমেটিক রিমাইন্ডার সিস্টেম
4. SMS টেমপ্লেট ম্যানেজমেন্ট
5. SMS লগিং

### Phase 4: রিপোর্ট ও ড্যাশবোর্ড (১ সপ্তাহ)
1. ড্যাশবোর্ড API
2. বিভিন্ন রিপোর্ট API
3. রিপোর্ট এক্সপোর্ট (PDF/Excel)
4. চার্ট ও গ্রাফ ডেটা

### Phase 5: ফ্রন্টএন্ড (২-৩ সপ্তাহ)
1. ড্যাশবোর্ড UI
2. প্রপার্টি ম্যানেজমেন্ট UI
3. ভাড়াটিয়া ম্যানেজমেন্ট UI
4. পেমেন্ট ম্যানেজমেন্ট UI
5. রিপোর্ট UI

### Phase 6: টেস্টিং ও ডিপ্লয়মেন্ট (১ সপ্তাহ)
1. ইউনিট টেস্ট
2. ইন্টিগ্রেশন টেস্ট
3. ইউজার অ্যাকসেপ্টেন্স টেস্টিং
4. প্রোডাকশন ডিপ্লয়মেন্ট

---

## সিকিউরিটি কনসিডারেশন

1. **ডেটা প্রাইভেসি**: ভাড়াটিয়াদের ব্যক্তিগত তথ্য সুরক্ষিত রাখা
2. **টেন্যান্ট আইসোলেশন**: প্রতিটি বাড়িওয়ালা শুধু নিজের ডেটা দেখতে পারবে
3. **পারমিশন চেক**: সব API এ proper permission চেক
4. **ফাইল আপলোড ভ্যালিডেশন**: শুধু ইমেজ ও PDF আপলোড
5. **SMS রেট লিমিটিং**: অতিরিক্ত SMS পাঠানো থেকে বিরত রাখা

---

## কস্ট এস্টিমেশন

### SMS খরচ (মাসিক)
- প্রতি SMS: ০.২৫ - ০.৫০ টাকা
- মাসিক SMS (৫০ ভাড়াটিয়া × ৩ SMS): ~৭৫ টাকা
- বার্ষিক: ~৯০০ টাকা

### হোস্টিং খরচ (মাসিক)
- শেয়ার্ড হোস্টিং: ৫০০-১০০০ টাকা
- VPS: ১৫০০-৩০০০ টাকা
- ক্লাউড (AWS/DigitalOcean): ১০০০-৫০০০ টাকা

### ডেভেলপমেন্ট টাইম
- মোট সময়: ৭-১০ সপ্তাহ
- ১ জন ডেভেলপার (ফুল-টাইম)

---

## পরবর্তী ধাপ

1. এই রিকোয়ারমেন্ট ডকুমেন্ট রিভিউ করুন
2. প্রয়োজনীয় পরিবর্তন বা সংযোজন জানান
3. SMS গেটওয়ে সিলেক্ট করুন
4. ডেভেলপমেন্ট শুরু করার অনুমতি দিন

---

**নোট**: এই সিস্টেম আপনার বিদ্যমান Django প্রজেক্টের সাথে সম্পূর্ণভাবে ইন্টিগ্রেট হবে এবং একই টেন্যান্ট সিস্টেম ব্যবহার করবে।
