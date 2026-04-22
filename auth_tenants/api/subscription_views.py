from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from auth_tenants.permissions import TenantAPIView, IsTenantAdmin, get_tenant

from ..models import SubscriptionPlan, TenantSubscription, PaymentHistory
from ..services.subscription_service import SubscriptionService

class SubscriptionPlansView(TenantAPIView):
    """🎯 Available subscription plans"""
    
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True)
        return self.success_response([{
            'id': plan.id,
            'name': plan.name,
            'plan_type': plan.plan_type,
            'price_monthly': plan.price_monthly,
            'price_yearly': plan.price_yearly,
            'max_users': plan.max_users,
            'max_storage_gb': plan.max_storage_gb,
            'max_api_calls_per_month': plan.max_api_calls_per_month,
            'included_modules': plan.included_modules,
        } for plan in plans])


class TenantSubscriptionView(TenantAPIView):
    """🎯 Current subscription management"""
    permission_classes = [IsTenantAdmin]
    
    def get(self, request):
        """Get current subscription details"""
        tenant = self.get_tenant()
        subscription = tenant.get_subscription()
        
        if not subscription:
            return self.error_response('No subscription found', status.HTTP_404_NOT_FOUND)
        
        return self.success_response({
            'subscription': {
                'id': subscription.id,
                'plan_name': subscription.plan.name,
                'plan_type': subscription.plan.plan_type,
                'status': subscription.status,
                'billing_cycle': subscription.billing_cycle,
                'started_at': subscription.started_at,
                'expires_at': subscription.expires_at,
                'trial_ends_at': subscription.trial_ends_at,
                'days_remaining': subscription.days_remaining(),
                'is_active': subscription.is_active(),
                'is_trial': subscription.is_trial(),
                'auto_renewal': subscription.auto_renewal,
            },
            'plan_details': {
                'price_monthly': subscription.plan.price_monthly,
                'price_yearly': subscription.plan.price_yearly,
                'max_users': subscription.plan.max_users,
                'max_storage_gb': subscription.plan.max_storage_gb,
                'max_api_calls_per_month': subscription.plan.max_api_calls_per_month,
            },
            'usage': tenant.get_usage_summary(),
            'included_modules': subscription.plan.included_modules,
        })
    
    def post(self, request):
        """Upgrade subscription"""
        tenant = self.get_tenant()
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        
        if not plan_id:
            return self.error_response('plan_id is required')
        
        result = SubscriptionService.upgrade_subscription(tenant, plan_id, billing_cycle)
        
        if result['success']:
            return self.success_response({
                'message': 'Subscription upgrade initiated',
                'amount_due': result['amount_due'],
                'payment_required': result['amount_due'] > 0,
                'subscription_id': result['subscription'].id
            })
        else:
            return self.error_response(result['error'])


class SubscriptionUsageView(TenantAPIView):
    """🎯 Usage monitoring"""
    permission_classes = [IsTenantAdmin]
    
    def get(self, request):
        """Get detailed usage information"""
        tenant = self.get_tenant()
        subscription = tenant.get_subscription()
        
        if not subscription:
            return self.error_response('No subscription found', status.HTTP_404_NOT_FOUND)
        
        # Get recent usage logs
        recent_logs = subscription.usage_logs.all()[:30]
        
        return self.success_response({
            'current_usage': tenant.get_usage_summary(),
            'limits_exceeded': {
                'users': tenant.is_usage_limit_exceeded('users'),
                'storage': tenant.is_usage_limit_exceeded('storage'),
                'api_calls': tenant.is_usage_limit_exceeded('api_calls'),
            },
            'usage_history': [{
                'date': log.recorded_at.date(),
                'users_count': log.users_count,
                'storage_mb': log.storage_mb,
                'api_calls': log.api_calls,
            } for log in recent_logs]
        })


class PaymentProcessView(TenantAPIView):
    """🎯 Payment processing"""
    permission_classes = [IsTenantAdmin]
    
    def post(self, request):
        """Process subscription payment"""
        tenant = self.get_tenant()
        subscription = tenant.get_subscription()
        
        if not subscription:
            return self.error_response('No subscription found', status.HTTP_404_NOT_FOUND)
        
        payment_data = {
            'amount': request.data.get('amount'),
            'payment_method': request.data.get('payment_method'),
            'transaction_id': request.data.get('transaction_id'),
        }
        
        # Validate required fields
        if not all(payment_data.values()):
            return self.error_response('amount, payment_method, and transaction_id are required')
        
        try:
            payment = SubscriptionService.process_payment(subscription, **payment_data)
            
            return self.success_response({
                'message': 'Payment processed successfully',
                'payment_id': payment.id,
                'status': payment.status,
                'subscription_status': subscription.status
            })
        except Exception as e:
            return self.error_response(str(e))


class PaymentHistoryView(TenantAPIView):
    """🎯 Payment history"""
    permission_classes = [IsTenantAdmin]
    
    def get(self, request):
        """Get payment history"""
        tenant = self.get_tenant()
        subscription = tenant.get_subscription()
        
        if not subscription:
            return self.error_response('No subscription found', status.HTTP_404_NOT_FOUND)
        
        payments = subscription.payments.all().order_by('-created_at')[:20]
        
        return self.success_response([{
            'id': payment.id,
            'amount': payment.amount,
            'currency': payment.currency,
            'payment_method': payment.payment_method,
            'transaction_id': payment.transaction_id,
            'status': payment.status,
            'paid_at': payment.paid_at,
            'created_at': payment.created_at,
        } for payment in payments])