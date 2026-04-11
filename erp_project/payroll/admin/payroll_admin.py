"""Payroll Admin - Professional & Simple"""
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.contrib.filters.admin import RangeDateFilter, ChoicesDropdownFilter

from payroll.models import (
    SalaryStructure, EmployeeSalary, SalaryMonth,
    SalarySlip, Bonus, AdvanceLoan,
    OvertimePolicy, DeductionRule, TaxSlab,
    SalaryAdvance, PayrollSettings
)


# ==================== SALARY STRUCTURE ADMIN ====================

@admin.register(SalaryStructure)
class SalaryStructureAdmin(ModelAdmin):
    list_display = ('code', 'name', 'basic_salary_percent', 'house_rent_percent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (('code', 'name'), 'description', 'is_active'),
            'classes': ['tab'],
        }),
        ('Salary Components (%)', {
            'fields': (
                ('basic_salary_percent', 'house_rent_percent'),
                ('medical_allowance_percent', 'conveyance_allowance_percent'),
                'food_allowance',
            ),
            'classes': ['tab'],
        }),
    )


# ==================== EMPLOYEE SALARY ADMIN ====================

@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(ModelAdmin):
    list_display = ('employee', 'gross_salary', 'basic_salary', 'salary_structure', 'effective_from', 'is_active')
    list_filter = ('is_active', ('effective_from', RangeDateFilter))
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    autocomplete_fields = ['employee', 'salary_structure']
    
    fieldsets = (
        ('Employee & Structure', {
            'fields': (('employee', 'salary_structure'), 'gross_salary', ('effective_from', 'is_active')),
            'classes': ['tab'],
        }),
        ('Salary Breakdown (Auto-calculated)', {
            'fields': (
                ('basic_salary', 'house_rent'),
                ('medical_allowance', 'conveyance_allowance'),
                'food_allowance',
            ),
            'classes': ['tab'],
        }),
        ('Bank Details', {
            'fields': (('bank_name', 'bank_account_no'), 'bank_branch'),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('basic_salary', 'house_rent', 'medical_allowance', 'conveyance_allowance', 'food_allowance')


# ==================== SALARY SLIP INLINE ====================

class SalarySlipInline(TabularInline):
    model = SalarySlip
    extra = 0
    fields = ('employee', 'gross_salary', 'total_deductions', 'net_salary', 'is_paid')
    readonly_fields = ('gross_salary', 'total_deductions', 'net_salary')
    can_delete = False
    tab = True


# ==================== SALARY MONTH ADMIN ====================

@admin.register(SalaryMonth)
class SalaryMonthAdmin(ModelAdmin):
    list_display = ('get_month_year', 'display_status', 'total_employees', 'total_gross', 'total_net', 'processed_at')
    list_filter = (('status', ChoicesDropdownFilter), 'year', 'month')
    search_fields = ('notes',)
    
    inlines = [SalarySlipInline]
    
    fieldsets = (
        ('Period', {
            'fields': (('month', 'year'), 'status'),
            'classes': ['tab'],
        }),
        ('Summary', {
            'fields': (
                ('total_employees', 'total_gross'),
                ('total_deductions', 'total_net'),
            ),
            'classes': ['tab'],
        }),
        ('Processing Info', {
            'fields': (('processed_by', 'processed_at'), 'notes'),
            'classes': ['tab'],
        }),
    )
    
    @display(description='Period')
    def get_month_year(self, obj):
        return f"{obj.get_month_display()} {obj.year}"
    
    @display(description='Status', label={
        'draft': 'secondary',
        'processing': 'warning',
        'processed': 'info',
        'paid': 'success',
        'closed': 'danger',
    })
    def display_status(self, obj):
        return obj.status


# ==================== SALARY SLIP ADMIN ====================

@admin.register(SalarySlip)
class SalarySlipAdmin(ModelAdmin):
    list_display = ('employee', 'salary_month', 'gross_salary', 'total_deductions', 'net_salary', 'display_paid')
    list_filter = ('is_paid', ('salary_month', admin.RelatedOnlyFieldListFilter))
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    autocomplete_fields = ['employee', 'salary_month']
    
    fieldsets = (
        ('Basic Info', {
            'fields': (('salary_month', 'employee'),),
            'classes': ['tab'],
        }),
        ('Earnings', {
            'fields': (
                ('basic_salary', 'house_rent'),
                ('medical_allowance', 'conveyance_allowance'),
                ('food_allowance', 'overtime_amount'),
                ('bonus', 'other_earnings'),
                'gross_salary',
            ),
            'classes': ['tab'],
        }),
        ('Deductions', {
            'fields': (
                ('absent_deduction', 'late_deduction'),
                ('advance_deduction', 'loan_deduction'),
                ('tax_deduction', 'pf_deduction'),
                'other_deductions',
                'total_deductions',
            ),
            'classes': ['tab'],
        }),
        ('Net Pay', {
            'fields': ('net_salary',),
            'classes': ['tab'],
        }),
        ('Attendance Summary', {
            'fields': (
                ('total_days', 'present_days'),
                ('absent_days', 'leave_days'),
                ('weekend_days', 'overtime_hours'),
            ),
            'classes': ['tab'],
        }),
        ('Payment', {
            'fields': (('is_paid', 'paid_date'), 'payment_method', 'remarks'),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('gross_salary', 'total_deductions', 'net_salary')
    
    @display(description='Paid', label={True: 'success', False: 'danger'})
    def display_paid(self, obj):
        return obj.is_paid


# ==================== BONUS ADMIN ====================

@admin.register(Bonus)
class BonusAdmin(ModelAdmin):
    list_display = ('employee', 'name', 'bonus_type', 'amount', 'get_period', 'display_paid')
    list_filter = (('bonus_type', ChoicesDropdownFilter), 'is_paid', 'year', 'month')
    search_fields = ('employee__first_name', 'employee__last_name', 'name')
    autocomplete_fields = ['employee']
    
    fieldsets = (
        ('Bonus Details', {
            'fields': (('employee', 'name'), ('bonus_type', 'amount'), ('month', 'year')),
            'classes': ['tab'],
        }),
        ('Payment', {
            'fields': (('is_paid', 'paid_date'), 'remarks'),
            'classes': ['tab'],
        }),
    )
    
    @display(description='Period')
    def get_period(self, obj):
        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return f"{months[obj.month]} {obj.year}"
    
    @display(description='Paid', label={True: 'success', False: 'warning'})
    def display_paid(self, obj):
        return obj.is_paid


# ==================== ADVANCE/LOAN ADMIN ====================

@admin.register(AdvanceLoan)
class AdvanceLoanAdmin(ModelAdmin):
    list_display = ('employee', 'loan_type', 'amount', 'installments', 'paid_installments', 'remaining_amount', 'display_status')
    list_filter = (('loan_type', ChoicesDropdownFilter), ('status', ChoicesDropdownFilter))
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ['employee']
    
    fieldsets = (
        ('Loan Details', {
            'fields': (('employee', 'loan_type'), 'amount', 'reason'),
            'classes': ['tab'],
        }),
        ('Installments', {
            'fields': (
                ('installments', 'installment_amount'),
                ('paid_installments', 'remaining_amount'),
            ),
            'classes': ['tab'],
        }),
        ('Status & Approval', {
            'fields': (
                'status',
                ('request_date', 'approved_date'),
                'approved_by',
                'remarks',
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('installment_amount', 'remaining_amount')
    
    @display(description='Status', label={
        'pending': 'warning',
        'approved': 'info',
        'rejected': 'danger',
        'paid': 'success',
        'completed': 'secondary',
    })
    def display_status(self, obj):
        return obj.status



# ==================== OVERTIME POLICY ADMIN ====================

@admin.register(OvertimePolicy)
class OvertimePolicyAdmin(ModelAdmin):
    list_display = ('code', 'name', 'regular_ot_rate', 'weekend_ot_rate', 'holiday_ot_rate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    
    fieldsets = (
        ('Policy Details', {
            'fields': (('code', 'name'), 'description', 'is_active'),
            'classes': ['tab'],
        }),
        ('OT Rates (Multiplier)', {
            'fields': (
                ('regular_ot_rate', 'weekend_ot_rate'),
                'holiday_ot_rate',
            ),
            'classes': ['tab'],
        }),
        ('Calculation', {
            'fields': (('calculation_base', 'min_ot_hours'),),
            'classes': ['tab'],
        }),
    )


# ==================== DEDUCTION RULE ADMIN ====================

@admin.register(DeductionRule)
class DeductionRuleAdmin(ModelAdmin):
    list_display = ('name', 'deduction_type', 'calculation_method', 'grace_minutes', 'is_active')
    list_filter = (('deduction_type', ChoicesDropdownFilter), ('calculation_method', ChoicesDropdownFilter), 'is_active')
    search_fields = ('name',)
    
    fieldsets = (
        ('Rule Details', {
            'fields': (('name', 'deduction_type'), 'is_active'),
            'classes': ['tab'],
        }),
        ('Calculation', {
            'fields': (('calculation_method', 'fixed_amount'), 'grace_minutes', 'description'),
            'classes': ['tab'],
        }),
    )


# ==================== TAX SLAB ADMIN ====================

@admin.register(TaxSlab)
class TaxSlabAdmin(ModelAdmin):
    list_display = ('name', 'min_income', 'max_income', 'tax_rate', 'financial_year', 'is_active')
    list_filter = ('is_active', 'financial_year')
    search_fields = ('name',)
    
    fieldsets = (
        ('Slab Details', {
            'fields': ('name', 'financial_year', 'is_active'),
            'classes': ['tab'],
        }),
        ('Income Range', {
            'fields': (('min_income', 'max_income'),),
            'classes': ['tab'],
        }),
        ('Tax', {
            'fields': (('tax_rate', 'fixed_tax'),),
            'classes': ['tab'],
        }),
    )


# ==================== SALARY ADVANCE ADMIN ====================

@admin.register(SalaryAdvance)
class SalaryAdvanceAdmin(ModelAdmin):
    list_display = ('employee', 'amount', 'request_date', 'required_date', 'display_status', 'is_deducted')
    list_filter = (('status', ChoicesDropdownFilter), 'is_deducted')
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ['employee']
    
    fieldsets = (
        ('Advance Details', {
            'fields': (('employee', 'amount'), ('request_date', 'required_date'), 'reason'),
            'classes': ['tab'],
        }),
        ('Deduction', {
            'fields': (('deduct_from_month', 'deduct_from_year'), 'is_deducted'),
            'classes': ['tab'],
        }),
        ('Status & Approval', {
            'fields': ('status', ('approved_date', 'approved_by'), 'remarks'),
            'classes': ['tab'],
        }),
    )
    
    @display(description='Status', label={
        'pending': 'warning',
        'approved': 'info',
        'rejected': 'danger',
        'paid': 'success',
        'deducted': 'secondary',
    })
    def display_status(self, obj):
        return obj.status


# ==================== PAYROLL SETTINGS ADMIN ====================

@admin.register(PayrollSettings)
class PayrollSettingsAdmin(ModelAdmin):
    list_display = ('working_days_per_month', 'working_hours_per_day', 'pf_employee_percent', 'enable_tax_deduction', 'is_active')
    
    fieldsets = (
        ('Working Days', {
            'fields': (('working_days_per_month', 'working_hours_per_day'),),
            'classes': ['tab'],
        }),
        ('Policies', {
            'fields': ('overtime_policy', ('absent_deduction_rule', 'late_deduction_rule')),
            'classes': ['tab'],
        }),
        ('PF Settings', {
            'fields': (('pf_employee_percent', 'pf_employer_percent'),),
            'classes': ['tab'],
        }),
        ('Tax', {
            'fields': ('enable_tax_deduction',),
            'classes': ['tab'],
        }),
        ('Status', {
            'fields': ('is_active',),
            'classes': ['tab'],
        }),
    )
    autocomplete_fields = ['overtime_policy', 'absent_deduction_rule', 'late_deduction_rule']
    
    def has_add_permission(self, request):
        # Only one settings instance allowed
        return not PayrollSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


# Import new models
from payroll.models import (
    OvertimePolicy, DeductionRule, TaxSlab,
    SalaryAdvance, PayrollSettings
)
