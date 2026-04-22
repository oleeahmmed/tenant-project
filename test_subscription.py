#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from auth_tenants.models import Tenant, SubscriptionPlan

print('=== Subscription System Test ===')
print()

print('Available Plans:')
for plan in SubscriptionPlan.objects.all():
    print(f'- {plan.name}: {plan.price_monthly} BDT/month')
    print(f'  Max Users: {plan.max_users}')
    print(f'  Modules: {", ".join(plan.included_modules)}')
    print()

print('Testing tenant subscription:')
tenant = Tenant.objects.first()
if tenant:
    subscription = tenant.get_subscription()
    print(f'Tenant: {tenant.name}')
    if subscription:
        print(f'Subscription: {subscription.plan.name}')
        print(f'Status: {subscription.status}')
        print(f'Days remaining: {subscription.days_remaining()}')
        print(f'Is trial: {subscription.is_trial()}')
        print()
        
        print('Module Access Test:')
        modules = ['hrm', 'inventory', 'finance', 'jiraclone', 'vault']
        for module in modules:
            can_access = tenant.can_access_module(module)
            print(f'- {module}: {"✅" if can_access else "❌"}')
        
        print()
        print('Usage Summary:')
        usage = tenant.get_usage_summary()
        for key, data in usage.items():
            print(f'- {key.title()}: {data["current"]}/{data["limit"]} ({data["percentage"]:.1f}%)')
    else:
        print('No subscription found')
else:
    print('No tenants found')

print()
print('=== Test Complete ===')