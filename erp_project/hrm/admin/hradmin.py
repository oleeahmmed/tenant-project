from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django import forms

from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display, action
from unfold.contrib.filters.admin import (
    RangeDateFilter,
    RangeDateTimeFilter,
    ChoicesDropdownFilter,
    RelatedDropdownFilter,
)

from hrm.models import (
    Department, Designation, Shift, Employee,
    EmployeePersonalInfo, EmployeeEducation, EmployeeSalary,
    EmployeeSkill, Attendance, LeaveType, LeaveBalance,
    LeaveApplication, Holiday, Overtime, Notice,
    Location, UserLocation, Roster, RosterAssignment, RosterDay
)


# ==================== INLINE CLASSES ====================

class EmployeePersonalInfoInline(TabularInline):
    model = EmployeePersonalInfo
    extra = 0
    fields = ('date_of_birth', 'gender', 'blood_group', 'marital_status', 'city')
    readonly_fields = ()
    show_change_link = True
    tab = True


class EmployeeSalaryInline(TabularInline):
    model = EmployeeSalary
    extra = 0
    fields = ('base_salary', 'per_hour_rate', 'expected_working_hours', 'overtime_rate')
    readonly_fields = ()
    show_change_link = True
    tab = True


class EmployeeEducationInline(TabularInline):
    model = EmployeeEducation
    extra = 0
    fields = ('education_level', 'degree_title', 'institution', 'passing_year', 'result')
    show_change_link = True
    tab = True


class EmployeeSkillInline(TabularInline):
    model = EmployeeSkill
    extra = 0
    fields = ('skill_name', 'skill_level', 'years_of_experience')
    show_change_link = True
    tab = True


class LeaveBalanceInline(TabularInline):
    model = LeaveBalance
    extra = 0
    fields = ('year', 'entitled_days', 'used_days', 'carried_forward_days')
    readonly_fields = ()
    show_change_link = True
    tab = True


class RosterAssignmentInline(TabularInline):
    model = RosterAssignment
    extra = 0
    fields = ('user_id',)
    show_change_link = True
    tab = True


# ==================== DEPARTMENT ADMIN ====================

