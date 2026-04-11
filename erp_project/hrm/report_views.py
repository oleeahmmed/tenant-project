# ==================== hrm/report_views.py ====================
"""
HRM Report Views - Admin Report Views
"""

from django.contrib import admin
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta, datetime, time
from decimal import Decimal
from collections import defaultdict

from hrm.models import AttendanceLog, Employee, EmployeeSalary


def is_employee_weekend(employee, date):
    """
    Check if given date is a weekend day for the employee
    
    Args:
        employee: Employee object
        date: Date to check
    
    Returns:
        bool: True if date is weekend for employee
    """
    if employee:
        return employee.is_weekend(date)
    # Default: friday, saturday, sunday
    day_name = date.strftime('%A').lower()
    return day_name in ['friday', 'saturday', 'sunday']


def get_work_day_range(date):
    """
    Get work day range: 6:00 AM to next day 4:00 AM
    
    Args:
        date: The work date
    
    Returns:
        tuple: (start_datetime, end_datetime)
    """
    start_datetime = datetime.combine(date, time(4, 30, 0))
    next_day = date + timedelta(days=1)
    end_datetime = datetime.combine(next_day, time(4, 0, 0))
    return start_datetime, end_datetime


def calculate_work_hours_from_punches(punches, break_time_minutes=0):
    """
    Calculate work hours from punch times
    
    Logic:
    1. Pair consecutive punches (IN-OUT pairs)
    2. Calculate paired time (sum of all pairs)
    3. Deduct break time
    4. Unpaired punches get 30 min penalty each
    5. Work Hours = (Paired Time - Break Time - Unpaired Penalty) / 60
    
    Args:
        punches: List of punch datetime objects
        break_time_minutes: Break time to deduct (default 60)
    
    Returns:
        dict with calculation details
    """
    if not punches or len(punches) == 0:
        return {
            'work_hours': Decimal('0.00'),
            'total_punches': 0,
            'paired_punches': 0,
            'unpaired_punches': 0,
            'paired_time_minutes': 0,
            'break_time_minutes': 0,
            'unpaired_penalty_minutes': 0,
            'first_punch': None,
            'last_punch': None,
            'punch_pairs': [],
            'unpaired_punch_times': [],
            'break_periods': [],
        }
    
    sorted_punches = sorted(punches)
    total_punches = len(sorted_punches)
    first_punch = sorted_punches[0]
    last_punch = sorted_punches[-1]
    
    # Pair consecutive punches
    punch_pairs = []
    unpaired_punch_times = []
    paired_time_minutes = 0
    
    i = 0
    while i < len(sorted_punches):
        if i + 1 < len(sorted_punches):
            # Pair this punch with next one
            pair_start = sorted_punches[i]
            pair_end = sorted_punches[i + 1]
            duration = (pair_end - pair_start).total_seconds() / 60
            punch_pairs.append((pair_start, pair_end, int(duration)))
            paired_time_minutes += duration
            i += 2  # Skip both punches
        else:
            # Unpaired punch
            unpaired_punch_times.append(sorted_punches[i])
            i += 1
    
    # Calculate unpaired penalty (30 min per unpaired punch)
    unpaired_penalty_minutes = len(unpaired_punch_times) * 30
    
    # Calculate work minutes
    work_minutes = paired_time_minutes - break_time_minutes - unpaired_penalty_minutes
    work_minutes = max(0, work_minutes)  # Can't be negative
    
    # Convert to hours
    work_hours = Decimal(str(work_minutes / 60)).quantize(Decimal('0.01'))
    
    # Calculate break periods (gaps between pairs)
    break_periods = []
    for i in range(len(punch_pairs) - 1):
        break_start = punch_pairs[i][1]  # End of current pair
        break_end = punch_pairs[i + 1][0]  # Start of next pair
        break_duration = (break_end - break_start).total_seconds() / 60
        if break_duration > 0:
            break_periods.append((break_start, break_end, int(break_duration)))
    
    return {
        'work_hours': work_hours,
        'total_punches': total_punches,
        'paired_punches': len(punch_pairs) * 2,
        'unpaired_punches': len(unpaired_punch_times),
        'paired_time_minutes': int(paired_time_minutes),
        'break_time_minutes': break_time_minutes,
        'unpaired_penalty_minutes': unpaired_penalty_minutes,
        'first_punch': first_punch,
        'last_punch': last_punch,
        'punch_pairs': punch_pairs,
        'unpaired_punch_times': unpaired_punch_times,
        'break_periods': break_periods,
    }


