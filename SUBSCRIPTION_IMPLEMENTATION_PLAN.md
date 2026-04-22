# 🚀 Subscription System Implementation Plan

## 📋 **Step-by-Step Implementation Guide**

### **Phase 1: Enhanced Models (1-2 days)**

#### 1.1 Update auth_tenants/models.py
```bash
# Add these models to your existing auth_tenants/models.py
```

#### 1.2 Create Migration
```bash
python manage.py makemigrations auth_tenants
python manage.py migrate
```

#### 1.3 Create Sample Data
```python
# Create management command: auth_tenants/management/commands/setup_subscription_plans.py
from django.core.management.base import BaseCommand
from auth_tenants.models import SubscriptionPlan

class Command(BaseCommand):
    def handle(self, *args, **options):
        plans = [
            {
                'name': 'Free Trial',
                'plan_type': 'free',
                'price_monthly': 0,
                'price_yearly': 0,
                'max_users': 3,
                'max_storage_gb': 1,
                'max_api_calls_per_month': 500,
                'included_modules': ['foundation', 'auth_tenants', 'chat']
            },
            {
                'name': 'Basic Plan',
                'plan_type': 'basic', 
                'price_monthly': 2000,  # 2000 BDT
                'price_yearly': 20000,  # 20000 BDT (2 months free)
                'max_users': 10,
                'max_storage_gb': 5,
                'max_api_calls_per_month': 5000,
                'included_modules': ['foundation', 'auth_tenants', 'chat', 'hrm', 'inventory', 'finance']
            },
            {
                'name': 'Professional',
                'plan_type': 'professional',
                'price_monthly': 5000,  # 5000 BDT
                'price_yearly': 50000,  # 50000 BDT
                'max_users': 50,
                'max_storage_gb': 20,
                'max_api_calls_per_month': 25000,
                'included_modules': [
                    'foundation', 'auth_tenants', 'chat', 'hrm', 'inventory', 
                    'finance', 'purchase', 'sales', 'production', 'pos', 'rental', 'school'
                ]
            },
            {
                'name': 'Enterprise',
                'plan_type': 'enterprise',
                'price_monthly': 10000,  # 10000 BDT
                'price_yearly': 100000,  # 100000 BDT
                'max_users': 200,
                'max_storage_gb': 100,
                'max_api_calls_per_month': 100000,
                'included_modules': [
                    'foundation', 'auth_tenants', 'chat', 'hrm', 'inventory', 
                    'finance', 'purchase', 'sales', 'production', 'pos', 'rental', 
                    'school', 'jiraclone', 'vault', 'support', 'screenhot', 'recruitment'
                ]
            }
        ]
        
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f"Created plan: {plan.name}")
```

### **Phase 2: Service Layer (1 day)**

#### 2.1 Create Subscription Service
```python
# auth_tenants/services/__init__.py
# auth_tenants/services/subscription_service.py (copy from design doc)
```

#### 2.2 Update Tenant Model Methods
```python
# Add methods to existing Tenant class in auth_tenants/models.py
```

### **Phase 3: API Integration (2 days)**

#### 3.1 Create Subscription APIs
```python
# auth_tenants/api/subscription_views.py
# auth_tenants/api/subscription_serializers.py
```

#### 3.2 Update URL Configuration
```python
# auth_tenants/api/urls.py - Add these endpoints:
path("subscription/plans/", SubscriptionPlansView.as_view()),
path("subscription/current/", TenantSubscriptionView.as_view()),
path("subscription/upgrade/", TenantSubscriptionView.as_view()),
path("subscription/payment/", PaymentProcessView.as_view()),
path("subscription/usage/", SubscriptionUsageView.as_view()),
```

### **Phase 4: Middleware & Access Control (1 day)**

#### 4.1 Create Subscription Middleware
```python
# auth_tenants/middleware.py
```

#### 4.2 Update Settings
```python
# config/settings.py
MIDDLEWARE = [
    # ... existing middleware ...
    'auth_tenants.middleware.SubscriptionMiddleware',
]
```

### **Phase 5: Frontend Dashboard (2-3 days)**

#### 5.1 Subscription Dashboard Template
```html
<!-- auth_tenants/templates/auth_tenants/subscription_dashboard.html -->
<div class="subscription-dashboard">
    <div class="current-plan-card">
        <h3>{{ subscription.plan.name }}</h3>
        <p>Status: {{ subscription.status }}</p>
        <p>Expires: {{ subscription.expires_at|date:"M d, Y" }}</p>
        <p>Days Remaining: {{ subscription.days_remaining }}</p>
    </div>
    
    <div class="usage-metrics">
        <div class="metric-card">
            <h4>Users</h4>
            <div class="progress-bar">
                <div class="progress" style="width: {{ usage.users.percentage }}%"></div>
            </div>
            <p>{{ usage.users.current }} / {{ usage.users.limit }}</p>
        </div>
        
        <div class="metric-card">
            <h4>Storage</h4>
            <div class="progress-bar">
                <div class="progress" style="width: {{ usage.storage.percentage }}%"></div>
            </div>
            <p>{{ usage.storage.current_mb }} MB / {{ usage.storage.limit_mb }} MB</p>
        </div>
    </div>
    
    <div class="upgrade-options">
        <h4>Available Plans</h4>
        {% for plan in available_plans %}
        <div class="plan-card">
            <h5>{{ plan.name }}</h5>
            <p>{{ plan.price_monthly }} BDT/month</p>
            <button onclick="upgradePlan({{ plan.id }})">Upgrade</button>
        </div>
        {% endfor %}
    </div>
</div>
```