@admin.register(Department)
class DepartmentAdmin(ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at')
    list_filter = ('is_active', ('created_at', RangeDateTimeFilter))
    search_fields = ('name', 'code', 'description')
    list_editable = ('is_active',)
    ordering = ('name',)
    list_per_page = 25
    
    fieldsets = (
        ('Department Information', {
            'fields': (
                ('code', 'name'),
                ('description',),
                ('is_active',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== DESIGNATION ADMIN ====================

@admin.register(Designation)
class DesignationAdmin(ModelAdmin):
    list_display = ('code', 'name', 'level', 'is_active', 'created_at')
    list_filter = ('is_active', 'level', ('created_at', RangeDateTimeFilter))
    search_fields = ('name', 'code', 'description')
    list_editable = ('is_active',)
    ordering = ('level', 'name')
    list_per_page = 25
    
    fieldsets = (
        ('Designation Information', {
            'fields': (
                ('code', 'name'),
                ('level',),
                ('description',),
                ('is_active',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== SHIFT ADMIN ====================

@admin.register(Shift)
class ShiftAdmin(ModelAdmin):
    list_display = ('code', 'name', 'start_time', 'end_time', 'break_time', 'grace_time', 'is_night_shift', 'is_active')
    list_filter = ('is_active', 'is_night_shift', ('created_at', RangeDateTimeFilter))
    search_fields = ('name', 'code')
    list_editable = ('is_active',)
    ordering = ('start_time',)
    list_per_page = 25
    
    fieldsets = (
        ('Shift Information', {
            'fields': (
                ('code', 'name'),
                ('start_time', 'end_time'),
                ('break_time', 'grace_time'),
                ('is_night_shift', 'is_active'),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== EMPLOYEE FORM ====================

class EmployeeForm(forms.ModelForm):
    """Custom form for Employee with weekend days as checkboxes"""
    
    WEEKEND_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    weekend_days = forms.MultipleChoiceField(
        choices=WEEKEND_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select days that are weekend for this employee"
    )
    
    class Meta:
        model = Employee
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Split comma-separated string into list for initial value
        if self.instance and self.instance.weekend_days:
            weekend_list = [d.strip().lower() for d in self.instance.weekend_days.split(',')]
            self.fields['weekend_days'].initial = weekend_list
    
    def clean_weekend_days(self):
        """Convert selected checkboxes back to comma-separated string"""
        days = self.cleaned_data.get('weekend_days', [])
        if days:
            return ','.join(days)
        return 'friday'  # Default


# ==================== EMPLOYEE ADMIN ====================

@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    form = EmployeeForm
    list_display = (
        'employee_id', 'user_id', 'get_full_name', 'display_portal_user',
        'department', 'designation', 'display_weekend_allowance',
        'display_device_enrollment', 'display_employment_status', 'is_active'
    )
    list_filter = (
        'is_active',
        ('employment_status', ChoicesDropdownFilter),
        ('joining_date', RangeDateFilter),
        ('created_at', RangeDateTimeFilter),
    )
    search_fields = ('user_id', 'employee_id', 'first_name', 'last_name', 'email', 'phone_number')
    list_editable = ('is_active',)
    ordering = ('employee_id',)
    list_per_page = 50
    
    # Autocomplete fields for better performance
    autocomplete_fields = ['portal_user', 'department', 'designation', 'shift']
    
    inlines = [EmployeePersonalInfoInline, EmployeeSalaryInline, EmployeeEducationInline, EmployeeSkillInline, LeaveBalanceInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                ('user_id', 'employee_id'),
                ('first_name', 'last_name'),
                ('email', 'phone_number'),
                ('portal_user',),
                ('weekend_allowance', 'is_active'),
                ('weekend_days',),
            ),
            'classes': ['tab'],
        }),
        ('Organizational Details', {
            'fields': (
                ('department', 'designation'),
                ('shift',),
            ),
            'classes': ['tab'],
        }),
        ('Employment Details', {
            'fields': (
                ('joining_date', 'employment_status'),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    @display(description='Portal User')
    def display_portal_user(self, obj):
        """Show if employee has portal access"""
        if obj.portal_user:
            return format_html('<span style="color: green;">✓ {}</span>', obj.portal_user.username)
        return format_html('<span style="color: gray;">{}</span>', '-')
    
    @display(description='Devices')
    def display_device_enrollment(self, obj):
        """Show number of devices employee is enrolled in"""
        count = obj.get_device_users().count()
        if count > 0:
            return format_html('<span style="color: green;">✓ {} device(s)</span>', count)
        return format_html('<span style="color: orange;">{}</span>', '⚠ Not enrolled')
    
    @display(description='Weekend', label={
        True: 'success',
        False: 'danger',
    })
    def display_weekend_allowance(self, obj):
        """Show if employee has weekend allowance"""
        if obj.weekend_allowance:
            return format_html('<span style="color: green;">{}</span>', '✓ 15 hrs')
        return format_html('<span style="color: red;">{}</span>', '✗ Disabled')
    
    @display(description='Status', label={
        'active': 'success',
        'probation': 'warning',
        'suspended': 'danger',
        'terminated': 'danger',
        'resigned': 'info',
    })
    def display_employment_status(self, obj):
        return obj.employment_status


# ==================== EMPLOYEE PERSONAL INFO ADMIN ====================

@admin.register(EmployeePersonalInfo)
class EmployeePersonalInfoAdmin(ModelAdmin):
    list_display = ('user_id', 'date_of_birth', 'gender', 'blood_group', 'marital_status', 'city')
    list_filter = (
        ('gender', ChoicesDropdownFilter),
        ('blood_group', ChoicesDropdownFilter),
        ('marital_status', ChoicesDropdownFilter),
    )
    search_fields = ('user_id__first_name', 'user_id__last_name', 'user_id__user_id', 'nid', 'passport_no', 'city')
    ordering = ('user_id',)
    list_per_page = 50
    
    # Autocomplete for better performance
    autocomplete_fields = ['user_id']
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                ('user_id',),
                ('date_of_birth', 'gender'),
                ('blood_group', 'marital_status'),
                ('nid', 'passport_no'),
            ),
            'classes': ['tab'],
        }),
        ('Emergency Contact', {
            'fields': (
                ('emergency_contact_name', 'emergency_contact_phone'),
                ('emergency_contact_relation',),
            ),
            'classes': ['tab'],
        }),
        ('Address', {
            'fields': (
                ('present_address',),
                ('permanent_address',),
                ('city',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== EMPLOYEE EDUCATION ADMIN ====================

@admin.register(EmployeeEducation)
class EmployeeEducationAdmin(ModelAdmin):
    list_display = ('user_id', 'education_level', 'degree_title', 'institution', 'passing_year', 'result')
    list_filter = (
        ('education_level', ChoicesDropdownFilter),
        'passing_year',
    )
    search_fields = ('user_id__first_name', 'user_id__last_name', 'degree_title', 'institution')
    ordering = ('-passing_year',)
    list_per_page = 50
    
    # Autocomplete for better performance
    autocomplete_fields = ['user_id']
    
    fieldsets = (
        ('Education Information', {
            'fields': (
                ('user_id',),
                ('education_level', 'degree_title'),
                ('institution',),
                ('passing_year', 'result'),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== EMPLOYEE SALARY ADMIN ====================

@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(ModelAdmin):
    list_display = (
        'user_id', 'base_salary', 'per_hour_rate', 
        'expected_working_hours', 'overtime_rate', 'payment_method', 'effective_from'
    )
    list_filter = (
        'payment_method',
        ('effective_from', RangeDateFilter),
    )
    search_fields = ('user_id__first_name', 'user_id__last_name', 'bank_name', 'bank_account_no')
    ordering = ('user_id',)
    list_per_page = 50
    
    # Autocomplete for better performance
    autocomplete_fields = ['user_id']
    
    fieldsets = (
        ('Salary Information', {
            'fields': (
                ('user_id',),
                ('base_salary', 'per_hour_rate'),
                ('expected_working_hours',),
                ('overtime_rate', 'overtime_grace_minutes'),
                ('effective_from',),
            ),
            'classes': ['tab'],
        }),
        ('Banking Details', {
            'fields': (
                ('bank_name', 'bank_account_no'),
                ('bank_branch', 'payment_method'),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== EMPLOYEE SKILL ADMIN ====================

@admin.register(EmployeeSkill)
class EmployeeSkillAdmin(ModelAdmin):
    list_display = ('user_id', 'skill_name', 'skill_level', 'years_of_experience')
    list_filter = (
        ('skill_level', ChoicesDropdownFilter),
        'years_of_experience',
    )
    search_fields = ('user_id__first_name', 'user_id__last_name', 'skill_name')
    ordering = ('user_id', 'skill_name')
    list_per_page = 50
    
    # Autocomplete for better performance
    autocomplete_fields = ['user_id']
    
    fieldsets = (
        ('Skill Information', {
            'fields': (
                ('user_id',),
                ('skill_name', 'skill_level'),
                ('years_of_experience',),
                ('description',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== ATTENDANCE ADMIN ====================

@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = (
        'user_id', 'date', 'display_status',
        'check_in_time', 'check_out_time', 'work_hours', 
        'overtime_hours', 'late_minutes'
    )
    list_filter = (
        ('status', ChoicesDropdownFilter),
        ('date', RangeDateFilter),
        'processed_from_logs',
    )
    search_fields = ('user_id__first_name', 'user_id__last_name', 'user_id__user_id')
    ordering = ('-date', 'user_id')
    date_hierarchy = 'date'
    list_per_page = 50
    
    # Autocomplete for better performance
    autocomplete_fields = ['user_id']
    
    fieldsets = (
        ('Attendance Information', {
            'fields': (
                ('user_id', 'date'),
                ('status'),
                ('check_in_time', 'check_out_time'),
            ),
            'classes': ['tab'],
        }),
        ('Work Details', {
            'fields': (
                ('work_hours', 'overtime_hours'),
                ('late_minutes', 'early_out_minutes'),
                ('remarks',),
            ),
            'classes': ['tab'],
        }),
        ('Processing Info', {
            'fields': (
                ('processed_from_logs', 'last_processed_at'),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    @display(description='Status', label={
        'present': 'success',
        'absent': 'danger',
        'half_day': 'warning',
        'leave': 'info',
        'holiday': 'primary',
        'weekend': 'secondary',
    })
    def display_status(self, obj):
        return obj.status


# ==================== LEAVE TYPE ADMIN ====================

@admin.register(LeaveType)
class LeaveTypeAdmin(ModelAdmin):
    list_display = ('code', 'name', 'max_days', 'paid', 'carry_forward', 'requires_approval', 'is_active')
    list_filter = ('is_active', 'paid', 'carry_forward', 'requires_approval')
    search_fields = ('name', 'code', 'description')
    list_editable = ('is_active',)
    ordering = ('name',)
    list_per_page = 25
    
    fieldsets = (
        ('Leave Type Information', {
            'fields': (
                ('code', 'name'),
                ('max_days',),
                ('paid', 'requires_approval'),
                ('carry_forward', 'max_carry_forward_days'),
                ('description',),
                ('is_active',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== LEAVE BALANCE ADMIN ====================

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(ModelAdmin):
    list_display = (
        'user_id', 'year', 
        'entitled_days', 'used_days', 'carried_forward_days', 'remaining_days'
    )
    list_filter = (
        'year',
        
    )
    search_fields = ('user_id__first_name', 'user_id__last_name', 'user_id__user_id')
    ordering = ('user_id',)
    list_per_page = 50
    
    # Autocomplete for better performance
    autocomplete_fields = ['user_id']
    
    fieldsets = (
        ('Leave Balance Information', {
            'fields': (
                ('user_id'),
                ('year',),
                ('entitled_days', 'used_days'),
                ('carried_forward_days',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== LEAVE APPLICATION ADMIN ====================

@admin.register(LeaveApplication)
class LeaveApplicationAdmin(ModelAdmin):
    list_display = (
        'user_id', 'start_date', 'end_date', 
        'total_days', 'display_status', 'approved_by'
    )
    list_filter = (
        ('status', ChoicesDropdownFilter),
        
        ('start_date', RangeDateFilter),
    )
    search_fields = ('user_id__first_name', 'user_id__last_name', 'reason')
    ordering = ('-start_date',)
    date_hierarchy = 'start_date'
    list_per_page = 50
    
    # Autocomplete for better performance
    autocomplete_fields = ['user_id']
    
    fieldsets = (
        ('Leave Application Information', {
            'fields': (
                ('user_id'),
                ('start_date', 'end_date'),
                ('total_days',),
                ('reason',),
                ('status',),
            ),
            'classes': ['tab'],
        }),
        ('Approval Details', {
            'fields': (
                ('approved_by', 'approved_at'),
                ('rejection_reason',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    @display(description='Status', label={
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        'cancelled': 'secondary',
    })
    def display_status(self, obj):
        return obj.status


# ==================== HOLIDAY ADMIN ====================

@admin.register(Holiday)
class HolidayAdmin(ModelAdmin):
    list_display = ('name', 'date', 'is_optional', 'created_at')
    list_filter = ('is_optional', ('date', RangeDateFilter))
    search_fields = ('name', 'description')
    ordering = ('-date',)
    date_hierarchy = 'date'
    list_per_page = 50
    
    fieldsets = (
        ('Holiday Information', {
            'fields': (
                ('name', 'date'),
                ('is_optional',),
                ('description',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== OVERTIME ADMIN ====================

@admin.register(Overtime)
class OvertimeAdmin(ModelAdmin):
    list_display = (
        'user_id', 'date', 'overtime_hours', 'overtime_type',
        'hourly_rate', 'overtime_rate_multiplier', 'total_amount',
        'display_status', 'is_paid'
    )
    list_filter = (
        ('status', ChoicesDropdownFilter),
        ('overtime_type', ChoicesDropdownFilter),
        'is_paid',
        ('date', RangeDateFilter),
    )
    search_fields = ('user_id__first_name', 'user_id__last_name', 'user_id__user_id')
    ordering = ('-date', 'user_id')
    date_hierarchy = 'date'
    list_per_page = 50
    
    # Autocomplete for better performance
    autocomplete_fields = ['user_id']
    
    fieldsets = (
        ('Overtime Information', {
            'fields': (
                ('user_id', 'date'),
                ('overtime_type'),
                ('start_time', 'end_time'),
                ('overtime_hours',),
            ),
            'classes': ['tab'],
        }),
        ('Rate & Payment', {
            'fields': (
                ('hourly_rate', 'overtime_rate_multiplier'),
                ('total_amount',),
            ),
            'classes': ['tab'],
        }),
        ('Status & Approval', {
            'fields': (
                ('status',),
                ('approved_by', 'approved_at'),
                ('is_paid', 'paid_date'),
                ('remarks',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    @display(description='Status', label={
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        'paid': 'info',
    })
    def display_status(self, obj):
        return obj.status


# ==================== NOTICE ADMIN ====================

@admin.register(Notice)
class NoticeAdmin(ModelAdmin):
    list_display = ('title', 'display_priority', 'published_date', 'expiry_date', 'is_active')
    list_filter = (
        'is_active',
        ('priority', ChoicesDropdownFilter),
        ('published_date', RangeDateFilter),
    )
    search_fields = ('title', 'description')
    list_editable = ('is_active',)
    ordering = ('-published_date',)
    date_hierarchy = 'published_date'
    list_per_page = 50
    
    fieldsets = (
        ('Notice Information', {
            'fields': (
                ('title',),
                ('description',),
                ('priority',),
                ('published_date', 'expiry_date'),
                ('is_active',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    @display(description='Priority', label={
        'low': 'info',
        'medium': 'warning',
        'high': 'danger',
        'urgent': 'danger',
    })
    def display_priority(self, obj):
        return obj.priority


# ==================== LOCATION ADMIN ====================

@admin.register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ('name', 'address', 'latitude', 'longitude', 'radius', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address')
    list_editable = ('is_active',)
    ordering = ('name',)
    list_per_page = 25
    
    fieldsets = (
        ('Location Information', {
            'fields': (
                ('name',),
                ('address',),
                ('latitude', 'longitude'),
                ('radius',),
                ('is_active',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== USER LOCATION ADMIN ====================

@admin.register(UserLocation)
class UserLocationAdmin(ModelAdmin):
    list_display = ('user_id', 'is_primary', 'created_at')
    list_filter = (
        'is_primary',
        
    )
    search_fields = ('user_id__first_name', 'user_id__last_name', 'location__name')
    ordering = ('user_id',)
    list_per_page = 50
    
    fieldsets = (
        ('User Location Information', {
            'fields': (
                ('user_id'),
                ('is_primary',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== ROSTER ADMIN ====================

@admin.register(Roster)
class RosterAdmin(ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = (
        'is_active',
        ('start_date', RangeDateFilter),
    )
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    ordering = ('-start_date',)
    list_per_page = 50
    inlines = [RosterAssignmentInline]
    
    fieldsets = (
        ('Roster Information', {
            'fields': (
                ('name',),
                ('start_date', 'end_date'),
                ('description',),
                ('is_active',),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== ROSTER ASSIGNMENT ADMIN ====================

@admin.register(RosterAssignment)
class RosterAssignmentAdmin(ModelAdmin):
    list_display = ('roster', 'user_id', 'created_at')
    list_filter = (
        ('roster', RelatedDropdownFilter),
    )
    search_fields = ('user_id__first_name', 'user_id__last_name', 'roster__name')
    ordering = ('roster', 'user_id')
    list_per_page = 50
    
    # Autocomplete for better performance
    autocomplete_fields = ['user_id']
    
    fieldsets = (
        ('Roster Assignment Information', {
            'fields': (
                ('roster', 'user_id'),
                
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


# ==================== ROSTER DAY ADMIN ====================

@admin.register(RosterDay)
class RosterDayAdmin(ModelAdmin):
    list_display = ('user_id', 'date', 'is_off', 'created_at')
    list_filter = (
        'is_off',
        ('date', RangeDateFilter),
    )
    search_fields = ('user_id__first_name', 'user_id__last_name')
    ordering = ('date', 'user_id')
    date_hierarchy = 'date'
    list_per_page = 50
    
    fieldsets = (
        ('Roster Day Information', {
            'fields': (
                ('user_id', 'date'),
                ('is_off'),
            ),
            'classes': ['tab'],
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ['tab'],
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
