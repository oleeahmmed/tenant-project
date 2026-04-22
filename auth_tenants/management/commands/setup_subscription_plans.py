from django.core.management.base import BaseCommand
from auth_tenants.services.subscription_service import SubscriptionService

class Command(BaseCommand):
    help = 'Setup default subscription plans'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating default subscription plans...')
        
        created_plans = SubscriptionService.create_default_plans()
        
        if created_plans:
            for plan in created_plans:
                self.stdout.write(
                    self.style.SUCCESS(f'Created plan: {plan.name} - {plan.price_monthly} BDT/month')
                )
        else:
            self.stdout.write(
                self.style.WARNING('All plans already exist')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Subscription plans setup completed!')
        )