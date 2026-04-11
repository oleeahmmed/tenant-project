# ==================== zktest/utils/api_utils.py ====================
"""
API utilities
Used by api/pyzk_views.py and other API views
"""

import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_date_range(range_type):
    """
    Get date range based on type
    
    Args:
        range_type: 'today', '7days', '30days', 'month', or 'custom'
    
    Returns:
        tuple: (date_from, date_to)
    """
    today = timezone.now().date()
    
    if range_type == 'today':
        return today, today
    elif range_type == '7days':
        return today - timedelta(days=7), today
    elif range_type == '30days':
        return today - timedelta(days=30), today
    elif range_type == 'month':
        return today.replace(day=1), today
    else:
        return today, today


def success_response(message='Success', data=None, **kwargs):
    """
    Standard success response
    
    Args:
        message: Success message
        data: Response data
        **kwargs: Additional fields
    
    Returns:
        dict: Response dictionary
    """
    response = {
        'success': True,
        'message': message,
        'timestamp': timezone.now().isoformat()
    }
    if data is not None:
        response['data'] = data
    response.update(kwargs)
    return response


def error_response(message='Error', data=None, errors=None, **kwargs):
    """
    Standard error response
    
    Args:
        message: Error message
        data: Response data
        errors: Error details
        **kwargs: Additional fields
    
    Returns:
        dict: Response dictionary
    """
    response = {
        'success': False,
        'message': message,
        'timestamp': timezone.now().isoformat()
    }
    if data is not None:
        response['data'] = data
    if errors is not None:
        response['errors'] = errors
    response.update(kwargs)
    return response


def auto_create_employee_from_device_user(device_user):
    """
    Auto-create employee from device user
    
    Args:
        device_user: DeviceUser instance
    
    Returns:
        Employee instance or None
    """
    from hrm.models import Employee
    
    try:
        # Check if employee already exists
        if Employee.objects.filter(user_id=device_user.user_id).exists():
            return None
        
        # Split name
        names = device_user.name.split(' ', 1) if device_user.name else ['', '']
        
        # Create employee
        employee = Employee.objects.create(
            user_id=device_user.user_id,
            employee_id=device_user.user_id,
            first_name=names[0],
            last_name=names[1] if len(names) > 1 else '',
            is_active=device_user.is_active
        )
        
        logger.info(f"Auto-created employee for user_id: {device_user.user_id}")
        return employee
    except Exception as e:
        logger.error(f"Failed to create employee: {str(e)}")
        return None
