"""
Payroll Models - Bangladesh Garments Industry
Simple and Professional Payroll System
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from hrm.models import Employee, Attendance, Overtime as HRMOvertime, Holiday


# ==================== SALARY STRUCTURE ====================

class SalaryStructure(models.Model):
    """Salary Structure Template"""
    name = models.CharField(_("Structure Name"), max_length=100)
    code = models.CharField(_("Structure Code"), max_length=50, unique=True)
    
    # Basic Components (% of Gross or Fixed Amount)
    basic_salary_percent = models.DecimalField(
        _("Basic Salary (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('60.00'),
        help_text=_("Percentage of gross salary")
    )
    house_rent_percent = models.DecimalField(
        _("House Rent (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('30.00')
    )
    medical_allowance_percent = models.DecimalField(
        _("Medical Allowance (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00')
    )
    conveyance_allowance_percent = models.DecimalField(
        _("Conveyance (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00')
    )
    
    # Additional Allowances
    food_allowance = models.DecimalField(
        _("Food Allowance (Fixed)"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    description = models.TextField(_("Description"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Salary Structure")
        verbose_name_plural = _("Salary Structures")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


# ==================== EMPLOYEE SALARY ====================

class EmployeeSalary(models.Model):
    """Employee Salary Assignment"""
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name='payroll_salary',
        verbose_name=_("Employee")
    )
    salary_structure = models.ForeignKey(
        SalaryStructure,
        on_delete=models.PROTECT,
        related_name='employee_salaries',
        verbose_name=_("Salary Structure")
    )
    
    # Gross Salary
    gross_salary = models.DecimalField(
        _("Gross Salary"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Calculated Components (auto-calculated from structure)
    basic_salary = models.DecimalField(
        _("Basic Salary"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    house_rent = models.DecimalField(
        _("House Rent"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    medical_allowance = models.DecimalField(
        _("Medical Allowance"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    conveyance_allowance = models.DecimalField(
        _("Conveyance"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    food_allowance = models.DecimalField(
        _("Food Allowance"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Bank Details
    bank_name = models.CharField(_("Bank Name"), max_length=100, blank=True)
    bank_account_no = models.CharField(_("Account Number"), max_length=50, blank=True)
    bank_branch = models.CharField(_("Branch"), max_length=100, blank=True)
    
    effective_from = models.DateField(_("Effective From"))
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Employee Salary")
        verbose_name_plural = _("Employee Salaries")
        ordering = ['employee']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - ৳{self.gross_salary}"
    
    def calculate_components(self):
        """Auto-calculate salary components from structure"""
        structure = self.salary_structure
        self.basic_salary = (self.gross_salary * structure.basic_salary_percent) / 100
        self.house_rent = (self.gross_salary * structure.house_rent_percent) / 100
        self.medical_allowance = (self.gross_salary * structure.medical_allowance_percent) / 100
        self.conveyance_allowance = (self.gross_salary * structure.conveyance_allowance_percent) / 100
        self.food_allowance = structure.food_allowance
    
    def save(self, *args, **kwargs):
        self.calculate_components()
        super().save(*args, **kwargs)


# ==================== SALARY PROCESSING ====================

class SalaryMonth(models.Model):
    """Monthly Salary Processing Period"""
    MONTH_CHOICES = [
        (1, _('January')), (2, _('February')), (3, _('March')),
        (4, _('April')), (5, _('May')), (6, _('June')),
        (7, _('July')), (8, _('August')), (9, _('September')),
        (10, _('October')), (11, _('November')), (12, _('December')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('processing', _('Processing')),
        ('processed', _('Processed')),
        ('paid', _('Paid')),
        ('closed', _('Closed')),
    ]
    
    month = models.IntegerField(_("Month"), choices=MONTH_CHOICES)
    year = models.IntegerField(_("Year"))
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Processing Info
    total_employees = models.IntegerField(_("Total Employees"), default=0)
    total_gross = models.DecimalField(_("Total Gross"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_deductions = models.DecimalField(_("Total Deductions"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_net = models.DecimalField(_("Total Net Pay"), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    processed_by = models.CharField(_("Processed By"), max_length=100, blank=True)
    processed_at = models.DateTimeField(_("Processed At"), null=True, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Salary Month")
        verbose_name_plural = _("Salary Months")
        ordering = ['-year', '-month']
        unique_together = [['month', 'year']]
    
    def __str__(self):
        return f"{self.get_month_display()} {self.year}"


# ==================== SALARY SLIP ====================

class SalarySlip(models.Model):
    """Individual Employee Salary Slip"""
    salary_month = models.ForeignKey(
        SalaryMonth,
        on_delete=models.CASCADE,
        related_name='salary_slips',
        verbose_name=_("Salary Month")
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='salary_slips',
        verbose_name=_("Employee")
    )
    
    # Earnings
    basic_salary = models.DecimalField(_("Basic Salary"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    house_rent = models.DecimalField(_("House Rent"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    medical_allowance = models.DecimalField(_("Medical"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    conveyance_allowance = models.DecimalField(_("Conveyance"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    food_allowance = models.DecimalField(_("Food"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    overtime_amount = models.DecimalField(_("Overtime"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    bonus = models.DecimalField(_("Bonus"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    other_earnings = models.DecimalField(_("Other Earnings"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    gross_salary = models.DecimalField(_("Gross Salary"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Deductions
    absent_deduction = models.DecimalField(_("Absent Deduction"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    late_deduction = models.DecimalField(_("Late Deduction"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    advance_deduction = models.DecimalField(_("Advance"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    loan_deduction = models.DecimalField(_("Loan"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_deduction = models.DecimalField(_("Tax"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    pf_deduction = models.DecimalField(_("PF"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    other_deductions = models.DecimalField(_("Other Deductions"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    total_deductions = models.DecimalField(_("Total Deductions"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Net Pay
    net_salary = models.DecimalField(_("Net Salary"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Attendance Summary
    total_days = models.IntegerField(_("Total Days"), default=0)
    present_days = models.IntegerField(_("Present Days"), default=0)
    absent_days = models.IntegerField(_("Absent Days"), default=0)
    leave_days = models.IntegerField(_("Leave Days"), default=0)
    weekend_days = models.IntegerField(_("Weekend Days"), default=0)
    overtime_hours = models.DecimalField(_("OT Hours"), max_digits=6, decimal_places=2, default=Decimal('0.00'))
    
    # Payment Info
    is_paid = models.BooleanField(_("Paid"), default=False)
    paid_date = models.DateField(_("Paid Date"), null=True, blank=True)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Salary Slip")
        verbose_name_plural = _("Salary Slips")
        ordering = ['-salary_month', 'employee']
        unique_together = [['salary_month', 'employee']]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.salary_month}"
    
    def calculate_totals(self):
        """Calculate gross, deductions, and net"""
        # Calculate gross
        self.gross_salary = (
            self.basic_salary + self.house_rent + self.medical_allowance +
            self.conveyance_allowance + self.food_allowance + 
            self.overtime_amount + self.bonus + self.other_earnings
        )
        
        # Calculate total deductions
        self.total_deductions = (
            self.absent_deduction + self.late_deduction + self.advance_deduction +
            self.loan_deduction + self.tax_deduction + self.pf_deduction + 
            self.other_deductions
        )
        
        # Calculate net
        self.net_salary = self.gross_salary - self.total_deductions
    
    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)


# ==================== BONUS ====================

class Bonus(models.Model):
    """Bonus Management"""
    BONUS_TYPE_CHOICES = [
        ('festival', _('Festival Bonus')),
        ('performance', _('Performance Bonus')),
        ('attendance', _('Attendance Bonus')),
        ('production', _('Production Bonus')),
        ('other', _('Other')),
    ]
    
    name = models.CharField(_("Bonus Name"), max_length=100)
    bonus_type = models.CharField(_("Bonus Type"), max_length=20, choices=BONUS_TYPE_CHOICES)
    month = models.IntegerField(_("Month"))
    year = models.IntegerField(_("Year"))
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='bonuses',
        verbose_name=_("Employee")
    )
    
    amount = models.DecimalField(
        _("Amount"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    is_paid = models.BooleanField(_("Paid"), default=False)
    paid_date = models.DateField(_("Paid Date"), null=True, blank=True)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Bonus")
        verbose_name_plural = _("Bonuses")
        ordering = ['-year', '-month', 'employee']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.name} - ৳{self.amount}"


# ==================== ADVANCE/LOAN ====================

class AdvanceLoan(models.Model):
    """Employee Advance/Loan"""
    TYPE_CHOICES = [
        ('advance', _('Advance')),
        ('loan', _('Loan')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('paid', _('Paid')),
        ('completed', _('Completed')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='advances_loans',
        verbose_name=_("Employee")
    )
    
    loan_type = models.CharField(_("Type"), max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(
        _("Amount"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    installments = models.IntegerField(_("Installments"), default=1)
    installment_amount = models.DecimalField(
        _("Installment Amount"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    paid_installments = models.IntegerField(_("Paid Installments"), default=0)
    remaining_amount = models.DecimalField(
        _("Remaining Amount"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    request_date = models.DateField(_("Request Date"))
    approved_date = models.DateField(_("Approved Date"), null=True, blank=True)
    approved_by = models.CharField(_("Approved By"), max_length=100, blank=True)
    
    reason = models.TextField(_("Reason"))
    remarks = models.TextField(_("Remarks"), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Advance/Loan")
        verbose_name_plural = _("Advances/Loans")
        ordering = ['-request_date']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_loan_type_display()} - ৳{self.amount}"
    
    def calculate_installment(self):
        """Calculate installment amount"""
        if self.installments > 0:
            self.installment_amount = self.amount / self.installments
            self.remaining_amount = self.amount
    
    def save(self, *args, **kwargs):
        if not self.installment_amount:
            self.calculate_installment()
        super().save(*args, **kwargs)



# ==================== OVERTIME POLICY ====================

class OvertimePolicy(models.Model):
    """Overtime Calculation Policy"""
    name = models.CharField(_("Policy Name"), max_length=100)
    code = models.CharField(_("Policy Code"), max_length=50, unique=True)
    
    # Rates
    regular_ot_rate = models.DecimalField(
        _("Regular OT Rate (multiplier)"),
        max_digits=4,
        decimal_places=2,
        default=Decimal('1.5'),
        help_text=_("e.g., 1.5 for time-and-a-half")
    )
    weekend_ot_rate = models.DecimalField(
        _("Weekend OT Rate (multiplier)"),
        max_digits=4,
        decimal_places=2,
        default=Decimal('2.0')
    )
    holiday_ot_rate = models.DecimalField(
        _("Holiday OT Rate (multiplier)"),
        max_digits=4,
        decimal_places=2,
        default=Decimal('2.0')
    )
    
    # Minimum OT hours to qualify
    min_ot_hours = models.DecimalField(
        _("Minimum OT Hours"),
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.5'),
        help_text=_("Minimum hours to qualify for OT payment")
    )
    
    # OT calculation base
    CALCULATION_BASE_CHOICES = [
        ('basic', _('Basic Salary')),
        ('gross', _('Gross Salary')),
    ]
    calculation_base = models.CharField(
        _("Calculation Base"),
        max_length=20,
        choices=CALCULATION_BASE_CHOICES,
        default='basic'
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    description = models.TextField(_("Description"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Overtime Policy")
        verbose_name_plural = _("Overtime Policies")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


# ==================== DEDUCTION RULES ====================

class DeductionRule(models.Model):
    """Salary Deduction Rules"""
    DEDUCTION_TYPE_CHOICES = [
        ('absent', _('Absent Deduction')),
        ('late', _('Late Deduction')),
        ('early_out', _('Early Out Deduction')),
    ]
    
    name = models.CharField(_("Rule Name"), max_length=100)
    deduction_type = models.CharField(_("Type"), max_length=20, choices=DEDUCTION_TYPE_CHOICES)
    
    # Calculation
    CALCULATION_METHOD_CHOICES = [
        ('per_day', _('Per Day')),
        ('per_hour', _('Per Hour')),
        ('fixed', _('Fixed Amount')),
    ]
    calculation_method = models.CharField(
        _("Calculation Method"),
        max_length=20,
        choices=CALCULATION_METHOD_CHOICES,
        default='per_day'
    )
    
    # For per_day: deduct full day salary
    # For per_hour: deduct hourly rate × hours
    # For fixed: deduct fixed amount
    fixed_amount = models.DecimalField(
        _("Fixed Amount"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Used only if calculation method is 'fixed'")
    )
    
    # Grace period (for late/early out)
    grace_minutes = models.IntegerField(
        _("Grace Minutes"),
        default=0,
        help_text=_("Grace period before deduction applies")
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    description = models.TextField(_("Description"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Deduction Rule")
        verbose_name_plural = _("Deduction Rules")
        ordering = ['deduction_type', 'name']
    
    def __str__(self):
        return f"{self.get_deduction_type_display()} - {self.name}"


# ==================== TAX SLAB ====================

class TaxSlab(models.Model):
    """Income Tax Slab (Bangladesh)"""
    name = models.CharField(_("Slab Name"), max_length=100)
    
    # Income Range
    min_income = models.DecimalField(
        _("Minimum Income"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    max_income = models.DecimalField(
        _("Maximum Income"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Leave blank for unlimited")
    )
    
    # Tax Rate
    tax_rate = models.DecimalField(
        _("Tax Rate (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Fixed Tax Amount (for progressive tax)
    fixed_tax = models.DecimalField(
        _("Fixed Tax Amount"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Fixed tax for this slab")
    )
    
    # Financial Year
    financial_year = models.CharField(_("Financial Year"), max_length=20, default="2024-2025")
    
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Tax Slab")
        verbose_name_plural = _("Tax Slabs")
        ordering = ['min_income']
    
    def __str__(self):
        max_str = f"{self.max_income}" if self.max_income else "Unlimited"
        return f"{self.name}: ৳{self.min_income} - ৳{max_str} @ {self.tax_rate}%"


# ==================== SALARY ADVANCE ====================

class SalaryAdvance(models.Model):
    """Salary Advance (separate from loan)"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('paid', _('Paid')),
        ('deducted', _('Deducted')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='salary_advances',
        verbose_name=_("Employee")
    )
    
    amount = models.DecimalField(
        _("Amount"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    request_date = models.DateField(_("Request Date"))
    required_date = models.DateField(_("Required Date"))
    
    # Deduction
    deduct_from_month = models.IntegerField(_("Deduct From Month"), null=True, blank=True)
    deduct_from_year = models.IntegerField(_("Deduct From Year"), null=True, blank=True)
    is_deducted = models.BooleanField(_("Deducted"), default=False)
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    approved_date = models.DateField(_("Approved Date"), null=True, blank=True)
    approved_by = models.CharField(_("Approved By"), max_length=100, blank=True)
    
    reason = models.TextField(_("Reason"))
    remarks = models.TextField(_("Remarks"), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Salary Advance")
        verbose_name_plural = _("Salary Advances")
        ordering = ['-request_date']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - ৳{self.amount} - {self.get_status_display()}"


# ==================== PAYROLL SETTINGS ====================

class PayrollSettings(models.Model):
    """Global Payroll Settings"""
    # Working Days
    working_days_per_month = models.IntegerField(_("Working Days/Month"), default=26)
    working_hours_per_day = models.DecimalField(
        _("Working Hours/Day"),
        max_digits=4,
        decimal_places=2,
        default=Decimal('8.0')
    )
    
    # Overtime
    overtime_policy = models.ForeignKey(
        OvertimePolicy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Default OT Policy")
    )
    
    # Deductions
    absent_deduction_rule = models.ForeignKey(
        DeductionRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='absent_settings',
        verbose_name=_("Absent Deduction Rule")
    )
    late_deduction_rule = models.ForeignKey(
        DeductionRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='late_settings',
        verbose_name=_("Late Deduction Rule")
    )
    
    # PF
    pf_employee_percent = models.DecimalField(
        _("PF Employee (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00')
    )
    pf_employer_percent = models.DecimalField(
        _("PF Employer (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00')
    )
    
    # Tax
    enable_tax_deduction = models.BooleanField(_("Enable Tax Deduction"), default=False)
    
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Payroll Settings")
        verbose_name_plural = _("Payroll Settings")
    
    def __str__(self):
        return "Payroll Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create settings"""
        settings, created = cls.objects.get_or_create(is_active=True)
        return settings