#### 5.2 JavaScript for Plan Management
```javascript
// static/js/subscription.js
function upgradePlan(planId) {
    fetch('/api/auth/subscription/upgrade/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            plan_id: planId,
            billing_cycle: 'monthly'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.payment_required) {
            // Redirect to payment page
            window.location.href = `/payment/?amount=${data.amount_due}`;
        }
    });
}
```

### **Phase 6: Payment Integration (3-4 days)**

#### 6.1 bKash Integration
```python
# auth_tenants/services/payment_service.py
import requests

class bKashPaymentService:
    def __init__(self):
        self.base_url = "https://tokenized.sandbox.bka.sh/v1.2.0-beta"  # Sandbox
        self.app_key = settings.BKASH_APP_KEY
        self.app_secret = settings.BKASH_APP_SECRET
        
    def create_payment(self, amount, invoice_no):
        # bKash payment creation logic
        pass
        
    def execute_payment(self, payment_id):
        # Execute payment logic
        pass
```

#### 6.2 Payment Views
```python
# auth_tenants/views/payment_views.py
class PaymentView(TemplateView):
    template_name = 'auth_tenants/payment.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['amount'] = self.request.GET.get('amount')
        return context

class PaymentCallbackView(View):
    def post(self, request):
        # Handle payment gateway callback
        pass
```

### **Phase 7: Automated Tasks (1-2 days)**

#### 7.1 Celery Tasks for Billing
```python
# auth_tenants/tasks.py
from celery import shared_task

@shared_task
def check_expiring_subscriptions():
    """Daily task to check expiring subscriptions"""
    from .services.subscription_service import SubscriptionService
    SubscriptionService.check_expiring_subscriptions()

@shared_task  
def update_usage_metrics():
    """Hourly task to update usage metrics"""
    from .models import Tenant
    for tenant in Tenant.objects.filter(is_active=True):
        SubscriptionService.update_usage_metrics(tenant)

@shared_task
def process_auto_renewals():
    """Daily task for auto-renewals"""
    # Auto-renewal logic
    pass
```

#### 7.2 Celery Beat Schedule
```python
# config/settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-expiring-subscriptions': {
        'task': 'auth_tenants.tasks.check_expiring_subscriptions',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'update-usage-metrics': {
        'task': 'auth_tenants.tasks.update_usage_metrics', 
        'schedule': crontab(minute=0),  # Every hour
    },
    'process-auto-renewals': {
        'task': 'auth_tenants.tasks.process_auto_renewals',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

---

## 🎯 **Quick Start Commands**

### Setup Commands:
```bash
# 1. Create models
python manage.py makemigrations auth_tenants
python manage.py migrate

# 2. Setup subscription plans
python manage.py setup_subscription_plans

# 3. Create superuser if needed
python manage.py createsuperuser

# 4. Start development server
python manage.py runserver

# 5. Start Celery (for background tasks)
celery -A config worker -l info
celery -A config beat -l info
```

### Testing Commands:
```bash
# Test subscription creation
python manage.py shell
>>> from auth_tenants.models import Tenant
>>> tenant = Tenant.objects.first()
>>> subscription = tenant.get_subscription()
>>> print(subscription.plan.name)

# Test module access
>>> tenant.can_access_module('hrm')
>>> tenant.can_access_module('enterprise_only_module')
```

---

## 📊 **Expected Results**

### **After Implementation:**

1. **Tenant Registration** → Auto-creates 14-day free trial
2. **Module Access** → Controlled by subscription plan
3. **Usage Monitoring** → Real-time tracking dashboard
4. **Payment Processing** → bKash/Nagad integration
5. **Auto-billing** → Automated renewal system
6. **Notifications** → Expiry warnings and upgrade prompts

### **Revenue Model:**
- **Free Trial**: 14 days, 3 users, basic modules
- **Basic Plan**: 2000 BDT/month, 10 users, core modules  
- **Professional**: 5000 BDT/month, 50 users, advanced modules
- **Enterprise**: 10000 BDT/month, 200 users, all modules

### **Business Benefits:**
- Predictable recurring revenue
- Scalable pricing model
- Usage-based upselling opportunities
- Professional SaaS experience
- Automated billing reduces manual work

---

## 🚨 **Important Notes**

1. **Database Backup**: Take backup before running migrations
2. **Environment Variables**: Add payment gateway credentials to .env
3. **SSL Certificate**: Required for payment processing
4. **Testing**: Use sandbox/test modes for payment gateways
5. **Monitoring**: Setup logging for payment transactions

এই plan follow করলে আপনার subscription system professional-grade হবে এবং revenue generation শুরু করতে পারবেন! 🚀

**Estimated Timeline: 10-12 days for complete implementation**