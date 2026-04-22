from django.utils import timezone
from django.db import transaction
from ..models import TenantSubscription, SubscriptionPlan, PaymentHistory, SubscriptionUsageLog

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
            # Send notification logic here
            print(f"Subscription expiring soon: {sub.tenant.name}")
        
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
        SubscriptionUsageLog.objects.create(
            subscription=subscription,
            users_count=subscription.current_users,
            storage_mb=subscription.current_storage_mb,
            api_calls=subscription.api_calls_this_month
        )
    
    @staticmethod
    def create_default_plans():
        """Create default subscription plans"""
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
        
        created_plans = []
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                created_plans.append(plan)
        
        return created_plans