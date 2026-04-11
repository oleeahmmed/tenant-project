from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from auth_tenants.models import Tenant
from finance.models import APInvoice, APPayment, APPaymentAllocation, ARInvoice, ARReceipt, ARReceiptAllocation, Account, FiscalPeriod, FiscalYear
from finance.services.posting import post_ap_invoice, post_ap_payment, post_ar_receipt
from foundation.models import Customer, Supplier


class FinancePostingTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Demo Tenant", slug="demo-tenant")
        self.today = timezone.localdate()
        self.fy = FiscalYear.objects.create(
            tenant=self.tenant,
            name="FY-TEST",
            start_date=self.today.replace(month=1, day=1),
            end_date=self.today.replace(month=12, day=31),
            is_closed=False,
        )
        self.period = FiscalPeriod.objects.create(
            tenant=self.tenant,
            fiscal_year=self.fy,
            period_no=1,
            name="P1",
            start_date=self.today.replace(month=1, day=1),
            end_date=self.today.replace(month=12, day=31),
            is_closed=False,
        )
        self.supplier = Supplier.objects.create(tenant=self.tenant, supplier_code="SUP-1", name="Supplier 1")
        self.customer = Customer.objects.create(tenant=self.tenant, customer_code="CUS-1", name="Customer 1")
        self.expense_acc = Account.objects.create(
            tenant=self.tenant,
            code="5010",
            name="Expense",
            account_type=Account.AccountType.EXPENSE,
            natural_side=Account.NaturalSide.DEBIT,
        )
        self.ap_acc = Account.objects.create(
            tenant=self.tenant,
            code="2010",
            name="AP",
            account_type=Account.AccountType.LIABILITY,
            natural_side=Account.NaturalSide.CREDIT,
        )
        self.cash_acc = Account.objects.create(
            tenant=self.tenant,
            code="1010",
            name="Cash",
            account_type=Account.AccountType.ASSET,
            natural_side=Account.NaturalSide.DEBIT,
        )
        self.ar_acc = Account.objects.create(
            tenant=self.tenant,
            code="1100",
            name="AR",
            account_type=Account.AccountType.ASSET,
            natural_side=Account.NaturalSide.DEBIT,
        )
        self.revenue_acc = Account.objects.create(
            tenant=self.tenant,
            code="4010",
            name="Revenue",
            account_type=Account.AccountType.INCOME,
            natural_side=Account.NaturalSide.CREDIT,
        )

    def test_closed_period_blocks_ap_invoice_post(self):
        self.period.is_closed = True
        self.period.save(update_fields=["is_closed"])
        invoice = APInvoice.objects.create(
            tenant=self.tenant,
            doc_no="AP-1",
            supplier=self.supplier,
            posting_date=self.today,
            subtotal=Decimal("100"),
            total_amount=Decimal("100"),
            expense_account=self.expense_acc,
            ap_account=self.ap_acc,
        )
        with self.assertRaises(ValidationError):
            post_ap_invoice(invoice=invoice)

    def test_ap_payment_creates_allocation_and_unapplied_amount(self):
        invoice = APInvoice.objects.create(
            tenant=self.tenant,
            doc_no="AP-2",
            supplier=self.supplier,
            posting_date=self.today,
            subtotal=Decimal("100"),
            total_amount=Decimal("100"),
            expense_account=self.expense_acc,
            ap_account=self.ap_acc,
            status=APInvoice.Status.POSTED,
        )
        payment = APPayment.objects.create(
            tenant=self.tenant,
            doc_no="APP-1",
            supplier=self.supplier,
            posting_date=self.today,
            amount=Decimal("150"),
            ap_account=self.ap_acc,
            cash_account=self.cash_acc,
        )
        post_ap_payment(payment=payment)
        payment.refresh_from_db()
        self.assertEqual(payment.unapplied_amount, Decimal("50"))
        alloc = APPaymentAllocation.objects.get(payment=payment, invoice=invoice)
        self.assertEqual(alloc.amount, Decimal("100"))

    def test_ar_receipt_allocates_to_selected_invoice_first(self):
        inv1 = ARInvoice.objects.create(
            tenant=self.tenant,
            doc_no="AR-1",
            customer=self.customer,
            posting_date=self.today,
            subtotal=Decimal("60"),
            total_amount=Decimal("60"),
            ar_account=self.ar_acc,
            revenue_account=self.revenue_acc,
            status=ARInvoice.Status.POSTED,
        )
        inv2 = ARInvoice.objects.create(
            tenant=self.tenant,
            doc_no="AR-2",
            customer=self.customer,
            posting_date=self.today,
            subtotal=Decimal("90"),
            total_amount=Decimal("90"),
            ar_account=self.ar_acc,
            revenue_account=self.revenue_acc,
            status=ARInvoice.Status.POSTED,
        )
        receipt = ARReceipt.objects.create(
            tenant=self.tenant,
            doc_no="ARR-1",
            customer=self.customer,
            posting_date=self.today,
            amount=Decimal("70"),
            ar_account=self.ar_acc,
            cash_account=self.cash_acc,
            ar_invoice=inv2,
        )
        post_ar_receipt(receipt=receipt)
        receipt.refresh_from_db()
        self.assertEqual(receipt.unapplied_amount, Decimal("0"))
        first_alloc = ARReceiptAllocation.objects.get(receipt=receipt, invoice=inv2)
        self.assertEqual(first_alloc.amount, Decimal("70"))
        self.assertFalse(ARReceiptAllocation.objects.filter(receipt=receipt, invoice=inv1).exists())
