from django.core.management.base import BaseCommand
from django.utils import timezone
from auth_tenants.models import Tenant, SubscriptionPlan, TenantSubscription

class Command(BaseCommand):
    help = 'Create subscriptions for existing tenants'
    
    def handle(self, *args, **options):
        self.stdout.write('Migrating existing tenants to subscription system...')
        
        # Get or create free plan
        free_plan, created = SubscriptionPlan.objects.get_or_create(
            plan_type='free',
            defaults={
                'name': 'Free Trial',
                'price_monthly': 0,
                'price_yearly': 0,
                'max_users': 3,
                'max_storage_gb': 1,
                'max_api_calls_per_month': 500,
                'included_modules': ['foundation', 'auth_tenants', 'chat']
            }
        )
        
        if created:
            self.stdout.write(f'Created free plan: {free_plan.name}')
        
        # Create subscriptions for tenants without one
        tenants_without_subscription = Tenant.objects.filter(subscription__isnull=True)
        
        created_count = 0
        for tenant in tenants_without_subscription:
            subscription = TenantSubscription.objects.create(
                tenant=tenant,
                plan=free_plan,
                status='trial',
                expires_at=timezone.now() + timezone.timedelta(days=30),  # 30 day trial for existing
                trial_ends_at=timezone.now() + timezone.timedelta(days=30)
            )
            created_count += 1
            self.stdout.write(f'Created subscription for: {tenant.name}')
        
        if created_count == 0:
            self.stdout.write('All tenants already have subscriptions')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} subscriptions')
            )