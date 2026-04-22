# Professional Subscription System Design

## 🎯 Current Analysis

আপনার existing system এ ইতিমধ্যে একটি solid foundation আছে:

### ✅ **Existing Strong Points:**
- `TenantModuleSubscription` model আছে
- `is_module_enabled()` method আছে  
- Permission-based access control আছে
- Multi-tenant architecture ready

### 🔧 **Enhancement Areas:**
- Subscription plans & pricing
- Payment integration
- Usage limits & quotas
- Billing cycles
- Feature restrictions
- Auto-renewal logic

---

## 🏗️ **Professional Subscription Architecture**

### **1. Subscription Plans Structure**

```python
# Enhanced Models (auth_tenants/models.py এ add করুন)

class SubscriptionPlan(models.Model):
    """Master subscription plans (Super Admin manages)"""
    
    PLAN_TYPES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('professional', 'Professional'), 
        ('enterprise', 'Enterprise'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Feature limits
    max_users = models.IntegerField(default=5)
    max_storage_gb = models.IntegerField(default=1)
    max_api_calls_per_month = models.IntegerField(default=1000)
    
    # Module access
    included_modules = models.JSONField(default=list)  # ['hrm', 'inventory', 'finance']
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ${self.price_monthly}/month"


class TenantSubscription(models.Model):
    """Active subscription for each tenant"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
        ('trial', 'Trial'),
    ]
    
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]
    
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='monthly')
    
    # Dates
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    current_users = models.IntegerField(default=0)
    current_storage_mb = models.IntegerField(default=0)
    api_calls_this_month = models.IntegerField(default=0)
    
    # Payment
    auto_renewal = models.BooleanField(default=True)
    payment_method_id = models.CharField(max_length=100, blank=True)  # Stripe/bKash ID
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_active(self):
        return self.status == 'active' and timezone.now() < self.expires_at
    
    def is_trial(self):
        return self.status == 'trial' and self.trial_ends_at and timezone.now() < self.trial_ends_at
    
    def days_remaining(self):
        if self.expires_at:
            delta = self.expires_at - timezone.now()
            return max(0, delta.days)
        return 0
    
    def can_access_module(self, module_code):
        if not self.is_active() and not self.is_trial():
            return False
        return module_code in self.plan.included_modules
    
    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name} ({self.status})"


class SubscriptionUsageLog(models.Model):
    """Track usage for billing and limits"""
    
    subscription = models.ForeignKey(TenantSubscription, on_delete=models.CASCADE, related_name='usage_logs')
    
    # Usage metrics
    users_count = models.IntegerField(default=0)
    storage_mb = models.IntegerField(default=0)
    api_calls = models.IntegerField(default=0)
    
    # Module-specific usage
    module_usage = models.JSONField(default=dict)  # {'hrm': {'employees': 50}, 'inventory': {'products': 200}}
    
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']


class PaymentHistory(models.Model):
    """Payment transaction history"""
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('rocket', 'Rocket'),
        ('stripe', 'Stripe'),
        ('bank', 'Bank Transfer'),
    ]
    
    subscription = models.ForeignKey(TenantSubscription, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='BDT')
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, unique=True)
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Payment gateway response
    gateway_response = models.JSONField(default=dict)
    
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.subscription.tenant.name} - {self.amount} {self.currency} ({self.status})"
```

### **2. Enhanced Tenant Model Methods**

```python
# auth_tenants/models.py এ Tenant class এ add করুন

class Tenant(models.Model):
    # ... existing fields ...
    
    def get_subscription(self):
        """Get active subscription or create trial"""
        try:
            return self.subscription
        except TenantSubscription.DoesNotExist:
            # Auto-create trial subscription
            free_plan = SubscriptionPlan.objects.filter(plan_type='free').first()
            if free_plan:
                return TenantSubscription.objects.create(
                    tenant=self,
                    plan=free_plan,
                    status='trial',
                    expires_at=timezone.now() + timezone.timedelta(days=14),
                    trial_ends_at=timezone.now() + timezone.timedelta(days=14)
                )
            return None
    
    def can_access_module(self, module_code: str) -> bool:
        """Enhanced module access check with subscription"""
        # Core modules always available
        if module_code in ('auth_tenants', 'foundation'):
            return True
            
        subscription = self.get_subscription()
        if not subscription:
            return False
            
        return subscription.can_access_module(module_code)
    
    def get_usage_summary(self):
        """Get current usage vs limits"""
        subscription = self.get_subscription()
        if not subscription:
            return {}
            
        return {
            'users': {
                'current': subscription.current_users,
                'limit': subscription.plan.max_users,
                'percentage': (subscription.current_users / subscription.plan.max_users) * 100
            },
            'storage': {
                'current_mb': subscription.current_storage_mb,
                'limit_mb': subscription.plan.max_storage_gb * 1024,
                'percentage': (subscription.current_storage_mb / (subscription.plan.max_storage_gb * 1024)) * 100
            },
            'api_calls': {
                'current': subscription.api_calls_this_month,
                'limit': subscription.plan.max_api_calls_per_month,
                'percentage': (subscription.api_calls_this_month / subscription.plan.max_api_calls_per_month) * 100
            }
        }
    
    def is_usage_limit_exceeded(self, check_type='users'):
        """Check if usage limit exceeded"""
        usage = self.get_usage_summary()
        if check_type in usage:
            return usage[check_type]['percentage'] >= 100
        return False
```

