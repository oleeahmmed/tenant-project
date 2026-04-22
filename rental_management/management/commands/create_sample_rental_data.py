"""
Create sample rental data for testing
Usage: python manage.py create_sample_rental_data --tenant-slug=your-tenant
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from auth_tenants.models import Tenant, User
from rental_management.models import Property, RentalTenant, RentalAgreement, Payment


class Command(BaseCommand):
    help = "Create sample rental data for testing"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-slug",
            type=str,
            required=True,
            help="Tenant slug to create data for",
        )
    
    def handle(self, *args, **options):
        tenant_slug = options["tenant_slug"]
        
        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Tenant '{tenant_slug}' not found"))
            return
        
        # Get a user for created_by
        user = User.objects.filter(tenant=tenant).first()
        if not user:
            user = User.objects.filter(role="super_admin").first()
        
        if not user:
            self.stdout.write(self.style.ERROR("No user found to assign as creator"))
            return
        
        self.stdout.write(f"Creating sample data for tenant: {tenant.name}")
        
        # Create Properties
        self.stdout.write("Creating properties...")
        properties = []
        
        # Flats
        for i in range(1, 11):
            prop = Property.objects.create(
                tenant=tenant,
                property_type="FLAT",
                property_number=f"F-{i:03d}",
                floor_number=f"{(i-1)//4 + 1}",
                size_sqft=Decimal("1200.00"),
                bedrooms=3,
                bathrooms=2,
                monthly_rent=Decimal("15000.00") + (i * 500),
                status="VACANT",
                description=f"৩ বেডরুম ফ্ল্যাট, {(i-1)//4 + 1} তলা",
                created_by=user
            )
            properties.append(prop)
            self.stdout.write(self.style.SUCCESS(f"  Created: {prop}"))
        
        # Garages
        for i in range(1, 6):
            prop = Property.objects.create(
                tenant=tenant,
                property_type="GARAGE",
                property_number=f"G-{i:02d}",
                floor_number="Ground",
                size_sqft=Decimal("200.00"),
                monthly_rent=Decimal("3000.00"),
                status="VACANT",
                description=f"গ্যারেজ নম্বর {i}",
                created_by=user
            )
            properties.append(prop)
            self.stdout.write(self.style.SUCCESS(f"  Created: {prop}"))
        
        # Shops
        for i in range(1, 4):
            prop = Property.objects.create(
                tenant=tenant,
                property_type="SHOP",
                property_number=f"S-{i:02d}",
                floor_number="Ground",
                size_sqft=Decimal("400.00"),
                monthly_rent=Decimal("20000.00") + (i * 2000),
                status="VACANT",
                description=f"দোকান নম্বর {i}",
                created_by=user
            )
            properties.append(prop)
            self.stdout.write(self.style.SUCCESS(f"  Created: {prop}"))
        
        # Create Rental Tenants
        self.stdout.write("\nCreating rental tenants...")
        tenants_data = [
            {"name": "আব্দুল করিম", "mobile": "01712345678", "occupation": "ব্যবসা"},
            {"name": "রহিমা বেগম", "mobile": "01812345679", "occupation": "চাকরি"},
            {"name": "মোহাম্মদ আলী", "mobile": "01912345680", "occupation": "ডাক্তার"},
            {"name": "ফাতেমা খাতুন", "mobile": "01612345681", "occupation": "শিক্ষক"},
            {"name": "জাহিদ হাসান", "mobile": "01512345682", "occupation": "ইঞ্জিনিয়ার"},
        ]
        
        rental_tenants = []
        for data in tenants_data:
            rt = RentalTenant.objects.create(
                tenant=tenant,
                name=data["name"],
                mobile_number=data["mobile"],
                email=f"{data['mobile']}@example.com",
                nid_number=f"123456789{len(rental_tenants)}",
                permanent_address="ঢাকা, বাংলাদেশ",
                emergency_contact_name="জরুরি যোগাযোগ",
                emergency_contact_number="01700000000",
                occupation=data["occupation"],
                family_members_count=4,
                is_active=True,
                created_by=user
            )
            rental_tenants.append(rt)
            self.stdout.write(self.style.SUCCESS(f"  Created: {rt}"))
        
        # Create Agreements
        self.stdout.write("\nCreating rental agreements...")
        today = date.today()
        
        for i, (prop, rt) in enumerate(zip(properties[:5], rental_tenants)):
            agreement = RentalAgreement.objects.create(
                tenant=tenant,
                property=prop,
                rental_tenant=rt,
                start_date=today - relativedelta(months=i),
                end_date=today + relativedelta(years=1) - relativedelta(months=i),
                monthly_rent=prop.monthly_rent,
                advance_amount=prop.monthly_rent * 3,
                advance_months=3,
                service_charge=Decimal("500.00"),
                rent_due_date=5,
                status="ACTIVE",
                notes=f"চুক্তি নম্বর {i+1}",
                created_by=user
            )
            
            # Update property
            prop.status = "OCCUPIED"
            prop.current_tenant = rt
            prop.save()
            
            self.stdout.write(self.style.SUCCESS(f"  Created: {agreement}"))
            
            # Create some payments
            if i < 3:
                payment = Payment.objects.create(
                    tenant=tenant,
                    agreement=agreement,
                    payment_type="ADVANCE",
                    amount=agreement.advance_amount,
                    payment_date=agreement.start_date,
                    payment_method="CASH",
                    notes="অ্যাডভান্স পেমেন্ট",
                    created_by=user
                )
                self.stdout.write(self.style.SUCCESS(f"    Payment: {payment.receipt_number}"))
        
        self.stdout.write(self.style.SUCCESS("\n✓ Sample data created successfully!"))
        self.stdout.write(f"  Properties: {len(properties)}")
        self.stdout.write(f"  Tenants: {len(rental_tenants)}")
        self.stdout.write(f"  Active Agreements: 5")