def generate_attendance_from_logs(user_id, date, attendance_logs, per_hour_rate, break_time_minutes=0, employee=None):
    """
    Generate attendance record from attendance logs for a specific date
    
    Args:
        user_id: Employee user_id
        date: Work date
        attendance_logs: QuerySet of AttendanceLog
        per_hour_rate: Employee's per hour rate
        break_time_minutes: Break time in minutes
        employee: Employee object (for weekend check and allowance)
    
    Returns:
        dict: Attendance data or None if no valid attendance
    """
    # Check if this is a weekend day for the employee
    is_weekend_day = employee and is_employee_weekend(employee, date)
    
    # Check if employee has weekend allowance enabled
    has_weekend_allowance = employee and employee.weekend_allowance
    
    # Get work day range
    start_datetime, end_datetime = get_work_day_range(date)
    
    # Make timezone aware if needed
    if timezone.is_naive(start_datetime):
        start_datetime = timezone.make_aware(start_datetime)
    if timezone.is_naive(end_datetime):
        end_datetime = timezone.make_aware(end_datetime)
    
    # Filter logs within work day range
    valid_logs = attendance_logs.filter(
        punch_time__gte=start_datetime,
        punch_time__lt=end_datetime
    ).order_by('punch_time')
    
    if not valid_logs.exists():
        return None
    
    # Extract punch times
    punches = [log.punch_time for log in valid_logs]
    
    # Calculate work hours
    calc_result = calculate_work_hours_from_punches(punches, break_time_minutes)
    
    # If weekend work and employee has allowance, ADD fixed 15 hours (not replace)
    weekend_bonus_hours = Decimal('15.00') if (is_weekend_day and has_weekend_allowance and calc_result['work_hours'] > 0) else Decimal('0.00')
    total_work_hours_for_pay = calc_result['work_hours'] + weekend_bonus_hours
    
    # Calculate daily amount
    daily_amount = (total_work_hours_for_pay * per_hour_rate).quantize(Decimal('0.01'))
    
    # Determine status
    status = 'present' if calc_result['work_hours'] > 0 else 'absent'
    
    return {
        'user_id': user_id,
        'date': date,
        'status': status,
        'is_weekend_work': is_weekend_day and has_weekend_allowance and calc_result['work_hours'] > 0,  # Mark if worked on weekend
        'weekend_bonus_hours': weekend_bonus_hours,  # 15 hours bonus if worked on weekend
        'check_in_time': calc_result['first_punch'],
        'check_out_time': calc_result['last_punch'],
        'work_hours': calc_result['work_hours'],  # Actual work hours from punches
        'total_work_hours': total_work_hours_for_pay,  # Actual + weekend bonus
        'total_punches': calc_result['total_punches'],
        'paired_punches': calc_result['paired_punches'],
        'unpaired_punches': calc_result['unpaired_punches'],
        'paired_time_minutes': calc_result['paired_time_minutes'],
        'break_time_minutes': calc_result['break_time_minutes'],
        'unpaired_penalty_minutes': calc_result['unpaired_penalty_minutes'],
        'daily_amount': daily_amount,
        'per_hour_rate': per_hour_rate,
        'punch_pairs': calc_result['punch_pairs'],
        'unpaired_punch_times': calc_result['unpaired_punch_times'],
        'break_periods': calc_result['break_periods'],
    }