### **3. Subscription Management Services**

```python
# auth_tenants/services/subscription_service.py

from django.utils import timezone
from django.db import transaction
from ..models import TenantSubscription, SubscriptionPlan, PaymentHistory

class SubscriptionService:
    
    @staticmethod
    def upgrade_subscription(tenant, plan_id, billing_cycle='monthly'):
        """Upgrade tenant subscription"""
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return {'success': False, 'error': 'Invalid plan'}
        
        with transaction.atomic():
            subscription = tenant.get_subscription()
            
            # Calculate new expiry
            if billing_cycle == 'monthly':
                expires_at = timezone.now() + timezone.timedelta(days=30)
                amount = plan.price_monthly
            else:  # yearly
                expires_at = timezone.now() + timezone.timedelta(days=365)
                amount = plan.price_yearly
            
            # Update subscription
            subscription.plan = plan
            subscription.billing_cycle = billing_cycle
            subscription.expires_at = expires_at
            subscription.status = 'active'
            subscription.save()
            
            return {
                'success': True,
                'subscription': subscription,
                'amount_due': amount
            }
    
    @staticmethod
    def process_payment(subscription, amount, payment_method, transaction_id):
        """Process subscription payment"""
        payment = PaymentHistory.objects.create(
            subscription=subscription,
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            status='completed',
            paid_at=timezone.now()
        )
        
        # Update subscription status
        subscription.status = 'active'
        subscription.save()
        
        return payment
    
    @staticmethod
    def check_expiring_subscriptions():
        """Check and notify expiring subscriptions"""
        expiring_soon = TenantSubscription.objects.filter(
            status='active',
            expires_at__lte=timezone.now() + timezone.timedelta(days=7),
            expires_at__gt=timezone.now()
        )
        
        for sub in expiring_soon:
            # Send notification
            pass  # Implement notification logic
        
        return expiring_soon
    
    @staticmethod
    def update_usage_metrics(tenant):
        """Update current usage metrics"""
        subscription = tenant.get_subscription()
        if not subscription:
            return
        
        # Count active users
        subscription.current_users = tenant.members.filter(is_active=True).count()
        
        # Calculate storage (implement based on your file storage)
        # subscription.current_storage_mb = calculate_tenant_storage(tenant)
        
        subscription.save()
        
        # Log usage
        from ..models import SubscriptionUsageLog
        SubscriptionUsageLog.objects.create(
            subscription=subscription,
            users_count=subscription.current_users,
            storage_mb=subscription.current_storage_mb,
            api_calls=subscription.api_calls_this_month
        )
```

### **4. API Endpoints for Subscription**

```python
# auth_tenants/api/subscription_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import SubscriptionPlan, TenantSubscription
from ..services.subscription_service import SubscriptionService
from .permissions import IsTenantAdmin

class SubscriptionPlansView(APIView):
    """Available subscription plans"""
    
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True)
        return Response([{
            'id': plan.id,
            'name': plan.name,
            'plan_type': plan.plan_type,
            'price_monthly': plan.price_monthly,
            'price_yearly': plan.price_yearly,
            'max_users': plan.max_users,
            'max_storage_gb': plan.max_storage_gb,
            'included_modules': plan.included_modules,
        } for plan in plans])


class TenantSubscriptionView(APIView):
    permission_classes = [IsTenantAdmin]
    
    def get(self, request):
        """Get current subscription details"""
        tenant = request.user.tenant
        subscription = tenant.get_subscription()
        
        if not subscription:
            return Response({'error': 'No subscription found'}, status=404)
        
        return Response({
            'subscription': {
                'plan_name': subscription.plan.name,
                'status': subscription.status,
                'expires_at': subscription.expires_at,
                'days_remaining': subscription.days_remaining(),
                'billing_cycle': subscription.billing_cycle,
            },
            'usage': tenant.get_usage_summary(),
            'included_modules': subscription.plan.included_modules,
        })
    
    def post(self, request):
        """Upgrade subscription"""
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        
        result = SubscriptionService.upgrade_subscription(
            request.user.tenant, plan_id, billing_cycle
        )
        
        if result['success']:
            return Response({
                'message': 'Subscription upgraded successfully',
                'amount_due': result['amount_due'],
                'payment_required': True
            })
        else:
            return Response({'error': result['error']}, status=400)


class PaymentProcessView(APIView):
    permission_classes = [IsTenantAdmin]
    
    def post(self, request):
        """Process subscription payment"""
        subscription = request.user.tenant.get_subscription()
        
        payment_data = {
            'amount': request.data.get('amount'),
            'payment_method': request.data.get('payment_method'),
            'transaction_id': request.data.get('transaction_id'),
        }
        
        payment = SubscriptionService.process_payment(
            subscription, **payment_data
        )
        
        return Response({
            'message': 'Payment processed successfully',
            'payment_id': payment.id,
            'status': payment.status
        })
```

