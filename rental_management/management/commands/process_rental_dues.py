"""
Management command to process rental dues and send reminders
Usage: python manage.py process_rental_dues
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from rental_management.models import RentalAgreement, DuePayment
from rental_management.services import SMSService, NotificationService
from auth_tenants.models import User


class Command(BaseCommand):
    help = "Process rental dues and send reminders"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--send-sms",
            action="store_true",
            help="Send SMS reminders to tenants with overdue payments",
        )
        parser.add_argument(
            "--create-dues",
            action="store_true",
            help="Create due payment records for current month",
        )
    
    def handle(self, *args, **options):
        today = date.today()
        
        if options["create_dues"]:
            self.stdout.write("Creating due payments for current month...")
            self.create_monthly_dues(today)
        
        if options["send_sms"]:
            self.stdout.write("Sending SMS reminders...")
            self.send_overdue_reminders(today)
        
        if not options["create_dues"] and not options["send_sms"]:
            self.stdout.write(self.style.WARNING("No action specified. Use --create-dues or --send-sms"))
    
    def create_monthly_dues(self, today):
        """Create due payment records for active agreements"""
        active_agreements = RentalAgreement.objects.filter(
            status="ACTIVE",
            start_date__lte=today,
            end_date__gte=today
        ).select_related("property", "rental_tenant")
        
        created_count = 0
        for agreement in active_agreements:
            # Calculate due date for current month
            due_date = today.replace(day=agreement.rent_due_date)
            if due_date < today:
                # If due date has passed, set for next month
                due_date = (today + relativedelta(months=1)).replace(day=agreement.rent_due_date)
            
            # Check if due payment already exists
            due_month = today.replace(day=1)
            existing = DuePayment.objects.filter(
                agreement=agreement,
                due_month=due_month
            ).exists()
            
            if not existing:
                DuePayment.objects.create(
                    tenant=agreement.tenant,
                    agreement=agreement,
                    due_month=due_month,
                    due_amount=agreement.monthly_rent + agreement.service_charge,
                    due_date=due_date,
                    is_paid=False
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created due for {agreement.rental_tenant.name} - {agreement.property}"
                    )
                )
        
        self.stdout.write(self.style.SUCCESS(f"Total dues created: {created_count}"))
    
    def send_overdue_reminders(self, today):
        """Send SMS reminders for overdue payments"""
        overdue_payments = DuePayment.objects.filter(
            is_paid=False,
            due_date__lt=today
        ).select_related("agreement", "agreement__rental_tenant", "agreement__property")
        
        sent_count = 0
        failed_count = 0
        
        for due in overdue_payments:
            # Send SMS reminder
            result = SMSService.send_due_reminder(due)
            
            if result["success"]:
                sent_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"SMS sent to {due.agreement.rental_tenant.name} ({due.agreement.rental_tenant.mobile_number})"
                    )
                )
                
                # Send in-app notification to tenant admins
                admin_users = User.objects.filter(
                    tenant=due.tenant,
                    role__in=["tenant_admin", "super_admin"]
                ).values_list("id", flat=True)
                
                if admin_users:
                    NotificationService.notify_due_payment(due, list(admin_users))
            else:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to send SMS to {due.agreement.rental_tenant.name}: {result['message']}"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"SMS sent: {sent_count}, Failed: {failed_count}")
        )