class AttendanceLogReportView(View):
    """Attendance Log Report View - Raw punch data from ZKTeco devices"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from hrm.forms import AttendanceLogReportForm
        
        form = AttendanceLogReportForm(data=request.GET or None)
        
        # Default queryset
        logs = AttendanceLog.objects.all().order_by('-punch_time')
        
        # Apply filters if form is valid
        if form.is_valid():
            from_date = form.cleaned_data.get('from_date')
            to_date = form.cleaned_data.get('to_date')
            employee = form.cleaned_data.get('employee')
            device_sn = form.cleaned_data.get('device_sn')
            is_processed = form.cleaned_data.get('is_processed')
            
            if from_date:
                logs = logs.filter(punch_time__date__gte=from_date)
            if to_date:
                logs = logs.filter(punch_time__date__lte=to_date)
            if employee:
                logs = logs.filter(user_id=employee.user_id)
            if device_sn:
                logs = logs.filter(device__serial_number__icontains=device_sn)
            if is_processed != '':
                logs = logs.filter(is_synced=(is_processed == 'true'))
        
        # Calculate statistics
        total_logs = logs.count()
        processed_logs = logs.filter(is_synced=True).count()
        unprocessed_logs = logs.filter(is_synced=False).count()
        unique_employees = logs.values('user_id').distinct().count()
        unique_devices = logs.values('device').distinct().count()
        
        # Get logs by punch type
        punch_type_breakdown = {}
        for punch_val in logs.values_list('punch_type', flat=True).distinct():
            if punch_val is not None:
                punch_type_breakdown[dict(AttendanceLog.PUNCH_TYPES).get(punch_val, 'Unknown')] = logs.filter(punch_type=punch_val).count()
        
        # Get logs by verify type
        verify_type_breakdown = {}
        for verify_val in logs.values_list('verify_type', flat=True).distinct():
            if verify_val is not None:
                verify_type_breakdown[dict(AttendanceLog.VERIFY_TYPES).get(verify_val, 'Unknown')] = logs.filter(verify_type=verify_val).count()
        
        # Processing rate
        processing_rate = 0
        if total_logs > 0:
            processing_rate = round((processed_logs / total_logs) * 100, 2)
        
        # Get employee lookup dictionary for display
        log_list = logs[:200]  # Limit to 200 records
        user_ids = [log.user_id for log in log_list if log.user_id]
        employees_dict = {}
        if user_ids:
            employees = Employee.objects.filter(user_id__in=user_ids)
            employees_dict = {emp.user_id: emp for emp in employees}
        
        # Attach employee objects to logs for template
        for log in log_list:
            log.employee_obj = employees_dict.get(log.user_id)
        
        context = {
            **admin.site.each_context(request),
            'title': 'Attendance Log Report',
            'subtitle': 'Raw punch data from ZKTeco devices',
            'form': form,
            'logs': log_list,
            'total_logs': total_logs,
            'processed_logs': processed_logs,
            'unprocessed_logs': unprocessed_logs,
            'unique_employees': unique_employees,
            'unique_devices': unique_devices,
            'punch_type_breakdown': punch_type_breakdown,
            'verify_type_breakdown': verify_type_breakdown,
            'processing_rate': processing_rate,
        }
        
        return render(request, 'admin/hrm/attendance_log_report.html', context)


class DailyAttendanceReportView(View):
    """Daily Attendance Report - Generated from AttendanceLog with specific rules"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        from hrm.forms import DailyAttendanceReportForm
        
        form = DailyAttendanceReportForm(data=request.GET or None)
        
        attendance_records = []
        total_present = 0
        total_absent = 0
        total_work_hours = Decimal('0.00')
        total_amount = Decimal('0.00')
        
        if form.is_valid():
            from_date = form.cleaned_data.get('from_date')
            to_date = form.cleaned_data.get('to_date')
            employee = form.cleaned_data.get('employee')
            break_time = form.cleaned_data.get('break_time_minutes', 0)
            
            if from_date and to_date:
                # Get employees to process
                employees = Employee.objects.filter(is_active=True).order_by('employee_id')
                if employee:
                    employees = employees.filter(user_id=employee.user_id)
                
                # Process each employee for each date
                for emp in employees:
                    # Get employee salary info from EmployeeSalary model
                    try:
                        salary_info = EmployeeSalary.objects.get(user_id=emp)
                        per_hour_rate = salary_info.per_hour_rate if salary_info.per_hour_rate else Decimal('0.00')
                    except EmployeeSalary.DoesNotExist:
                        per_hour_rate = Decimal('0.00')
                    
                    # Get all logs for this employee
                    emp_logs = AttendanceLog.objects.filter(user_id=emp.user_id).order_by('punch_time')
                    
                    # Process each date in range
                    current_date = from_date
                    while current_date <= to_date:
                        # Get work day range for this date
                        start_datetime, end_datetime = get_work_day_range(current_date)
                        
                        # Make timezone aware if needed
                        if timezone.is_naive(start_datetime):
                            start_datetime = timezone.make_aware(start_datetime)
                        if timezone.is_naive(end_datetime):
                            end_datetime = timezone.make_aware(end_datetime)
                        
                        # Get punch logs for this work day
                        day_logs = emp_logs.filter(
                            punch_time__gte=start_datetime,
                            punch_time__lt=end_datetime
                        ).order_by('punch_time')
                        
                        # Generate attendance for this date
                        attendance_data = generate_attendance_from_logs(
                            user_id=emp.user_id,
                            date=current_date,
                            attendance_logs=emp_logs,
                            per_hour_rate=per_hour_rate,
                            break_time_minutes=break_time,
                            employee=emp  # Pass employee for weekend check
                        )
                        
                        # Always add record, even if absent
                        if attendance_data:
                            # Add employee object and punch logs for display
                            attendance_data['employee'] = emp
                            attendance_data['punch_logs'] = list(day_logs)
                            
                            # Check if it's a weekend day with no work (unpaid weekend)
                            is_weekend = is_employee_weekend(emp, current_date)
                            if is_weekend and attendance_data['status'] == 'absent':
                                # No work on weekend day = "Weekend" status
                                attendance_data['status'] = 'weekend'
                            
                            attendance_records.append(attendance_data)
                            
                            # Update statistics
                            if attendance_data['status'] == 'present':
                                total_present += 1
                                total_work_hours += attendance_data['work_hours']
                                total_amount += attendance_data['daily_amount']
                            else:
                                total_absent += 1
                        else:
                            # No punches at all - check if it's weekend
                            is_weekend = is_employee_weekend(emp, current_date)
                            status = 'weekend' if is_weekend else 'absent'
                            
                            if status == 'absent':
                                total_absent += 1
                            
                            attendance_records.append({
                                'employee': emp,
                                'user_id': emp.user_id,
                                'date': current_date,
                                'status': status,
                                'is_weekend_work': False,
                                'check_in_time': None,
                                'check_out_time': None,
                                'work_hours': Decimal('0.00'),
                                'total_punches': 0,
                                'paired_punches': 0,
                                'unpaired_punches': 0,
                                'paired_time_minutes': 0,
                                'break_time_minutes': 0,
                                'unpaired_penalty_minutes': 0,
                                'daily_amount': Decimal('0.00'),
                                'per_hour_rate': per_hour_rate,
                                'punch_logs': [],
                                'punch_pairs': [],
                                'unpaired_punch_times': [],
                                'break_periods': [],
                            })
                        
                        current_date += timedelta(days=1)
        
        # Sort by date and employee
        attendance_records.sort(key=lambda x: (x['date'], x['employee'].employee_id))
        
        # Generate employee summary
        employee_summary = {}
        for record in attendance_records:
            emp_id = record['employee'].user_id
            if emp_id not in employee_summary:
                employee_summary[emp_id] = {
                    'employee': record['employee'],
                    'per_hour_rate': record['per_hour_rate'],
                    'total_days': 0,
                    'present_days': 0,
                    'absent_days': 0,
                    'weekend_days': 0,  # Count of unpaid weekend days (no punch)
                    'weekend_work_days': 0,  # Count of weekend days with work
                    'weekend_hours': Decimal('0.00'),  # Total weekend bonus hours
                    'work_hours': Decimal('0.00'),  # Actual work hours from punches
                    'total_work_hours': Decimal('0.00'),  # work_hours + weekend_hours
                    'total_amount': Decimal('0.00'),
                }
            
            employee_summary[emp_id]['total_days'] += 1
            
            if record['status'] == 'present':
                employee_summary[emp_id]['present_days'] += 1
                # Add actual work hours and weekend bonus if applicable
                employee_summary[emp_id]['work_hours'] += record['work_hours']
                employee_summary[emp_id]['total_work_hours'] += record['total_work_hours']
                employee_summary[emp_id]['total_amount'] += record['daily_amount']
                # Track if they worked on weekend
                if record.get('is_weekend_work'):
                    employee_summary[emp_id]['weekend_work_days'] += 1
                    employee_summary[emp_id]['weekend_hours'] += record.get('weekend_bonus_hours', Decimal('0.00'))
            elif record['status'] == 'weekend':
                employee_summary[emp_id]['weekend_days'] += 1
                # Weekend day without punch = 15 hours bonus
                employee_summary[emp_id]['weekend_hours'] += Decimal('15.00')
                employee_summary[emp_id]['total_work_hours'] += Decimal('15.00')
                employee_summary[emp_id]['total_amount'] += (Decimal('15.00') * record['per_hour_rate']).quantize(Decimal('0.01'))
            else:  # absent
                employee_summary[emp_id]['absent_days'] += 1
        
        # IMPORTANT: If employee has ANY absent day, remove ALL weekend benefits
        # (They don't get any weekend allowance if they were absent even once)
        for emp_id, summary in employee_summary.items():
            if summary['absent_days'] > 0:
                # Remove all weekend benefits
                summary['weekend_days'] = 0
                summary['weekend_work_days'] = 0
                summary['weekend_hours'] = Decimal('0.00')
                # Recalculate total work hours and amount (only actual work, no weekend bonus)
                summary['total_work_hours'] = summary['work_hours']
                summary['total_amount'] = (summary['work_hours'] * summary['per_hour_rate']).quantize(Decimal('0.01'))
        
        # Calculate attendance percentage and format hours for each employee
        for emp_id, summary in employee_summary.items():
            # Calculate based on actual working days (excluding weekends)
            working_days = summary['total_days'] - summary['weekend_days']
            if working_days > 0:
                summary['attendance_percentage'] = round((summary['present_days'] / working_days) * 100, 1)
            else:
                summary['attendance_percentage'] = 0
            
            # Convert total work hours to hours:minutes format
            total_minutes = int(summary['total_work_hours'] * 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            summary['work_hours_formatted'] = f"{hours}h {minutes}m"
        
        # Convert to list and sort by employee ID
        employee_summary_list = sorted(employee_summary.values(), key=lambda x: x['employee'].employee_id)
        
        # Format total work hours for grand total
        total_minutes = int(total_work_hours * 60)
        total_hours_part = total_minutes // 60
        total_minutes_part = total_minutes % 60
        total_work_hours_formatted = f"{total_hours_part}h {total_minutes_part}m"
        
        context = {
            **admin.site.each_context(request),
            'title': 'Daily Attendance Report',
            'subtitle': 'Generated from AttendanceLog with work day rules (6 AM - 4 AM)',
            'form': form,
            'attendance_records': attendance_records[:500],  # Limit to 500 records
            'employee_summary': employee_summary_list,
            'total_records': len(attendance_records),
            'total_present': total_present,
            'total_absent': total_absent,
            'total_work_hours': round(total_work_hours, 2),
            'total_work_hours_formatted': total_work_hours_formatted,
            'total_amount': round(total_amount, 2),
        }
        
        return render(request, 'admin/hrm/daily_attendance_report.html', context)
