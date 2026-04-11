"""
Compliance Models - Bangladesh Labor Law
Professional Compliance Management
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from hrm.models import Employee, LeaveType, Department, Designation


# ==================== PROVIDENT FUND ====================

class ProvidentFund(models.Model):
    """Employee Provident Fund (PF)"""
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name='provident_fund',
        verbose_name=_("Employee")
    )
    
    # Contribution Rates
    employee_contribution_percent = models.DecimalField(
        _("Employee Contribution (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00')
    )
    employer_contribution_percent = models.DecimalField(
        _("Employer Contribution (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00')
    )
    
    # Balances
    employee_balance = models.DecimalField(
        _("Employee Balance"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    employer_balance = models.DecimalField(
        _("Employer Balance"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_balance = models.DecimalField(
        _("Total Balance"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    start_date = models.DateField(_("Start Date"))
    is_active = models.BooleanField(_("Active"), default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Provident Fund")
        verbose_name_plural = _("Provident Funds")
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - PF: ৳{self.total_balance}"


# ==================== GRATUITY ====================

class Gratuity(models.Model):
    """Gratuity Calculation"""
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name='gratuity',
        verbose_name=_("Employee")
    )
    
    # Calculation
    years_of_service = models.DecimalField(
        _("Years of Service"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    last_basic_salary = models.DecimalField(
        _("Last Basic Salary"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    gratuity_amount = models.DecimalField(
        _("Gratuity Amount"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Formula: (Last Basic × Years of Service × 2) / 12")
    )
    
    is_paid = models.BooleanField(_("Paid"), default=False)
    paid_date = models.DateField(_("Paid Date"), null=True, blank=True)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Gratuity")
        verbose_name_plural = _("Gratuities")
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - Gratuity: ৳{self.gratuity_amount}"
    
    def calculate_gratuity(self):
        """Calculate gratuity: (Last Basic × Years × 2) / 12"""
        self.gratuity_amount = (self.last_basic_salary * self.years_of_service * 2) / 12


# ==================== INCREMENT ====================

class Increment(models.Model):
    """Salary Increment History"""
    INCREMENT_TYPE_CHOICES = [
        ('annual', _('Annual Increment')),
        ('promotion', _('Promotion')),
        ('performance', _('Performance')),
        ('adjustment', _('Adjustment')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='increments',
        verbose_name=_("Employee")
    )
    
    increment_type = models.CharField(_("Type"), max_length=20, choices=INCREMENT_TYPE_CHOICES)
    
    previous_salary = models.DecimalField(
        _("Previous Salary"),
        max_digits=10,
        decimal_places=2
    )
    new_salary = models.DecimalField(
        _("New Salary"),
        max_digits=10,
        decimal_places=2
    )
    increment_amount = models.DecimalField(
        _("Increment Amount"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    increment_percent = models.DecimalField(
        _("Increment (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    effective_date = models.DateField(_("Effective Date"))
    approved_by = models.CharField(_("Approved By"), max_length=100)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Increment")
        verbose_name_plural = _("Increments")
        ordering = ['-effective_date']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_increment_type_display()} - ৳{self.increment_amount}"
    
    def calculate_increment(self):
        """Calculate increment amount and percentage"""
        self.increment_amount = self.new_salary - self.previous_salary
        if self.previous_salary > 0:
            self.increment_percent = (self.increment_amount / self.previous_salary) * 100
    
    def save(self, *args, **kwargs):
        self.calculate_increment()
        super().save(*args, **kwargs)


# ==================== WARNING/SHOW CAUSE ====================

class Warning(models.Model):
    """Warning/Show Cause Notice"""
    WARNING_TYPE_CHOICES = [
        ('verbal', _('Verbal Warning')),
        ('written', _('Written Warning')),
        ('show_cause', _('Show Cause Notice')),
        ('final', _('Final Warning')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='warnings',
        verbose_name=_("Employee")
    )
    
    warning_type = models.CharField(_("Type"), max_length=20, choices=WARNING_TYPE_CHOICES)
    warning_date = models.DateField(_("Warning Date"))
    
    reason = models.TextField(_("Reason"))
    action_taken = models.TextField(_("Action Taken"), blank=True)
    
    issued_by = models.CharField(_("Issued By"), max_length=100)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Warning")
        verbose_name_plural = _("Warnings")
        ordering = ['-warning_date']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_warning_type_display()}"


# ==================== TRANSFER/PROMOTION ====================

class Transfer(models.Model):
    """Transfer/Promotion Record"""
    TRANSFER_TYPE_CHOICES = [
        ('transfer', _('Transfer')),
        ('promotion', _('Promotion')),
        ('demotion', _('Demotion')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='transfers',
        verbose_name=_("Employee")
    )
    
    transfer_type = models.CharField(_("Type"), max_length=20, choices=TRANSFER_TYPE_CHOICES)
    
    # From
    from_department = models.ForeignKey(
        'hrm.Department',
        on_delete=models.PROTECT,
        related_name='transfers_from',
        verbose_name=_("From Department"),
        null=True,
        blank=True
    )
    from_designation = models.ForeignKey(
        'hrm.Designation',
        on_delete=models.PROTECT,
        related_name='transfers_from',
        verbose_name=_("From Designation"),
        null=True,
        blank=True
    )
    
    # To
    to_department = models.ForeignKey(
        'hrm.Department',
        on_delete=models.PROTECT,
        related_name='transfers_to',
        verbose_name=_("To Department"),
        null=True,
        blank=True
    )
    to_designation = models.ForeignKey(
        'hrm.Designation',
        on_delete=models.PROTECT,
        related_name='transfers_to',
        verbose_name=_("To Designation"),
        null=True,
        blank=True
    )
    
    effective_date = models.DateField(_("Effective Date"))
    approved_by = models.CharField(_("Approved By"), max_length=100)
    
    reason = models.TextField(_("Reason"))
    remarks = models.TextField(_("Remarks"), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Transfer/Promotion")
        verbose_name_plural = _("Transfers/Promotions")
        ordering = ['-effective_date']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_transfer_type_display()}"


# ==================== APPOINTMENT LETTER ====================

class AppointmentLetter(models.Model):
    """Appointment Letter"""
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name='appointment_letter',
        verbose_name=_("Employee")
    )
    
    letter_number = models.CharField(_("Letter Number"), max_length=50, unique=True)
    issue_date = models.DateField(_("Issue Date"))
    joining_date = models.DateField(_("Joining Date"))
    
    designation = models.ForeignKey(
        'hrm.Designation',
        on_delete=models.PROTECT,
        verbose_name=_("Designation")
    )
    department = models.ForeignKey(
        'hrm.Department',
        on_delete=models.PROTECT,
        verbose_name=_("Department")
    )
    
    salary = models.DecimalField(
        _("Salary"),
        max_digits=10,
        decimal_places=2
    )
    
    probation_period = models.IntegerField(_("Probation Period (months)"), default=3)
    
    terms_conditions = models.TextField(_("Terms & Conditions"), blank=True)
    
    issued_by = models.CharField(_("Issued By"), max_length=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Appointment Letter")
        verbose_name_plural = _("Appointment Letters")
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.letter_number}"



# ==================== LEAVE ENTITLEMENT ====================

class LeaveEntitlement(models.Model):
    """Annual Leave Entitlement"""
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_entitlements',
        verbose_name=_("Employee")
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='entitlements',
        verbose_name=_("Leave Type")
    )
    
    year = models.IntegerField(_("Year"))
    entitled_days = models.DecimalField(
        _("Entitled Days"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    used_days = models.DecimalField(
        _("Used Days"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    carried_forward = models.DecimalField(
        _("Carried Forward"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Leave Entitlement")
        verbose_name_plural = _("Leave Entitlements")
        ordering = ['-year', 'employee']
        unique_together = [['employee', 'leave_type', 'year']]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.name} - {self.year}"
    
    @property
    def remaining_days(self):
        return self.entitled_days + self.carried_forward - self.used_days


# ==================== SERVICE BOOK ====================

class ServiceBook(models.Model):
    """Employee Service Book"""
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name='service_book',
        verbose_name=_("Employee")
    )
    
    # Joining Details
    joining_date = models.DateField(_("Joining Date"))
    confirmation_date = models.DateField(_("Confirmation Date"), null=True, blank=True)
    probation_period = models.IntegerField(_("Probation Period (months)"), default=3)
    
    # Current Position
    current_department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='service_books',
        verbose_name=_("Current Department")
    )
    current_designation = models.ForeignKey(
        Designation,
        on_delete=models.PROTECT,
        related_name='service_books',
        verbose_name=_("Current Designation")
    )
    
    # Service Details
    total_service_years = models.DecimalField(
        _("Total Service (Years)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Performance
    last_appraisal_date = models.DateField(_("Last Appraisal Date"), null=True, blank=True)
    next_appraisal_date = models.DateField(_("Next Appraisal Date"), null=True, blank=True)
    performance_rating = models.CharField(_("Performance Rating"), max_length=20, blank=True)
    
    # Disciplinary
    total_warnings = models.IntegerField(_("Total Warnings"), default=0)
    last_warning_date = models.DateField(_("Last Warning Date"), null=True, blank=True)
    
    # Leave Summary
    total_casual_leave = models.DecimalField(_("Total Casual Leave"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    total_sick_leave = models.DecimalField(_("Total Sick Leave"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    total_annual_leave = models.DecimalField(_("Total Annual Leave"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    remarks = models.TextField(_("Remarks"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Service Book")
        verbose_name_plural = _("Service Books")
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - Service Book"


# ==================== RESIGNATION ====================

class Resignation(models.Model):
    """Employee Resignation"""
    STATUS_CHOICES = [
        ('submitted', _('Submitted')),
        ('under_review', _('Under Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('withdrawn', _('Withdrawn')),
        ('completed', _('Completed')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='resignations',
        verbose_name=_("Employee")
    )
    
    submission_date = models.DateField(_("Submission Date"))
    resignation_date = models.DateField(_("Resignation Date"))
    last_working_day = models.DateField(_("Last Working Day"))
    
    # Notice Period
    notice_period_days = models.IntegerField(_("Notice Period (days)"), default=30)
    notice_period_served = models.BooleanField(_("Notice Period Served"), default=False)
    
    reason = models.TextField(_("Reason"))
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='submitted')
    
    # Approval
    reviewed_by = models.CharField(_("Reviewed By"), max_length=100, blank=True)
    reviewed_date = models.DateField(_("Reviewed Date"), null=True, blank=True)
    review_comments = models.TextField(_("Review Comments"), blank=True)
    
    # Exit Process
    exit_interview_done = models.BooleanField(_("Exit Interview Done"), default=False)
    exit_interview_date = models.DateField(_("Exit Interview Date"), null=True, blank=True)
    clearance_completed = models.BooleanField(_("Clearance Completed"), default=False)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Resignation")
        verbose_name_plural = _("Resignations")
        ordering = ['-submission_date']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.submission_date}"


# ==================== TERMINATION ====================

class Termination(models.Model):
    """Employee Termination"""
    TERMINATION_TYPE_CHOICES = [
        ('voluntary', _('Voluntary')),
        ('involuntary', _('Involuntary')),
        ('retirement', _('Retirement')),
        ('contract_end', _('Contract End')),
        ('death', _('Death')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='terminations',
        verbose_name=_("Employee")
    )
    
    termination_type = models.CharField(_("Type"), max_length=20, choices=TERMINATION_TYPE_CHOICES)
    termination_date = models.DateField(_("Termination Date"))
    last_working_day = models.DateField(_("Last Working Day"))
    
    reason = models.TextField(_("Reason"))
    
    # Notice
    notice_given = models.BooleanField(_("Notice Given"), default=False)
    notice_period_days = models.IntegerField(_("Notice Period (days)"), default=0)
    
    # Approval
    approved_by = models.CharField(_("Approved By"), max_length=100)
    approved_date = models.DateField(_("Approved Date"))
    
    # Exit Process
    exit_interview_done = models.BooleanField(_("Exit Interview Done"), default=False)
    clearance_completed = models.BooleanField(_("Clearance Completed"), default=False)
    
    # Final Settlement
    final_settlement_amount = models.DecimalField(
        _("Final Settlement"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    settlement_paid = models.BooleanField(_("Settlement Paid"), default=False)
    settlement_date = models.DateField(_("Settlement Date"), null=True, blank=True)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Termination")
        verbose_name_plural = _("Terminations")
        ordering = ['-termination_date']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_termination_type_display()}"


# ==================== PERFORMANCE APPRAISAL ====================

class PerformanceAppraisal(models.Model):
    """Employee Performance Appraisal"""
    RATING_CHOICES = [
        ('outstanding', _('Outstanding')),
        ('exceeds', _('Exceeds Expectations')),
        ('meets', _('Meets Expectations')),
        ('needs_improvement', _('Needs Improvement')),
        ('unsatisfactory', _('Unsatisfactory')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='appraisals',
        verbose_name=_("Employee")
    )
    
    appraisal_period_start = models.DateField(_("Period Start"))
    appraisal_period_end = models.DateField(_("Period End"))
    appraisal_date = models.DateField(_("Appraisal Date"))
    
    # Ratings
    overall_rating = models.CharField(_("Overall Rating"), max_length=20, choices=RATING_CHOICES)
    
    # Scores (out of 5)
    quality_of_work = models.DecimalField(_("Quality of Work"), max_digits=3, decimal_places=1, default=Decimal('0.0'))
    productivity = models.DecimalField(_("Productivity"), max_digits=3, decimal_places=1, default=Decimal('0.0'))
    attendance = models.DecimalField(_("Attendance"), max_digits=3, decimal_places=1, default=Decimal('0.0'))
    teamwork = models.DecimalField(_("Teamwork"), max_digits=3, decimal_places=1, default=Decimal('0.0'))
    communication = models.DecimalField(_("Communication"), max_digits=3, decimal_places=1, default=Decimal('0.0'))
    
    total_score = models.DecimalField(_("Total Score"), max_digits=4, decimal_places=1, default=Decimal('0.0'))
    
    # Comments
    strengths = models.TextField(_("Strengths"), blank=True)
    areas_for_improvement = models.TextField(_("Areas for Improvement"), blank=True)
    goals_for_next_period = models.TextField(_("Goals for Next Period"), blank=True)
    
    # Appraiser
    appraised_by = models.CharField(_("Appraised By"), max_length=100)
    
    # Recommendation
    recommend_increment = models.BooleanField(_("Recommend Increment"), default=False)
    recommend_promotion = models.BooleanField(_("Recommend Promotion"), default=False)
    
    remarks = models.TextField(_("Remarks"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Performance Appraisal")
        verbose_name_plural = _("Performance Appraisals")
        ordering = ['-appraisal_date']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.appraisal_date}"
    
    def calculate_total_score(self):
        """Calculate total score"""
        self.total_score = (
            self.quality_of_work + self.productivity + self.attendance +
            self.teamwork + self.communication
        )
    
    def save(self, *args, **kwargs):
        self.calculate_total_score()
        super().save(*args, **kwargs)


# ==================== TRAINING ====================

class Training(models.Model):
    """Employee Training Record"""
    TRAINING_TYPE_CHOICES = [
        ('induction', _('Induction')),
        ('technical', _('Technical')),
        ('soft_skills', _('Soft Skills')),
        ('safety', _('Safety')),
        ('compliance', _('Compliance')),
        ('management', _('Management')),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('ongoing', _('Ongoing')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    title = models.CharField(_("Training Title"), max_length=200)
    training_type = models.CharField(_("Type"), max_length=20, choices=TRAINING_TYPE_CHOICES)
    
    # Participants
    employees = models.ManyToManyField(
        Employee,
        related_name='trainings',
        verbose_name=_("Participants")
    )
    
    # Schedule
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    duration_hours = models.DecimalField(_("Duration (hours)"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Trainer
    trainer_name = models.CharField(_("Trainer Name"), max_length=100)
    trainer_organization = models.CharField(_("Trainer Organization"), max_length=200, blank=True)
    
    # Venue
    venue = models.CharField(_("Venue"), max_length=200)
    
    # Cost
    cost_per_person = models.DecimalField(
        _("Cost per Person"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    description = models.TextField(_("Description"), blank=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Training")
        verbose_name_plural = _("Trainings")
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} - {self.start_date}"
