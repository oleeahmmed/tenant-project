#!/usr/bin/env python3
"""
Comprehensive ERP Demo Data Import Script
Usage: python import_erp.py
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import timedelta, date
import random

# Import ERP models
from erp.models import (
    Company, Category, Product, Customer, Supplier, SalesPerson, Warehouse,
    SalesQuotation, SalesQuotationItem,
    SalesOrder, SalesOrderItem, Delivery, DeliveryItem,
    Invoice, InvoiceItem, SalesReturn, SalesReturnItem,
    PurchaseQuotation, PurchaseQuotationItem,
    PurchaseOrder, PurchaseOrderItem, PurchaseReturn, PurchaseReturnItem,
    GoodsReceipt, GoodsReceiptItem, GoodsReceiptPO, GoodsReceiptPOItem,
    PurchaseInvoice, PurchaseInvoiceItem,
    GoodsIssue, GoodsIssueItem, ProductionIssue, ProductionIssueItem,
    BillOfMaterials, BOMComponent,
    ProductionOrder, ProductionOrderComponent,
    ProductionReceipt, ProductionReceiptItem,
    InventoryTransfer, InventoryTransferItem,
    ProductWarehouseStock, StockTransaction, StockAdjustment, StockAdjustmentItem,
    BankAccount, IncomingPayment, IncomingPaymentInvoice,
    OutgoingPayment, OutgoingPaymentInvoice,
    AccountType, ChartOfAccounts, CostCenter, Project,
    JournalEntry, JournalEntryLine, FiscalYear, Budget,
    Currency, ExchangeRate, TaxType, TaxRate, PaymentTerm,
    UnitOfMeasure, UOMConversion, PriceList, PriceListItem,
    DiscountType, DiscountRule, PaymentMethod,
    QuickSale, QuickSaleItem, UserProfile
)


class DataImporter:
    """Main data importer class"""
    
    def __init__(self):
        self.data = {}
        self.today = timezone.now().date()
        
    def log(self, message, symbol='✓'):
        """Print formatted log message"""
        print(f'{symbol} {message}')
    
    def error(self, message):
        """Print error message"""
        print(f'❌ {message}')
    
    @transaction.atomic
    def create_superuser(self):
        """Create or get superuser"""
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.log('Created superuser: admin / admin123')
        else:
            self.log('Superuser already exists', '⚠')
        self.data['user'] = user
        return user
    
    @transaction.atomic
    def create_company(self):
        """Create company info"""
        company, created = Company.objects.get_or_create(
            name='Tech Solutions Ltd',
            defaults={
                'address': '123 Business Street, Gulshan-2',
                'city': 'Dhaka',
                'country': 'Bangladesh',
                'phone': '+880-1711-123456',
                'email': 'info@techsolutions.com',
                'website': 'https://techsolutions.com',
                'tax_number': 'TAX-123456789',
            }
        )
        if created:
            self.log('Created company: Tech Solutions Ltd')
        else:
            self.log('Company already exists', '⚠')
        self.data['company'] = company
        return company
    
    @transaction.atomic
    def create_currencies(self):
        """Create currencies"""
        currencies_data = [
            {'code': 'BDT', 'name': 'Bangladeshi Taka', 'symbol': '৳', 'is_base': True},
            {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'is_base': False},
            {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'is_base': False},
        ]
        
        currencies = []
        for data in currencies_data:
            currency, created = Currency.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            currencies.append(currency)
        
        # Create exchange rates
        ExchangeRate.objects.get_or_create(
            from_currency=currencies[1],  # USD
            to_currency=currencies[0],    # BDT
            effective_date=self.today,
            defaults={'rate': Decimal('110.00')}
        )
        ExchangeRate.objects.get_or_create(
            from_currency=currencies[2],  # EUR
            to_currency=currencies[0],    # BDT
            effective_date=self.today,
            defaults={'rate': Decimal('120.00')}
        )
        
        self.log(f'Created {len(currencies)} currencies with exchange rates')
        self.data['currencies'] = currencies
        return currencies
    
    @transaction.atomic
    def create_fiscal_year(self):
        """Create fiscal year"""
        fiscal_year, created = FiscalYear.objects.get_or_create(
            name='FY 2024-2025',
            defaults={
                'start_date': date(2024, 7, 1),
                'end_date': date(2025, 6, 30),
                'is_closed': False,
            }
        )
        self.log(f'Created fiscal year: {fiscal_year.name}')
        self.data['fiscal_year'] = fiscal_year
        return fiscal_year
    
    @transaction.atomic
    def create_warehouses(self):
        """Create demo warehouses"""
        warehouses_data = [
            {
                'name': 'Main Warehouse',
                'code': 'WH-001',
                'address': 'Plot 123, Tejgaon Industrial Area',
                'city': 'Dhaka',
                'country': 'Bangladesh',
                'phone': '+880-1700-111111',
                'email': 'main@warehouse.com',
                'manager': 'Kamal Hossain',
                'is_active': True,
            },
            {
                'name': 'Branch Warehouse',
                'code': 'WH-002',
                'address': 'Sector 7, Uttara',
                'city': 'Dhaka',
                'country': 'Bangladesh',
                'phone': '+880-1700-222222',
                'email': 'branch@warehouse.com',
                'manager': 'Rina Begum',
                'is_active': True,
            },
            {
                'name': 'Chittagong Warehouse',
                'code': 'WH-003',
                'address': 'EPZ Area, Chittagong',
                'city': 'Chittagong',
                'country': 'Bangladesh',
                'phone': '+880-1700-333333',
                'email': 'ctg@warehouse.com',
                'manager': 'Jamal Ahmed',
                'is_active': True,
            },
        ]
        
        warehouses = []
        for data in warehouses_data:
            warehouse, created = Warehouse.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            warehouses.append(warehouse)
        
        self.log(f'Created {len(warehouses)} warehouses')
        self.data['warehouses'] = warehouses
        return warehouses

    
    @transaction.atomic
    def create_categories(self):
        """Create product categories"""
        categories_data = [
            {'name': 'Computers & Laptops', 'code': 'CAT-001', 'description': 'Desktop computers and laptops'},
            {'name': 'Computer Accessories', 'code': 'CAT-002', 'description': 'Mouse, keyboard, webcam, etc.'},
            {'name': 'Storage Devices', 'code': 'CAT-003', 'description': 'Hard drives, flash drives, SSDs'},
            {'name': 'Printers & Scanners', 'code': 'CAT-004', 'description': 'Printing and scanning equipment'},
            {'name': 'Monitors & Displays', 'code': 'CAT-005', 'description': 'Computer monitors and displays'},
            {'name': 'Networking Equipment', 'code': 'CAT-006', 'description': 'Routers, switches, cables'},
        ]
        
        categories = []
        for data in categories_data:
            category, created = Category.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            categories.append(category)
        
        self.log(f'Created {len(categories)} categories')
        self.data['categories'] = categories
        return categories
    
    @transaction.atomic
    def create_uom(self):
        """Create units of measure"""
        uom_data = [
            {'name': 'Piece', 'code': 'PCS', 'uom_type': 'unit'},
            {'name': 'Box', 'code': 'BOX', 'uom_type': 'unit'},
            {'name': 'Kilogram', 'code': 'KG', 'uom_type': 'weight'},
            {'name': 'Meter', 'code': 'M', 'uom_type': 'length'},
            {'name': 'Liter', 'code': 'L', 'uom_type': 'volume'},
        ]
        
        uoms = []
        for data in uom_data:
            uom, created = UnitOfMeasure.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            uoms.append(uom)
        
        # Create UOM conversion (1 Box = 10 Pieces)
        if len(uoms) >= 2:
            UOMConversion.objects.get_or_create(
                from_uom=uoms[1],  # Box
                to_uom=uoms[0],    # Piece
                defaults={'conversion_factor': Decimal('10.00')}
            )
        
        self.log(f'Created {len(uoms)} units of measure')
        self.data['uoms'] = uoms
        return uoms
    
    @transaction.atomic
    def create_tax_types(self):
        """Create tax types and rates"""
        tax_type, created = TaxType.objects.get_or_create(
            name='VAT',
            defaults={
                'code': 'VAT',
                'description': 'Value Added Tax',
                'is_active': True,
            }
        )
        
        tax_rates = []
        rates_data = [
            {'name': 'Standard VAT', 'rate': Decimal('15.00'), 'is_default': True},
            {'name': 'Reduced VAT', 'rate': Decimal('5.00'), 'is_default': False},
            {'name': 'Zero VAT', 'rate': Decimal('0.00'), 'is_default': False},
        ]
        
        for data in rates_data:
            data['tax_type'] = tax_type
            rate, created = TaxRate.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            tax_rates.append(rate)
        
        self.log(f'Created tax type with {len(tax_rates)} rates')
        self.data['tax_rates'] = tax_rates
        return tax_rates
    
    @transaction.atomic
    def create_payment_terms(self):
        """Create payment terms"""
        terms_data = [
            {'name': 'Immediate', 'code': 'IMM', 'days': 0, 'description': 'Payment due immediately'},
            {'name': 'Net 15', 'code': 'NET15', 'days': 15, 'description': 'Payment due in 15 days'},
            {'name': 'Net 30', 'code': 'NET30', 'days': 30, 'description': 'Payment due in 30 days'},
            {'name': 'Net 45', 'code': 'NET45', 'days': 45, 'description': 'Payment due in 45 days'},
            {'name': 'Net 60', 'code': 'NET60', 'days': 60, 'description': 'Payment due in 60 days'},
        ]
        
        terms = []
        for data in terms_data:
            term, created = PaymentTerm.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            terms.append(term)
        
        self.log(f'Created {len(terms)} payment terms')
        self.data['payment_terms'] = terms
        return terms
    
    @transaction.atomic
    def create_payment_methods(self):
        """Create payment methods"""
        methods_data = [
            {'name': 'Cash', 'code': 'CASH', 'is_active': True},
            {'name': 'Bank Transfer', 'code': 'BANK', 'is_active': True},
            {'name': 'Credit Card', 'code': 'CARD', 'is_active': True},
            {'name': 'Mobile Banking', 'code': 'MOBILE', 'is_active': True},
            {'name': 'Cheque', 'code': 'CHEQUE', 'is_active': True},
        ]
        
        methods = []
        for data in methods_data:
            method, created = PaymentMethod.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            methods.append(method)
        
        self.log(f'Created {len(methods)} payment methods')
        self.data['payment_methods'] = methods
        return methods
    
    @transaction.atomic
    def create_bank_accounts(self):
        """Create bank accounts"""
        accounts_data = [
            {
                'account_name': 'Main Operating Account',
                'account_number': '1234567890',
                'bank_name': 'Dutch Bangla Bank',
                'branch': 'Gulshan Branch',
                'currency': self.data['currencies'][0],  # BDT
                'balance': Decimal('500000.00'),
                'is_active': True,
            },
            {
                'account_name': 'USD Account',
                'account_number': '0987654321',
                'bank_name': 'Standard Chartered',
                'branch': 'Motijheel Branch',
                'currency': self.data['currencies'][1],  # USD
                'balance': Decimal('10000.00'),
                'is_active': True,
            },
        ]
        
        accounts = []
        for data in accounts_data:
            account, created = BankAccount.objects.get_or_create(
                account_number=data['account_number'],
                defaults=data
            )
            accounts.append(account)
        
        self.log(f'Created {len(accounts)} bank accounts')
        self.data['bank_accounts'] = accounts
        return accounts
    
    @transaction.atomic
    def create_customers(self):
        """Create demo customers"""
        customers_data = [
            {
                'name': 'ABC Corporation',
                'code': 'CUST-001',
                'phone': '+880-1711-123456',
                'email': 'contact@abccorp.com',
                'address': '123 Main Street, Gulshan',
                'city': 'Dhaka',
                'country': 'Bangladesh',
                'credit_limit': Decimal('100000.00'),
                'payment_terms': 'Net 30',
                'is_active': True,
            },
            {
                'name': 'XYZ Enterprises',
                'code': 'CUST-002',
                'phone': '+880-1712-234567',
                'email': 'info@xyzent.com',
                'address': '456 Park Avenue, Banani',
                'city': 'Dhaka',
                'country': 'Bangladesh',
                'credit_limit': Decimal('150000.00'),
                'payment_terms': 'Net 30',
                'is_active': True,
            },
            {
                'name': 'Tech Solutions Ltd',
                'code': 'CUST-003',
                'phone': '+880-1713-345678',
                'email': 'sales@techsol.com',
                'address': '789 Tech Park, Bashundhara',
                'city': 'Dhaka',
                'country': 'Bangladesh',
                'credit_limit': Decimal('200000.00'),
                'payment_terms': 'Net 45',
                'is_active': True,
            },
            {
                'name': 'Global Trading Co',
                'code': 'CUST-004',
                'phone': '+880-1714-456789',
                'email': 'orders@globaltrading.com',
                'address': '321 Business District, Motijheel',
                'city': 'Dhaka',
                'country': 'Bangladesh',
                'credit_limit': Decimal('80000.00'),
                'payment_terms': 'Net 15',
                'is_active': True,
            },
            {
                'name': 'Retail Mart',
                'code': 'CUST-005',
                'phone': '+880-1715-567890',
                'email': 'purchase@retailmart.com',
                'address': '654 Shopping Complex, Dhanmondi',
                'city': 'Dhaka',
                'country': 'Bangladesh',
                'credit_limit': Decimal('120000.00'),
                'payment_terms': 'Net 30',
                'is_active': True,
            },
        ]
        
        customers = []
        for data in customers_data:
            customer, created = Customer.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            customers.append(customer)
        
        self.log(f'Created {len(customers)} customers')
        self.data['customers'] = customers
        return customers
    
    @transaction.atomic
    def create_suppliers(self):
        """Create demo suppliers"""
        suppliers_data = [
            {
                'name': 'Tech Wholesale Ltd',
                'code': 'SUPP-001',
                'phone': '+880-1731-111111',
                'email': 'sales@techwholesale.com',
                'address': 'Tejgaon Industrial Area',
                'city': 'Dhaka',
                'country': 'Bangladesh',
                'payment_terms': 'Net 30',
                'is_active': True,
            },
            {
                'name': 'Computer Parts BD',
                'code': 'SUPP-002',
                'phone': '+880-1732-222222',
                'email': 'info@computerparts.com',
                'address': 'Elephant Road',
                'city': 'Dhaka',
                'country': 'Bangladesh',
                'payment_terms': 'Net 45',
                'is_active': True,
            },
            {
                'name': 'Electronics Supplier',
                'code': 'SUPP-003',
                'phone': '+880-1733-333333',
                'email': 'contact@electronicsupplier.com',
                'address': 'Bangla Motor',
                'city': 'Dhaka',
                'country': 'Bangladesh',
                'payment_terms': 'Net 30',
                'is_active': True,
            },
        ]
        
        suppliers = []
        for data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            suppliers.append(supplier)
        
        self.log(f'Created {len(suppliers)} suppliers')
        self.data['suppliers'] = suppliers
        return suppliers

    
    @transaction.atomic
    def create_sales_persons(self):
        """Create demo sales persons"""
        sales_persons_data = [
            {
                'name': 'Karim Ahmed',
                'code': 'SP-001',
                'phone': '+880-1721-111111',
                'email': 'karim@company.com',
                'employee_id': 'EMP001',
                'commission_rate': Decimal('2.50'),
                'is_active': True,
            },
            {
                'name': 'Fatima Rahman',
                'code': 'SP-002',
                'phone': '+880-1722-222222',
                'email': 'fatima@company.com',
                'employee_id': 'EMP002',
                'commission_rate': Decimal('3.00'),
                'is_active': True,
            },
            {
                'name': 'Rahim Hossain',
                'code': 'SP-003',
                'phone': '+880-1723-333333',
                'email': 'rahim@company.com',
                'employee_id': 'EMP003',
                'commission_rate': Decimal('2.00'),
                'is_active': True,
            },
        ]
        
        sales_persons = []
        for data in sales_persons_data:
            sales_person, created = SalesPerson.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            sales_persons.append(sales_person)
        
        self.log(f'Created {len(sales_persons)} sales persons')
        self.data['sales_persons'] = sales_persons
        return sales_persons
    
    @transaction.atomic
    def create_products(self):
        """Create demo products"""
        categories = self.data['categories']
        warehouses = self.data['warehouses']
        
        products_data = [
            {
                'name': 'Laptop Dell Inspiron 15',
                'sku': 'DELL-INS-15',
                'barcode': '1234567890001',
                'category': categories[0],
                'description': 'Intel Core i5, 8GB RAM, 512GB SSD',
                'purchase_price': Decimal('45000.00'),
                'selling_price': Decimal('55000.00'),
                'min_stock_level': Decimal('5.00'),
                'max_stock_level': Decimal('50.00'),
                'unit': 'PCS',
                'is_active': True,
                'track_inventory': True,
            },
            {
                'name': 'HP Laser Printer',
                'sku': 'HP-LASER-01',
                'barcode': '1234567890002',
                'category': categories[3],
                'description': 'Monochrome laser printer with WiFi',
                'purchase_price': Decimal('12000.00'),
                'selling_price': Decimal('15000.00'),
                'min_stock_level': Decimal('3.00'),
                'max_stock_level': Decimal('20.00'),
                'unit': 'PCS',
                'is_active': True,
                'track_inventory': True,
            },
            {
                'name': 'Wireless Mouse Logitech',
                'sku': 'LOG-MOUSE-01',
                'barcode': '1234567890003',
                'category': categories[1],
                'description': 'Ergonomic wireless mouse',
                'purchase_price': Decimal('800.00'),
                'selling_price': Decimal('1200.00'),
                'min_stock_level': Decimal('20.00'),
                'max_stock_level': Decimal('100.00'),
                'unit': 'PCS',
                'is_active': True,
                'track_inventory': True,
            },
            {
                'name': 'Mechanical Keyboard',
                'sku': 'MECH-KB-01',
                'barcode': '1234567890004',
                'category': categories[1],
                'description': 'RGB backlit mechanical keyboard',
                'purchase_price': Decimal('2500.00'),
                'selling_price': Decimal('3500.00'),
                'min_stock_level': Decimal('10.00'),
                'max_stock_level': Decimal('50.00'),
                'unit': 'PCS',
                'is_active': True,
                'track_inventory': True,
            },
            {
                'name': 'USB Flash Drive 64GB',
                'sku': 'USB-64GB',
                'barcode': '1234567890005',
                'category': categories[2],
                'description': 'High-speed USB 3.0 flash drive',
                'purchase_price': Decimal('400.00'),
                'selling_price': Decimal('600.00'),
                'min_stock_level': Decimal('50.00'),
                'max_stock_level': Decimal('200.00'),
                'unit': 'PCS',
                'is_active': True,
                'track_inventory': True,
            },
            {
                'name': 'External Hard Drive 1TB',
                'sku': 'HDD-EXT-1TB',
                'barcode': '1234567890006',
                'category': categories[2],
                'description': 'Portable external HDD',
                'purchase_price': Decimal('3500.00'),
                'selling_price': Decimal('4500.00'),
                'min_stock_level': Decimal('8.00'),
                'max_stock_level': Decimal('40.00'),
                'unit': 'PCS',
                'is_active': True,
                'track_inventory': True,
            },
            {
                'name': 'Webcam HD 1080p',
                'sku': 'WEBCAM-HD',
                'barcode': '1234567890007',
                'category': categories[1],
                'description': 'Full HD webcam with microphone',
                'purchase_price': Decimal('2000.00'),
                'selling_price': Decimal('2800.00'),
                'min_stock_level': Decimal('15.00'),
                'max_stock_level': Decimal('60.00'),
                'unit': 'PCS',
                'is_active': True,
                'track_inventory': True,
            },
            {
                'name': 'Monitor 24 inch LED',
                'sku': 'MON-24-LED',
                'barcode': '1234567890008',
                'category': categories[4],
                'description': 'Full HD LED monitor',
                'purchase_price': Decimal('9000.00'),
                'selling_price': Decimal('12000.00'),
                'min_stock_level': Decimal('5.00'),
                'max_stock_level': Decimal('30.00'),
                'unit': 'PCS',
                'is_active': True,
                'track_inventory': True,
            },
            {
                'name': 'Network Router WiFi 6',
                'sku': 'ROUTER-WIFI6',
                'barcode': '1234567890009',
                'category': categories[5],
                'description': 'Dual-band WiFi 6 router',
                'purchase_price': Decimal('3000.00'),
                'selling_price': Decimal('4200.00'),
                'min_stock_level': Decimal('10.00'),
                'max_stock_level': Decimal('40.00'),
                'unit': 'PCS',
                'is_active': True,
                'track_inventory': True,
            },
            {
                'name': 'HDMI Cable 2m',
                'sku': 'HDMI-CABLE-2M',
                'barcode': '1234567890010',
                'category': categories[5],
                'description': 'High-speed HDMI cable 2 meters',
                'purchase_price': Decimal('200.00'),
                'selling_price': Decimal('350.00'),
                'min_stock_level': Decimal('30.00'),
                'max_stock_level': Decimal('150.00'),
                'unit': 'PCS',
                'is_active': True,
                'track_inventory': True,
            },
        ]
        
        products = []
        for data in products_data:
            data['default_warehouse'] = warehouses[0]
            product, created = Product.objects.get_or_create(
                sku=data['sku'],
                defaults=data
            )
            products.append(product)
            
            # Create initial warehouse stock
            if created:
                initial_stock = Decimal(str(random.randint(20, 100)))
                ProductWarehouseStock.objects.create(
                    product=product,
                    warehouse=warehouses[0],
                    quantity=initial_stock
                )
                
                # Create stock transaction
                StockTransaction.objects.create(
                    product=product,
                    warehouse=warehouses[0],
                    transaction_type='opening_stock',
                    quantity=initial_stock,
                    transaction_date=self.today - timedelta(days=90),
                    reference_number='OPENING-STOCK',
                    notes='Initial opening stock'
                )
        
        self.log(f'Created {len(products)} products with initial stock')
        self.data['products'] = products
        return products
    
    @transaction.atomic
    def create_price_lists(self):
        """Create price lists"""
        products = self.data['products']
        
        price_list, created = PriceList.objects.get_or_create(
            name='Retail Price List',
            defaults={
                'code': 'RETAIL-001',
                'currency': self.data['currencies'][0],
                'is_active': True,
                'valid_from': self.today - timedelta(days=30),
                'valid_to': self.today + timedelta(days=365),
            }
        )
        
        # Add items to price list
        for product in products[:5]:
            PriceListItem.objects.get_or_create(
                price_list=price_list,
                product=product,
                defaults={
                    'price': product.selling_price * Decimal('0.95'),  # 5% discount
                    'discount_percentage': Decimal('5.00'),
                }
            )
        
        self.log('Created price list with items')
        self.data['price_lists'] = [price_list]
        return [price_list]
    
    @transaction.atomic
    def create_discount_types(self):
        """Create discount types"""
        discount_type, created = DiscountType.objects.get_or_create(
            name='Seasonal Discount',
            defaults={
                'code': 'SEASONAL',
                'discount_type': 'percentage',
                'value': Decimal('10.00'),
                'is_active': True,
                'valid_from': self.today,
                'valid_to': self.today + timedelta(days=30),
            }
        )
        
        self.log('Created discount type')
        self.data['discount_types'] = [discount_type]
        return [discount_type]

    
    @transaction.atomic
    def create_sales_quotations(self):
        """Create demo sales quotations"""
        customers = self.data['customers']
        sales_persons = self.data['sales_persons']
        products = self.data['products']
        
        quotations = []
        for i in range(5):
            customer = random.choice(customers)
            sales_person = random.choice(sales_persons) if random.random() > 0.3 else None
            
            sq = SalesQuotation.objects.create(
                quotation_date=self.today - timedelta(days=random.randint(5, 30)),
                valid_until=self.today + timedelta(days=random.randint(15, 45)),
                customer=customer,
                salesperson=sales_person,
                status=random.choice(['draft', 'sent', 'accepted', 'rejected']),
                payment_terms='Net 30',
                discount_amount=Decimal(str(random.randint(0, 500))),
                tax_rate=Decimal('15.00'),
                notes='Demo sales quotation',
            )
            
            # Add 2-4 items
            num_items = random.randint(2, 4)
            selected_products = random.sample(products, min(num_items, len(products)))
            
            for product in selected_products:
                SalesQuotationItem.objects.create(
                    sales_quotation=sq,
                    product=product,
                    quantity=Decimal(str(random.randint(1, 10))),
                    unit_price=product.selling_price,
                    discount_percentage=Decimal(str(random.randint(0, 10))),
                )
            
            sq.calculate_totals()
            quotations.append(sq)
        
        self.log(f'Created {len(quotations)} sales quotations')
        self.data['sales_quotations'] = quotations
        return quotations
    
    @transaction.atomic
    def create_purchase_quotations(self):
        """Create demo purchase quotations"""
        suppliers = self.data['suppliers']
        products = self.data['products']
        
        quotations = []
        for i in range(3):
            supplier = suppliers[i % len(suppliers)]
            
            pq = PurchaseQuotation.objects.create(
                quotation_date=self.today - timedelta(days=random.randint(10, 40)),
                valid_until=self.today + timedelta(days=random.randint(20, 60)),
                supplier=supplier,
                status=random.choice(['draft', 'sent', 'received', 'accepted']),
                discount_amount=Decimal('300.00'),
                tax_amount=Decimal('500.00'),
                notes='Demo purchase quotation',
            )
            
            # Add 2-3 items
            num_items = random.randint(2, 3)
            selected_products = random.sample(products, num_items)
            
            for product in selected_products:
                PurchaseQuotationItem.objects.create(
                    purchase_quotation=pq,
                    product=product,
                    quantity=Decimal(str(random.randint(10, 30))),
                    unit_price=product.purchase_price,
                )
            
            pq.calculate_totals()
            quotations.append(pq)
        
        self.log(f'Created {len(quotations)} purchase quotations')
        self.data['purchase_quotations'] = quotations
        return quotations
    
    @transaction.atomic
    def create_purchase_orders(self):
        """Create demo purchase orders"""
        suppliers = self.data['suppliers']
        products = self.data['products']
        
        purchase_orders = []
        for i in range(5):
            supplier = suppliers[i % len(suppliers)]
            
            po = PurchaseOrder.objects.create(
                order_date=self.today - timedelta(days=random.randint(30, 90)),
                expected_date=self.today - timedelta(days=random.randint(1, 20)),
                supplier=supplier,
                status='completed',
                discount_amount=Decimal('500.00'),
                tax_amount=Decimal('1000.00'),
                payment_terms='Net 30',
                notes='Demo purchase order',
            )
            
            # Add 2-4 items
            num_items = random.randint(2, 4)
            selected_products = random.sample(products, num_items)
            
            for product in selected_products:
                PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    product=product,
                    quantity=Decimal(str(random.randint(10, 50))),
                    unit_price=product.purchase_price,
                )
            
            po.calculate_totals()
            purchase_orders.append(po)
        
        self.log(f'Created {len(purchase_orders)} purchase orders')
        self.data['purchase_orders'] = purchase_orders
        return purchase_orders
    
    @transaction.atomic
    def create_sales_orders(self):
        """Create demo sales orders"""
        customers = self.data['customers']
        sales_persons = self.data['sales_persons']
        products = self.data['products']
        
        sales_orders = []
        for i in range(10):
            customer = random.choice(customers)
            sales_person = random.choice(sales_persons) if random.random() > 0.3 else None
            
            so = SalesOrder.objects.create(
                order_date=self.today - timedelta(days=random.randint(1, 60)),
                customer=customer,
                salesperson=sales_person,
                status=random.choice(['draft', 'confirmed', 'processing', 'completed']),
                delivery_date=self.today + timedelta(days=random.randint(1, 14)),
                payment_terms='Net 30',
                discount_amount=Decimal(str(random.randint(0, 1000))),
                tax_rate=Decimal('15.00'),
                notes='Demo sales order',
            )
            
            # Add 1-5 items
            num_items = random.randint(1, 5)
            selected_products = random.sample(products, min(num_items, len(products)))
            
            for product in selected_products:
                SalesOrderItem.objects.create(
                    sales_order=so,
                    product=product,
                    quantity=Decimal(str(random.randint(1, 10))),
                    unit_price=product.selling_price,
                    discount_percentage=Decimal(str(random.randint(0, 5))),
                )
            
            so.calculate_totals()
            sales_orders.append(so)
        
        self.log(f'Created {len(sales_orders)} sales orders')
        self.data['sales_orders'] = sales_orders
        return sales_orders
    
    @transaction.atomic
    def create_goods_receipts_po(self):
        """Create goods receipts from purchase orders"""
        purchase_orders = self.data['purchase_orders']
        warehouses = self.data['warehouses']
        
        receipts = []
        for po in purchase_orders[:3]:
            receipt = GoodsReceiptPO.objects.create(
                receipt_date=po.order_date + timedelta(days=random.randint(3, 10)),
                purchase_order=po,
                supplier=po.supplier,
                warehouse=warehouses[0],
                status=random.choice(['received', 'inspected', 'completed']),
                received_by='Warehouse Staff',
                notes='Demo goods receipt',
            )
            
            # Receive partial or full quantities
            for po_item in po.items.all():
                receive_qty = po_item.quantity * Decimal(str(random.uniform(0.7, 1.0)))
                GoodsReceiptPOItem.objects.create(
                    goods_receipt=receipt,
                    purchase_order_item=po_item,
                    product=po_item.product,
                    quantity=receive_qty,
                    unit_price=po_item.unit_price,
                )
            
            receipts.append(receipt)
        
        self.log(f'Created {len(receipts)} goods receipts (PO)')
        self.data['goods_receipts_po'] = receipts
        return receipts
    
    @transaction.atomic
    def create_purchase_invoices(self):
        """Create purchase invoices"""
        purchase_orders = self.data['purchase_orders']
        
        invoices = []
        for po in purchase_orders[:3]:
            invoice = PurchaseInvoice.objects.create(
                invoice_date=po.order_date + timedelta(days=random.randint(5, 15)),
                due_date=po.order_date + timedelta(days=35),
                purchase_order=po,
                supplier=po.supplier,
                status=random.choice(['draft', 'received', 'paid', 'partially_paid']),
                discount_amount=po.discount_amount,
                tax_amount=po.tax_amount,
                paid_amount=Decimal('0.00'),
                notes='Demo purchase invoice',
            )
            
            # Invoice items
            for po_item in po.items.all():
                PurchaseInvoiceItem.objects.create(
                    purchase_invoice=invoice,
                    purchase_order_item=po_item,
                    product=po_item.product,
                    quantity=po_item.quantity,
                    unit_price=po_item.unit_price,
                )
            
            invoice.calculate_totals()
            # Set paid amount
            invoice.paid_amount = invoice.total_amount * Decimal(str(random.uniform(0, 1)))
            invoice.save()
            
            invoices.append(invoice)
        
        self.log(f'Created {len(invoices)} purchase invoices')
        self.data['purchase_invoices'] = invoices
        return invoices
    
    @transaction.atomic
    def create_deliveries(self):
        """Create deliveries from sales orders"""
        sales_orders = self.data['sales_orders']
        
        deliveries = []
        for so in sales_orders[:5]:
            delivery = Delivery.objects.create(
                delivery_date=so.order_date + timedelta(days=random.randint(1, 7)),
                sales_order=so,
                customer=so.customer,
                salesperson=so.salesperson,
                status=random.choice(['pending', 'in_transit', 'delivered']),
                delivery_address=so.customer.address,
                notes='Demo delivery',
            )
            
            # Deliver partial or full quantities
            for so_item in so.items.all():
                deliver_qty = so_item.quantity * Decimal(str(random.uniform(0.5, 1.0)))
                DeliveryItem.objects.create(
                    delivery=delivery,
                    product=so_item.product,
                    quantity=deliver_qty,
                    unit_price=so_item.unit_price,
                )
            
            deliveries.append(delivery)
        
        self.log(f'Created {len(deliveries)} deliveries')
        self.data['deliveries'] = deliveries
        return deliveries
    
    @transaction.atomic
    def create_invoices(self):
        """Create invoices from sales orders"""
        sales_orders = self.data['sales_orders']
        
        invoices = []
        for so in sales_orders[:6]:
            invoice = Invoice.objects.create(
                invoice_date=so.order_date + timedelta(days=random.randint(1, 5)),
                due_date=so.order_date + timedelta(days=30),
                sales_order=so,
                customer=so.customer,
                salesperson=so.salesperson,
                status=random.choice(['draft', 'sent', 'paid', 'partially_paid']),
                discount_amount=so.discount_amount,
                tax_amount=so.tax_amount,
                paid_amount=Decimal('0.00'),
                notes='Demo invoice',
            )
            
            # Invoice items
            for so_item in so.items.all():
                invoice_qty = so_item.quantity * Decimal(str(random.uniform(0.5, 1.0)))
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=so_item.product,
                    quantity=invoice_qty,
                    unit_price=so_item.unit_price,
                )
            
            invoice.calculate_totals()
            # Set paid amount
            invoice.paid_amount = invoice.total_amount * Decimal(str(random.uniform(0, 1)))
            invoice.save()
            
            invoices.append(invoice)
        
        self.log(f'Created {len(invoices)} invoices')
        self.data['invoices'] = invoices
        return invoices

    
    @transaction.atomic
    def create_payments(self):
        """Create incoming and outgoing payments"""
        invoices = self.data.get('invoices', [])
        purchase_invoices = self.data.get('purchase_invoices', [])
        bank_accounts = self.data['bank_accounts']
        payment_methods = self.data['payment_methods']
        
        # Create incoming payments (from customers)
        incoming_payments = []
        for invoice in invoices[:3]:
            if invoice.paid_amount > 0:
                payment = IncomingPayment.objects.create(
                    payment_date=invoice.invoice_date + timedelta(days=random.randint(5, 20)),
                    customer=invoice.customer,
                    payment_method=random.choice(payment_methods),
                    bank_account=bank_accounts[0],
                    amount=invoice.paid_amount,
                    reference_number=f'PAY-IN-{random.randint(1000, 9999)}',
                    notes='Demo incoming payment',
                )
                
                IncomingPaymentInvoice.objects.create(
                    incoming_payment=payment,
                    invoice=invoice,
                    amount=invoice.paid_amount,
                )
                
                incoming_payments.append(payment)
        
        # Create outgoing payments (to suppliers)
        outgoing_payments = []
        for p_invoice in purchase_invoices[:2]:
            if p_invoice.paid_amount > 0:
                payment = OutgoingPayment.objects.create(
                    payment_date=p_invoice.invoice_date + timedelta(days=random.randint(10, 30)),
                    supplier=p_invoice.supplier,
                    payment_method=random.choice(payment_methods),
                    bank_account=bank_accounts[0],
                    amount=p_invoice.paid_amount,
                    reference_number=f'PAY-OUT-{random.randint(1000, 9999)}',
                    notes='Demo outgoing payment',
                )
                
                OutgoingPaymentInvoice.objects.create(
                    outgoing_payment=payment,
                    purchase_invoice=p_invoice,
                    amount=p_invoice.paid_amount,
                )
                
                outgoing_payments.append(payment)
        
        self.log(f'Created {len(incoming_payments)} incoming and {len(outgoing_payments)} outgoing payments')
        self.data['incoming_payments'] = incoming_payments
        self.data['outgoing_payments'] = outgoing_payments
        return incoming_payments, outgoing_payments
    
    @transaction.atomic
    def create_sales_returns(self):
        """Create sales returns"""
        sales_orders = self.data['sales_orders']
        
        returns = []
        for so in sales_orders[:2]:
            sales_return = SalesReturn.objects.create(
                return_date=so.order_date + timedelta(days=random.randint(10, 20)),
                sales_order=so,
                customer=so.customer,
                salesperson=so.salesperson,
                status='pending',
                reason='Defective product',
                notes='Demo sales return',
            )
            
            # Return small quantities
            for so_item in so.items.all()[:2]:
                return_qty = Decimal(str(random.randint(1, 3)))
                SalesReturnItem.objects.create(
                    sales_return=sales_return,
                    product=so_item.product,
                    quantity=return_qty,
                    unit_price=so_item.unit_price,
                )
            
            sales_return.calculate_totals()
            returns.append(sales_return)
        
        self.log(f'Created {len(returns)} sales returns')
        self.data['sales_returns'] = returns
        return returns
    
    @transaction.atomic
    def create_purchase_returns(self):
        """Create purchase returns"""
        purchase_orders = self.data['purchase_orders']
        
        returns = []
        for po in purchase_orders[:1]:
            purchase_return = PurchaseReturn.objects.create(
                return_date=po.order_date + timedelta(days=random.randint(5, 15)),
                purchase_order=po,
                supplier=po.supplier,
                status='pending',
                reason='Wrong items received',
                notes='Demo purchase return',
            )
            
            # Return small quantities
            for po_item in po.items.all()[:2]:
                return_qty = Decimal(str(random.randint(1, 5)))
                PurchaseReturnItem.objects.create(
                    purchase_return=purchase_return,
                    product=po_item.product,
                    quantity=return_qty,
                    unit_price=po_item.unit_price,
                )
            
            purchase_return.calculate_totals()
            returns.append(purchase_return)
        
        self.log(f'Created {len(returns)} purchase returns')
        self.data['purchase_returns'] = returns
        return returns
    
    @transaction.atomic
    def create_goods_issues(self):
        """Create goods issues"""
        sales_orders = self.data['sales_orders']
        warehouses = self.data['warehouses']
        
        issues = []
        for so in sales_orders[:3]:
            issue = GoodsIssue.objects.create(
                issue_date=so.order_date + timedelta(days=random.randint(1, 5)),
                issue_type='sales',
                sales_order=so,
                customer=so.customer,
                status=random.choice(['issued', 'completed']),
                issued_by='Warehouse Staff',
                warehouse_location=warehouses[0].name,
                notes='Demo goods issue',
            )
            
            # Issue partial or full quantities
            for so_item in so.items.all():
                issue_qty = so_item.quantity * Decimal(str(random.uniform(0.6, 1.0)))
                GoodsIssueItem.objects.create(
                    goods_issue=issue,
                    product=so_item.product,
                    quantity=issue_qty,
                    unit_price=so_item.unit_price,
                )
            
            issues.append(issue)
        
        self.log(f'Created {len(issues)} goods issues')
        self.data['goods_issues'] = issues
        return issues
    
    @transaction.atomic
    def create_inventory_transfers(self):
        """Create inventory transfers"""
        products = self.data['products']
        warehouses = self.data['warehouses']
        
        transfers = []
        for i in range(2):
            transfer = InventoryTransfer.objects.create(
                transfer_date=self.today - timedelta(days=random.randint(5, 20)),
                from_warehouse=warehouses[0],
                to_warehouse=warehouses[1],
                status=random.choice(['pending', 'in_transit', 'completed']),
                transferred_by='Transfer Staff',
                received_by='Branch Staff' if i == 0 else '',
                notes='Demo inventory transfer',
            )
            
            # Transfer 2-3 products
            num_items = random.randint(2, 3)
            selected_products = random.sample(products, num_items)
            
            for product in selected_products:
                transfer_qty = Decimal(str(random.randint(5, 15)))
                InventoryTransferItem.objects.create(
                    inventory_transfer=transfer,
                    product=product,
                    quantity=transfer_qty,
                    unit_price=product.purchase_price,
                )
            
            transfers.append(transfer)
        
        self.log(f'Created {len(transfers)} inventory transfers')
        self.data['inventory_transfers'] = transfers
        return transfers
    
    @transaction.atomic
    def create_stock_adjustments(self):
        """Create stock adjustments"""
        products = self.data['products']
        warehouses = self.data['warehouses']
        
        adjustments = []
        for i in range(2):
            adjustment = StockAdjustment.objects.create(
                adjustment_date=self.today - timedelta(days=random.randint(10, 30)),
                warehouse=warehouses[0],
                adjustment_type=random.choice(['increase', 'decrease']),
                reason=random.choice(['damaged', 'expired', 'found', 'lost']),
                status='completed',
                approved_by='Manager',
                notes='Demo stock adjustment',
            )
            
            # Adjust 2 products
            for product in products[:2]:
                adj_qty = Decimal(str(random.randint(1, 5)))
                StockAdjustmentItem.objects.create(
                    stock_adjustment=adjustment,
                    product=product,
                    quantity=adj_qty,
                    unit_price=product.purchase_price,
                    reason='Physical count variance',
                )
            
            adjustment.calculate_totals()
            adjustments.append(adjustment)
        
        self.log(f'Created {len(adjustments)} stock adjustments')
        self.data['stock_adjustments'] = adjustments
        return adjustments
    
    @transaction.atomic
    def create_bills_of_materials(self):
        """Create bills of materials"""
        products = self.data['products']
        
        boms = []
        
        # BOM 1: Custom Laptop Assembly
        bom1 = BillOfMaterials.objects.create(
            name='Custom Laptop Assembly',
            bom_number='BOM-001',
            product=products[0],  # Laptop
            version='1.0',
            quantity=Decimal('1.00'),
            status='active',
            labor_cost=Decimal('5000.00'),
            overhead_cost=Decimal('2000.00'),
            notes='Complete laptop assembly',
        )
        
        # Components
        BOMComponent.objects.create(
            bom=bom1,
            product=products[2],  # Mouse
            quantity=Decimal('1.00'),
            scrap_percentage=Decimal('2.00'),
        )
        BOMComponent.objects.create(
            bom=bom1,
            product=products[3],  # Keyboard
            quantity=Decimal('1.00'),
            scrap_percentage=Decimal('2.00'),
        )
        BOMComponent.objects.create(
            bom=bom1,
            product=products[6],  # Webcam
            quantity=Decimal('1.00'),
            scrap_percentage=Decimal('1.00'),
        )
        
        bom1.calculate_costs()
        boms.append(bom1)
        
        # BOM 2: Workstation Package
        bom2 = BillOfMaterials.objects.create(
            name='Computer Workstation Package',
            bom_number='BOM-002',
            product=products[7],  # Monitor
            version='1.0',
            quantity=Decimal('1.00'),
            status='active',
            labor_cost=Decimal('1500.00'),
            overhead_cost=Decimal('500.00'),
            notes='Complete workstation setup',
        )
        
        BOMComponent.objects.create(
            bom=bom2,
            product=products[2],  # Mouse
            quantity=Decimal('1.00'),
            scrap_percentage=Decimal('1.00'),
        )
        
        bom2.calculate_costs()
        boms.append(bom2)
        
        # finished building BOM list
        self.log(f'Created {len(boms)} bills of materials')
        self.data['boms'] = boms
        return boms
    
    @transaction.atomic
    def create_production_orders(self):
        """Create production orders"""
        boms = self.data['boms']
        warehouses = self.data['warehouses']
        sales_orders = self.data['sales_orders']
        
        orders = []
        for i, bom in enumerate(boms):
            po = ProductionOrder.objects.create(
                order_date=self.today - timedelta(days=random.randint(10, 30)),
                planned_start_date=self.today - timedelta(days=random.randint(5, 15)),
                planned_end_date=self.today + timedelta(days=random.randint(1, 10)),
                bom=bom,
                warehouse=warehouses[0],
                quantity_to_produce=Decimal(str(random.randint(5, 15))),
                status=random.choice(['planned', 'in_progress', 'completed']),
                sales_order=sales_orders[i] if i < len(sales_orders) else None,
            )
            
            for bom_comp in bom.components.all():
                ProductionOrderComponent.objects.create(
                    production_order=po,
                    product=bom_comp.product,
                    quantity_required=bom_comp.quantity * po.quantity_to_produce,
                    quantity_consumed=Decimal('0.00'),
                )
            
            orders.append(po)
        
        self.log(f'Created {len(orders)} production orders')
        self.data['production_orders'] = orders
        return orders
    
    @transaction.atomic
    def create_production_receipts(self):
        """Create production receipts"""
        production_orders = self.data.get('production_orders', [])
        
        receipts = []
        for po in production_orders:
            if po.status in ['in_progress', 'completed']:
                qty_received = po.quantity_to_produce * Decimal(str(random.uniform(0.8, 1.0)))
                
                receipt = ProductionReceipt.objects.create(
                    receipt_date=po.planned_start_date + timedelta(days=random.randint(3, 7)),
                    production_order=po,
                    quantity_received=qty_received,
                    quantity_rejected=Decimal('0.00'),
                    status='completed',
                    received_by='Production Staff',
                )
                
                for po_comp in po.components.all():
                    ProductionReceiptItem.objects.create(
                        production_receipt=receipt,
                        product=po_comp.product,
                        quantity_consumed=po_comp.quantity_required,
                    )
                
                receipts.append(receipt)
        
        self.log(f'Created {len(receipts)} production receipts')
        self.data['production_receipts'] = receipts
        return receipts
    
    @transaction.atomic
    def create_quick_sales(self):
        """Create quick sales (POS)"""
        products = self.data['products']
        payment_methods = self.data['payment_methods']
        user = self.data['user']
        
        # Create profile
        pos_profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'branch': self.data['warehouses'][0]}
        )
        
        quick_sales = []
        for i in range(5):
            qs = QuickSale.objects.create(
                sale_date=self.today - timedelta(days=random.randint(0, 10)),
                customer_name=f'Walk-in Customer {i+1}',
                customer_phone=f'+880-17{random.randint(10000000, 99999999)}',
                payment_method=random.choice(payment_methods),
                status='completed',
                user=user,
                discount_amount=Decimal(str(random.randint(0, 100))),
                tax_rate=Decimal('15.00'),
            )
            
            # Add 1-3 items
            for product in random.sample(products, random.randint(1, 3)):
                QuickSaleItem.objects.create(
                    quick_sale=qs,
                    product=product,
                    quantity=Decimal(str(random.randint(1, 3))),
                    unit_price=product.selling_price,
                )
            
            qs.calculate_totals()
            quick_sales.append(qs)
        
        self.log(f'Created {len(quick_sales)} quick sales')
        self.data['quick_sales'] = quick_sales
        return quick_sales
    
    def run_import(self):
        """Run all import functions"""
        print('🚀 Starting comprehensive ERP demo data import...\n')
        print('='*70)
        
        try:
            # Core setup
            self.create_superuser()
            self.create_company()
            self.create_currencies()
            self.create_fiscal_year()
            
            # Master data
            self.create_warehouses()
            self.create_categories()
            self.create_uom()
            self.create_tax_types()
            self.create_payment_terms()
            self.create_payment_methods()
            self.create_bank_accounts()
            
            # Business partners
            self.create_customers()
            self.create_suppliers()
            self.create_sales_persons()
            
            # Products and pricing
            self.create_products()
            self.create_price_lists()
            self.create_discount_types()
            
            # Sales cycle
            self.create_sales_quotations()
            self.create_sales_orders()
            self.create_deliveries()
            self.create_invoices()
            self.create_sales_returns()
            
            # Purchase cycle
            self.create_purchase_quotations()
            self.create_purchase_orders()
            self.create_goods_receipts_po()
            self.create_purchase_invoices()
            self.create_purchase_returns()
            
            # Inventory operations
            self.create_goods_issues()
            self.create_inventory_transfers()
            self.create_stock_adjustments()
            
            # Production
            self.create_bills_of_materials()
            self.create_production_orders()
            self.create_production_receipts()
            
            # Payments
            self.create_payments()
            
            # POS
            self.create_quick_sales()
            
            print('\n' + '='*70)
            print('🎉 Demo data import completed successfully!')
            print('='*70)
            self.print_summary()
            self.print_login_info()
            
        except Exception as e:
            self.error(f'Error during import: {str(e)}')
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def print_summary(self):
        """Print import summary"""
        print('\n📊 Demo Data Summary:')
        print('-'*70)
        
        summary_items = [
            ('Warehouses', 'warehouses'),
            ('Categories', 'categories'),
            ('Products', 'products'),
            ('Customers', 'customers'),
            ('Suppliers', 'suppliers'),
            ('Sales Persons', 'sales_persons'),
            ('Bank Accounts', 'bank_accounts'),
            ('Sales Quotations', 'sales_quotations'),
            ('Purchase Quotations', 'purchase_quotations'),
            ('Purchase Orders', 'purchase_orders'),
            ('Sales Orders', 'sales_orders'),
            ('Deliveries', 'deliveries'),
            ('Invoices', 'invoices'),
            ('Purchase Invoices', 'purchase_invoices'),
            ('Sales Returns', 'sales_returns'),
            ('Purchase Returns', 'purchase_returns'),
            ('Goods Receipts', 'goods_receipts_po'),
            ('Goods Issues', 'goods_issues'),
            ('Inventory Transfers', 'inventory_transfers'),
            ('Stock Adjustments', 'stock_adjustments'),
            ('Bills of Materials', 'boms'),
            ('Production Orders', 'production_orders'),
            ('Production Receipts', 'production_receipts'),
            ('Quick Sales (POS)', 'quick_sales'),
        ]
        
        for label, key in summary_items:
            count = len(self.data.get(key, []))
            if count > 0:
                print(f'  • {label:.<50} {count:>3}')
        
        print('-'*70)
    
    def print_login_info(self):
        """Print login information"""
        print('\n🔐 LOGIN CREDENTIALS:')
        print('='*70)
        print('  Username: admin')
        print('  Password: admin123')
        print('='*70)
        print('\n📝 Next Steps:')
        print('  1. Run: python manage.py runserver')
        print('  2. Open: http://127.0.0.1:8000/admin/')
        print('  3. Login with credentials above')
        print('='*70)


def main():
    """Main entry point"""
    importer = DataImporter()
    importer.run_import()


if __name__ == '__main__':
    main()
