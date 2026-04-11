# ==================== zktest/utils/attendance_utils.py ====================
"""
Attendance calculation utilities
Used by report_views.py and mobile_views.py
"""

from datetime import datetime, timedelta, time
from decimal import Decimal
from django.utils import timezone


def get_work_day_range(date):
    """
    Get work day range: 6:00 AM to next day 4:00 AM
    
    Args:
        date: The work date
    
    Returns:
        tuple: (start_datetime, end_datetime)
    """
    # Work day starts at 6:00 AM
    start_datetime = datetime.combine(date, time(6, 0, 0))
    
    # Work day ends at 4:00 AM next day
    next_day = date + timedelta(days=1)
    end_datetime = datetime.combine(next_day, time(4, 0, 0))
    
    return start_datetime, end_datetime


def calculate_work_hours(punches, break_time_minutes=60, pair_threshold_minutes=30):
    """
    Calculate work hours for hourly-based employees
    
    CORRECT LOGIC:
    1. Total Work Time = Last Punch - First Punch
    2. Calculate breaks between ALL consecutive punches (excluding first and last)
    3. If gap ≤ 30 min = Actual break time (use the gap duration)
    4. If gap > 30 min = Employee forgot to punch, add only 30 min break
    5. Work Hours = Total Time - Total Breaks
    
    Args:
        punches: List of punch datetime objects (sorted)
        break_time_minutes: Not used, calculated automatically
        pair_threshold_minutes: Threshold to detect forgotten punches (default 30)
    
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
            'break_periods': []
        }
    
    # Sort punches
    sorted_punches = sorted(punches)
    total_punches = len(sorted_punches)
    first_punch = sorted_punches[0]
    last_punch = sorted_punches[-1]
    
    # Calculate total work duration (last - first)
    total_duration = last_punch - first_punch
    total_duration_minutes = int(total_duration.total_seconds() / 60)
    
    # Group consecutive punches within 30 min as break periods
    punch_pairs = []
    break_periods = []
    unpaired_punch_times = []
    total_break_minutes = 0
    
    i = 1  # Start from second punch (skip first)
    while i < len(sorted_punches) - 1:  # Stop before last punch
        # Start a potential break group
        break_start = sorted_punches[i]
        break_end = sorted_punches[i]
        
        # Look ahead to find all punches within 30 min of break_start
        j = i + 1
        while j < len(sorted_punches) - 1:  # Don't include last punch
            time_diff = sorted_punches[j] - break_start
            diff_minutes = int(time_diff.total_seconds() / 60)
            
            if diff_minutes <= pair_threshold_minutes:
                # This punch is part of the same break group
                break_end = sorted_punches[j]
                j += 1
            else:
                # Gap > 30 min, end this break group
                break
        
        # Calculate break duration
        break_duration = break_end - break_start
        break_minutes = int(break_duration.total_seconds() / 60)
        
        # Add this break period
        if break_minutes >= 0:
            punch_pairs.append((break_start, break_end, break_minutes))
            break_periods.append((break_start, break_end, break_minutes))
            total_break_minutes += break_minutes
        
        # Move to next ungrouped punch
        i = j if j > i else i + 1
    
    # Calculate work minutes
    work_minutes = total_duration_minutes - total_break_minutes
    
    # Ensure work_minutes is not negative
    if work_minutes < 0:
        work_minutes = 0
    
    # Convert to hours
    work_hours = Decimal(str(work_minutes / 60)).quantize(Decimal('0.01'))
    
    # Count paired punches
    paired_count = len(punch_pairs) * 2 if punch_pairs else 0
    
    return {
        'work_hours': work_hours,
        'total_punches': total_punches,
        'paired_punches': paired_count,
        'unpaired_punches': len(unpaired_punch_times),
        'paired_time_minutes': sum(duration for _, _, duration in punch_pairs),
        'break_time_minutes': total_break_minutes,
        'unpaired_penalty_minutes': len(unpaired_punch_times) * 30,
        'first_punch': first_punch,
        'last_punch': last_punch,
        'punch_pairs': punch_pairs,
        'unpaired_punch_times': unpaired_punch_times,
        'break_periods': break_periods
    }


def calculate_daily_amount(work_hours, per_hour_rate):
    """
    Calculate daily amount
    
    Args:
        work_hours: Decimal work hours
        per_hour_rate: Decimal per hour rate
    
    Returns:
        Decimal: daily amount
    """
    return (work_hours * per_hour_rate).quantize(Decimal('0.01'))


def generate_attendance_from_logs(user_id, date, attendance_logs, per_hour_rate, break_time_minutes=60):
    """
    Generate attendance record from attendance logs for a specific date
    
    Args:
        user_id: Employee user_id
        date: Work date
        attendance_logs: QuerySet of AttendanceLog for this employee and date range
        per_hour_rate: Employee's per hour rate
        break_time_minutes: Break time in minutes
    
    Returns:
        dict: Attendance data or None if no valid attendance
    """
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
    
    # Extract punch times - ensure they're timezone aware
    punches = []
    for log in valid_logs:
        punch_time = log.punch_time
        # Ensure timezone aware
        if timezone.is_naive(punch_time):
            punch_time = timezone.make_aware(punch_time)
        punches.append(punch_time)
    
    # Calculate work hours
    calc_result = calculate_work_hours(punches, break_time_minutes)
    
    # Calculate daily amount
    daily_amount = calculate_daily_amount(calc_result['work_hours'], per_hour_rate)
    
    # Determine status - present if work_hours > 0
    status = 'present' if calc_result['work_hours'] > 0 else 'absent'
    
    # Return data even if work_hours is 0 (to show punch details)
    return {
        'user_id': user_id,
        'date': date,
        'status': status,
        'check_in_time': calc_result['first_punch'],
        'check_out_time': calc_result['last_punch'],
        'work_hours': calc_result['work_hours'],
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
