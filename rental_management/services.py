"""Rental Management Services - SMS, Notifications, Reports"""

import requests
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from typing import List, Optional

from rental_management.models import SMSLog, DuePayment, RentalAgreement
from notification.services import notify_users


class SMSService:
    """SMS Gateway Service"""
    
    @staticmethod
    def send_sms(mobile_number: str, message: str, tenant_id: int, 
                 rental_tenant_id: Optional[int] = None, 
                 message_type: str = "CUSTOM") -> dict:
        """
        SMS পাঠানো
        
        Returns:
            dict: {"success": bool, "message": str, "log_id": int}
        """
        # Create SMS log
        sms_log = SMSLog.objects.create(
            tenant_id=tenant_id,
            rental_tenant_id=rental_tenant_id,
            mobile_number=mobile_number,
            message_text=message,
            message_type=message_type,
            status="PENDING"
        )
        
        # SMS Gateway configuration (from settings)
        sms_gateway_url = getattr(settings, "SMS_GATEWAY_URL", None)
        sms_api_key = getattr(settings, "SMS_API_KEY", None)
        sms_sender_id = getattr(settings, "SMS_SENDER_ID", None)
        
        if not all([sms_gateway_url, sms_api_key, sms_sender_id]):
            sms_log.status = "FAILED"
            sms_log.error_message = "SMS Gateway not configured"
            sms_log.save()
            return {
                "success": False,
                "message": "SMS Gateway not configured",
                "log_id": sms_log.id
            }
        
        try:
            # Example API call (adjust based on your SMS provider)
            payload = {
                "api_key": sms_api_key,
                "sender_id": sms_sender_id,
                "mobile": mobile_number,
                "message": message,
            }
            
            response = requests.post(sms_gateway_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                sms_log.status = "SENT"
                sms_log.sent_at = timezone.now()
                sms_log.save()
                return {
                    "success": True,
                    "message": "SMS sent successfully",
                    "log_id": sms_log.id
                }
            else:
                sms_log.status = "FAILED"
                sms_log.error_message = f"HTTP {response.status_code}: {response.text}"
                sms_log.save()
                return {
                    "success": False,
                    "message": f"SMS failed: {response.text}",
                    "log_id": sms_log.id
                }
        
        except Exception as e:
            sms_log.status = "FAILED"
            sms_log.error_message = str(e)
            sms_log.save()
            return {
                "success": False,
                "message": f"SMS error: {str(e)}",
                "log_id": sms_log.id
            }


    @staticmethod
    def send_due_reminder(due_payment: DuePayment) -> dict:
        """বকেয়া রিমাইন্ডার SMS পাঠানো"""
        tenant_name = due_payment.agreement.rental_tenant.name
        property_name = str(due_payment.agreement.property)
        due_amount = due_payment.due_amount
        due_date = due_payment.due_date.strftime("%d/%m/%Y")
        
        message = (
            f"প্রিয় {tenant_name},\n"
            f"{property_name} এর {due_payment.due_month.strftime('%B %Y')} মাসের ভাড়া "
            f"{due_amount} টাকা বকেয়া আছে। "
            f"পরিশোধের তারিখ: {due_date}। "
            f"অনুগ্রহ করে যথাশীঘ্র পরিশোধ করুন।"
        )
        
        result = SMSService.send_sms(
            mobile_number=due_payment.agreement.rental_tenant.mobile_number,
            message=message,
            tenant_id=due_payment.tenant_id,
            rental_tenant_id=due_payment.agreement.rental_tenant_id,
            message_type="DUE_NOTICE"
        )
        
        if result["success"]:
            due_payment.reminder_sent = True
            due_payment.reminder_count += 1
            due_payment.save()
        
        return result
    
    @staticmethod
    def send_payment_reminder(agreement: RentalAgreement, days_before: int = 3) -> dict:
        """পেমেন্ট রিমাইন্ডার SMS (পেমেন্ট তারিখের আগে)"""
        tenant_name = agreement.rental_tenant.name
        property_name = str(agreement.property)
        monthly_rent = agreement.monthly_rent
        
        message = (
            f"প্রিয় {tenant_name},\n"
            f"{property_name} এর আগামী {days_before} দিনের মধ্যে "
            f"{monthly_rent} টাকা ভাড়া পরিশোধ করার কথা মনে করিয়ে দিচ্ছি। "
            f"ধন্যবাদ।"
        )
        
        return SMSService.send_sms(
            mobile_number=agreement.rental_tenant.mobile_number,
            message=message,
            tenant_id=agreement.tenant_id,
            rental_tenant_id=agreement.rental_tenant_id,
            message_type="REMINDER"
        )
    
    @staticmethod
    def send_contract_expiry_notice(agreement: RentalAgreement) -> dict:
        """চুক্তি শেষ হওয়ার নোটিশ"""
        tenant_name = agreement.rental_tenant.name
        property_name = str(agreement.property)
        end_date = agreement.end_date.strftime("%d/%m/%Y")
        
        message = (
            f"প্রিয় {tenant_name},\n"
            f"{property_name} এর ভাড়া চুক্তি {end_date} তারিখে শেষ হবে। "
            f"চুক্তি নবায়ন করতে চাইলে অনুগ্রহ করে যোগাযোগ করুন।"
        )
        
        return SMSService.send_sms(
            mobile_number=agreement.rental_tenant.mobile_number,
            message=message,
            tenant_id=agreement.tenant_id,
            rental_tenant_id=agreement.rental_tenant_id,
            message_type="CONTRACT_EXPIRY"
        )


class NotificationService:
    """In-app notification service using existing notification system"""
    
    @staticmethod
    def notify_due_payment(due_payment: DuePayment, user_ids: List[int]):
        """বকেয়া পেমেন্ট নোটিফিকেশন"""
        tenant_name = due_payment.agreement.rental_tenant.name
        property_name = str(due_payment.agreement.property)
        
        notify_users(
            tenant_id=due_payment.tenant_id,
            recipient_ids=user_ids,
            title=f"বকেয়া ভাড়া - {tenant_name}",
            body=f"{property_name} এর {due_payment.due_month.strftime('%B %Y')} মাসের ভাড়া বকেয়া আছে।",
            kind="rental.due_payment",
            link_url=f"/dashboard/rental/dues/?agreement={due_payment.agreement_id}",
            metadata={
                "due_payment_id": due_payment.id,
                "agreement_id": due_payment.agreement_id,
                "amount": str(due_payment.due_amount),
            }
        )
    
    @staticmethod
    def notify_payment_received(payment, user_ids: List[int]):
        """পেমেন্ট প্রাপ্তি নোটিফিকেশন"""
        tenant_name = payment.agreement.rental_tenant.name
        
        notify_users(
            tenant_id=payment.tenant_id,
            recipient_ids=user_ids,
            title=f"পেমেন্ট প্রাপ্ত - {tenant_name}",
            body=f"{payment.amount} টাকা পেমেন্ট প্রাপ্ত হয়েছে। রিসিপ্ট: {payment.receipt_number}",
            kind="rental.payment_received",
            link_url=f"/dashboard/rental/payments/{payment.id}/",
            metadata={
                "payment_id": payment.id,
                "amount": str(payment.amount),
                "receipt_number": payment.receipt_number,
            }
        )
    
    @staticmethod
    def notify_contract_expiring(agreement: RentalAgreement, user_ids: List[int]):
        """চুক্তি শেষ হওয়ার নোটিফিকেশন"""
        tenant_name = agreement.rental_tenant.name
        property_name = str(agreement.property)
        
        notify_users(
            tenant_id=agreement.tenant_id,
            recipient_ids=user_ids,
            title=f"চুক্তি শেষ হচ্ছে - {tenant_name}",
            body=f"{property_name} এর চুক্তি {agreement.end_date.strftime('%d/%m/%Y')} তারিখে শেষ হবে।",
            kind="rental.contract_expiring",
            link_url=f"/dashboard/rental/agreements/{agreement.id}/",
            metadata={
                "agreement_id": agreement.id,
                "end_date": agreement.end_date.isoformat(),
            }
        )