### **5. Middleware for Module Access Control**

```python
# auth_tenants/middleware.py

from django.http import JsonResponse
from django.urls import resolve

class SubscriptionMiddleware:
    """Check module access based on subscription"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for superusers and auth endpoints
        if (request.user.is_anonymous or 
            request.user.role == 'super_admin' or
            request.path.startswith('/api/auth/')):
            return self.get_response(request)
        
        # Get module from URL
        try:
            url_name = resolve(request.path_info).url_name
            app_name = resolve(request.path_info).app_name
        except:
            return self.get_response(request)
        
        # Check module access
        if app_name and request.user.tenant:
            if not request.user.tenant.can_access_module(app_name):
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        'error': 'Module not available in your subscription plan',
                        'upgrade_required': True
                    }, status=403)
                else:
                    # Redirect to upgrade page
                    pass
        
        return self.get_response(request)
```

---

## 🚀 **Implementation Steps**

### **Phase 1: Database Setup**
1. Add new models to `auth_tenants/models.py`
2. Create migrations: `python manage.py makemigrations auth_tenants`
3. Run migrations: `python manage.py migrate`

### **Phase 2: Service Layer**
1. Create `auth_tenants/services/subscription_service.py`
2. Update existing `Tenant.is_module_enabled()` method

### **Phase 3: API Integration**
1. Add subscription API views
2. Update existing API permissions
3. Add middleware for access control

### **Phase 4: Frontend Integration**
1. Subscription management dashboard
2. Usage monitoring widgets
3. Payment integration forms

### **Phase 5: Payment Gateway**
1. bKash/Nagad integration
2. Stripe for international
3. Webhook handlers

---

## 💡 **Professional Features**

### **Usage Monitoring Dashboard**
```python
# Real-time usage tracking
def get_tenant_dashboard_data(tenant):
    return {
        'subscription_status': tenant.subscription.status,
        'days_remaining': tenant.subscription.days_remaining(),
        'usage_metrics': tenant.get_usage_summary(),
        'recent_payments': tenant.subscription.payments.filter(
            status='completed'
        ).order_by('-paid_at')[:5],
        'available_upgrades': SubscriptionPlan.objects.filter(
            price_monthly__gt=tenant.subscription.plan.price_monthly
        )
    }
```

### **Automated Billing**
```python
# Celery task for auto-renewal
@shared_task
def process_subscription_renewals():
    expiring = TenantSubscription.objects.filter(
        status='active',
        expires_at__lte=timezone.now() + timezone.timedelta(hours=24),
        auto_renewal=True
    )
    
    for subscription in expiring:
        # Process payment and renew
        pass
```

### **Usage Limits Enforcement**
```python
# Decorator for API rate limiting
def check_api_limit(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.tenant.is_usage_limit_exceeded('api_calls'):
            return JsonResponse({'error': 'API limit exceeded'}, status=429)
        
        # Increment API call counter
        subscription = request.user.tenant.get_subscription()
        subscription.api_calls_this_month += 1
        subscription.save()
        
        return view_func(request, *args, **kwargs)
    return wrapper
```

---

## 🎯 **Benefits of This Design**

1. **Scalable**: Supports multiple plans and custom pricing
2. **Flexible**: Module-based access control
3. **Professional**: Usage tracking and billing automation
4. **User-friendly**: Clear upgrade paths and notifications
5. **Revenue-focused**: Multiple payment methods and auto-renewal
6. **Analytics-ready**: Comprehensive usage logging

এই system implement করলে আপনার SaaS platform industry-standard হবে এবং revenue generation এর জন্য perfect হবে! 🚀