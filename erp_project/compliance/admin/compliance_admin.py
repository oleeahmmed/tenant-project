"""Compliance Admin - Bangladesh Labor Law"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.contrib.filters.admin import RangeDateFilter, ChoicesDropdownFilter

from compliance.models import (
    ProvidentFund, Gratuity, Increment, Warning,
    Transfer, AppointmentLetter,
    LeaveEntitlement, ServiceBook, Resignation,
    Termination, PerformanceAppraisal, Training
)


# ==================== PROVIDENT FUND ADMIN ====================

@admin.register(ProvidentFund)
class ProvidentFundAdmin(ModelAdmin):
    list_display = ('employee', 'employee_balance', 'employer_balance', 'total_balance', 'is_active')
    list_filter = ('is_active', ('start_date', RangeDateFilter))
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    autocomplete_fields = ['employee']
    
    fieldsets = (
        ('Employee', {
            'fields': ('employee', ('start_date', 'is_active')),
            'classes': ['tab'],
        }),
        ('Contribution Rates', {
            'fields': (('employee_contribution_percent', 'employer_contribution_percent'),),
            'classes': ['tab'],
        }),
        ('Balances', {
            'fields': (
                ('employee_balance', 'employer_balance'),
                'total_balance',
            ),
            'classes': ['tab'],
        }),
    )


# ==================== GRATUITY ADMIN ====================

@admin.register(Gratuity)
class GratuityAdmin(ModelAdmin):
    list_display = ('employee', 'years_of_service', 'last_basic_salary', 'gratuity_amount', 'display_paid')
    list_filter = ('is_paid',)
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ['employee']
    
    fieldsets = (
        ('Employee', {
            'fields': ('employee',),
            'classes': ['tab'],
        }),
        ('Calculation', {
            'fields': (
                ('years_of_service', 'last_basic_salary'),
                'gratuity_amount',
            ),
            'classes': ['tab'],
        }),
        ('Payment', {
            'fields': (('is_paid', 'paid_date'), 'remarks'),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('gratuity_amount',)
    
    @display(description='Paid', label={True: 'success', False: 'warning'})
    def display_paid(self, obj):
        return obj.is_paid


# ==================== INCREMENT ADMIN ====================

@admin.register(Increment)
class IncrementAdmin(ModelAdmin):
    list_display = ('employee', 'increment_type', 'previous_salary', 'new_salary', 'increment_amount', 'increment_percent', 'effective_date')
    list_filter = (('increment_type', ChoicesDropdownFilter), ('effective_date', RangeDateFilter))
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ['employee']
    
    fieldsets = (
        ('Employee & Type', {
            'fields': (('employee', 'increment_type'), 'effective_date'),
            'classes': ['tab'],
        }),
        ('Salary Details', {
            'fields': (
                ('previous_salary', 'new_salary'),
                ('increment_amount', 'increment_percent'),
            ),
            'classes': ['tab'],
        }),
        ('Approval', {
            'fields': ('approved_by', 'remarks'),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('increment_amount', 'increment_percent')


# ==================== WARNING ADMIN ====================

@admin.register(Warning)
class WarningAdmin(ModelAdmin):
    list_display = ('employee', 'warning_type', 'warning_date', 'issued_by')
    list_filter = (('warning_type', ChoicesDropdownFilter), ('warning_date', RangeDateFilter))
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')
    autocomplete_fields = ['employee']
    
    fieldsets = (
        ('Warning Details', {
            'fields': (('employee', 'warning_type'), 'warning_date', 'issued_by'),
            'classes': ['tab'],
        }),
        ('Details', {
            'fields': ('reason', 'action_taken', 'remarks'),
            'classes': ['tab'],
        }),
    )


# ==================== TRANSFER ADMIN ====================

@admin.register(Transfer)
class TransferAdmin(ModelAdmin):
    list_display = ('employee', 'transfer_type', 'from_department', 'to_department', 'effective_date')
    list_filter = (('transfer_type', ChoicesDropdownFilter), ('effective_date', RangeDateFilter))
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ['employee', 'from_department', 'to_department', 'from_designation', 'to_designation']
    
    fieldsets = (
        ('Transfer Details', {
            'fields': (('employee', 'transfer_type'), 'effective_date'),
            'classes': ['tab'],
        }),
        ('From', {
            'fields': (('from_department', 'from_designation'),),
            'classes': ['tab'],
        }),
        ('To', {
            'fields': (('to_department', 'to_designation'),),
            'classes': ['tab'],
        }),
        ('Approval', {
            'fields': ('approved_by', 'reason', 'remarks'),
            'classes': ['tab'],
        }),
    )


# ==================== APPOINTMENT LETTER ADMIN ====================

@admin.register(AppointmentLetter)
class AppointmentLetterAdmin(ModelAdmin):
    list_display = ('employee', 'letter_number', 'designation', 'department', 'salary', 'issue_date', 'joining_date')
    list_filter = (('issue_date', RangeDateFilter), ('joining_date', RangeDateFilter))
    search_fields = ('employee__first_name', 'employee__last_name', 'letter_number')
    autocomplete_fields = ['employee', 'designation', 'department']
    
    fieldsets = (
        ('Letter Details', {
            'fields': (('letter_number', 'issue_date'), 'joining_date'),
            'classes': ['tab'],
        }),
        ('Employee Details', {
            'fields': (
                'employee',
                ('designation', 'department'),
                ('salary', 'probation_period'),
            ),
            'classes': ['tab'],
        }),
        ('Terms', {
            'fields': ('terms_conditions', 'issued_by'),
            'classes': ['tab'],
        }),
    )



# ==================== LEAVE ENTITLEMENT ADMIN ====================

@admin.register(LeaveEntitlement)
class LeaveEntitlementAdmin(ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'entitled_days', 'used_days', 'remaining_days')
    list_filter = ('year',)
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ['employee', 'leave_type']
    
    fieldsets = (
        ('Entitlement Details', {
            'fields': (('employee', 'leave_type'), 'year'),
            'classes': ['tab'],
        }),
        ('Days', {
            'fields': (
                ('entitled_days', 'used_days'),
                'carried_forward',
            ),
            'classes': ['tab'],
        }),
    )


# ==================== SERVICE BOOK ADMIN ====================

@admin.register(ServiceBook)
class ServiceBookAdmin(ModelAdmin):
    list_display = ('employee', 'joining_date', 'current_department', 'current_designation', 'total_service_years', 'performance_rating')
    list_filter = (('joining_date', RangeDateFilter),)
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ['employee', 'current_department', 'current_designation']
    
    fieldsets = (
        ('Employee', {
            'fields': ('employee',),
            'classes': ['tab'],
        }),
        ('Joining Details', {
            'fields': (
                ('joining_date', 'confirmation_date'),
                'probation_period',
            ),
            'classes': ['tab'],
        }),
        ('Current Position', {
            'fields': (
                ('current_department', 'current_designation'),
                'total_service_years',
            ),
            'classes': ['tab'],
        }),
        ('Performance', {
            'fields': (
                ('last_appraisal_date', 'next_appraisal_date'),
                'performance_rating',
            ),
            'classes': ['tab'],
        }),
        ('Disciplinary', {
            'fields': (('total_warnings', 'last_warning_date'),),
            'classes': ['tab'],
        }),
        ('Leave Summary', {
            'fields': (
                ('total_casual_leave', 'total_sick_leave'),
                'total_annual_leave',
            ),
            'classes': ['tab'],
        }),
        ('Remarks', {
            'fields': ('remarks',),
            'classes': ['tab'],
        }),
    )


# ==================== RESIGNATION ADMIN ====================

@admin.register(Resignation)
class ResignationAdmin(ModelAdmin):
    list_display = ('employee', 'submission_date', 'resignation_date', 'last_working_day', 'display_status', 'notice_period_served')
    list_filter = (('status', ChoicesDropdownFilter), 'notice_period_served', ('submission_date', RangeDateFilter))
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ['employee']
    
    fieldsets = (
        ('Resignation Details', {
            'fields': (
                'employee',
                ('submission_date', 'resignation_date'),
                'last_working_day',
                'reason',
            ),
            'classes': ['tab'],
        }),
        ('Notice Period', {
            'fields': (('notice_period_days', 'notice_period_served'),),
            'classes': ['tab'],
        }),
        ('Status & Review', {
            'fields': (
                'status',
                ('reviewed_by', 'reviewed_date'),
                'review_comments',
            ),
            'classes': ['tab'],
        }),
        ('Exit Process', {
            'fields': (
                ('exit_interview_done', 'exit_interview_date'),
                'clearance_completed',
                'remarks',
            ),
            'classes': ['tab'],
        }),
    )
    
    @display(description='Status', label={
        'submitted': 'warning',
        'under_review': 'info',
        'approved': 'success',
        'rejected': 'danger',
        'withdrawn': 'secondary',
        'completed': 'primary',
    })
    def display_status(self, obj):
        return obj.status


# ==================== TERMINATION ADMIN ====================

@admin.register(Termination)
class TerminationAdmin(ModelAdmin):
    list_display = ('employee', 'termination_type', 'termination_date', 'last_working_day', 'settlement_paid')
    list_filter = (('termination_type', ChoicesDropdownFilter), 'settlement_paid', ('termination_date', RangeDateFilter))
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ['employee']
    
    fieldsets = (
        ('Termination Details', {
            'fields': (
                ('employee', 'termination_type'),
                ('termination_date', 'last_working_day'),
                'reason',
            ),
            'classes': ['tab'],
        }),
        ('Notice', {
            'fields': (('notice_given', 'notice_period_days'),),
            'classes': ['tab'],
        }),
        ('Approval', {
            'fields': (('approved_by', 'approved_date'),),
            'classes': ['tab'],
        }),
        ('Exit Process', {
            'fields': (
                ('exit_interview_done', 'clearance_completed'),
            ),
            'classes': ['tab'],
        }),
        ('Final Settlement', {
            'fields': (
                'final_settlement_amount',
                ('settlement_paid', 'settlement_date'),
            ),
            'classes': ['tab'],
        }),
        ('Remarks', {
            'fields': ('remarks',),
            'classes': ['tab'],
        }),
    )


# ==================== PERFORMANCE APPRAISAL ADMIN ====================

@admin.register(PerformanceAppraisal)
class PerformanceAppraisalAdmin(ModelAdmin):
    list_display = ('employee', 'appraisal_date', 'overall_rating', 'total_score', 'recommend_increment', 'recommend_promotion')
    list_filter = (('overall_rating', ChoicesDropdownFilter), 'recommend_increment', 'recommend_promotion', ('appraisal_date', RangeDateFilter))
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ['employee']
    
    fieldsets = (
        ('Appraisal Details', {
            'fields': (
                'employee',
                ('appraisal_period_start', 'appraisal_period_end'),
                'appraisal_date',
            ),
            'classes': ['tab'],
        }),
        ('Ratings', {
            'fields': (
                'overall_rating',
                ('quality_of_work', 'productivity'),
                ('attendance', 'teamwork'),
                'communication',
                'total_score',
            ),
            'classes': ['tab'],
        }),
        ('Comments', {
            'fields': (
                'strengths',
                'areas_for_improvement',
                'goals_for_next_period',
            ),
            'classes': ['tab'],
        }),
        ('Recommendations', {
            'fields': (
                'appraised_by',
                ('recommend_increment', 'recommend_promotion'),
                'remarks',
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('total_score',)


# ==================== TRAINING ADMIN ====================

@admin.register(Training)
class TrainingAdmin(ModelAdmin):
    list_display = ('title', 'training_type', 'start_date', 'end_date', 'duration_hours', 'display_status')
    list_filter = (('training_type', ChoicesDropdownFilter), ('status', ChoicesDropdownFilter), ('start_date', RangeDateFilter))
    search_fields = ('title', 'trainer_name')
    filter_horizontal = ('employees',)
    
    fieldsets = (
        ('Training Details', {
            'fields': (
                ('title', 'training_type'),
                'employees',
                'description',
            ),
            'classes': ['tab'],
        }),
        ('Schedule', {
            'fields': (
                ('start_date', 'end_date'),
                'duration_hours',
                'venue',
            ),
            'classes': ['tab'],
        }),
        ('Trainer', {
            'fields': (
                ('trainer_name', 'trainer_organization'),
            ),
            'classes': ['tab'],
        }),
        ('Cost & Status', {
            'fields': (
                ('cost_per_person', 'status'),
                'remarks',
            ),
            'classes': ['tab'],
        }),
    )
    
    @display(description='Status', label={
        'scheduled': 'info',
        'ongoing': 'warning',
        'completed': 'success',
        'cancelled': 'danger',
    })
    def display_status(self, obj):
        return obj.status


