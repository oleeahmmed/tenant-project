"""
HRM Forms - Report Filter Forms
Updated with shadcn-style input classes
"""

from django import forms
from hrm.models import Employee
from datetime import date, timedelta


class AttendanceLogReportForm(forms.Form):
    """Attendance Log Report Filter Form"""
    
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'input',
        }),
        label='From Date',
        initial=lambda: date.today() - timedelta(days=7)
    )
    
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'input',
        }),
        label='To Date',
        initial=date.today
    )
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True).order_by('employee_id'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'input',
        }),
        label='Employee',
        empty_label='All Employees'
    )
    
    device_sn = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Device Serial Number',
        }),
        label='Device SN'
    )
    
    is_processed = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('true', 'Processed'),
            ('false', 'Unprocessed'),
        ],
        widget=forms.Select(attrs={
            'class': 'input',
        }),
        label='Processing Status',
        initial=''
    )


class DailyAttendanceReportForm(forms.Form):
    """Daily Attendance Report Filter Form"""
    
    from_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'input',
        }),
        label='From Date',
        initial=lambda: date.today() - timedelta(days=7)
    )
    
    to_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'input',
        }),
        label='To Date',
        initial=date.today
    )
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True).order_by('employee_id'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'input',
        }),
        label='Employee',
        empty_label='All Employees'
    )
    
    break_time_minutes = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'input',
            'min': '0',
            'max': '480',
            'step': '15',
        }),
        label='Break Time (minutes)',
        help_text='Default break time to deduct from work hours'
    )


