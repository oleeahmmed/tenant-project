# ==================== zktest/utils/__init__.py ====================
"""
Utility functions package
Organized by functionality
"""

# Import from attendance_utils
from .attendance_utils import (
    get_work_day_range,
    calculate_work_hours,
    calculate_daily_amount,
    generate_attendance_from_logs,
)

# Import from pyzk_utils
from .pyzk_utils import (
    ZKDeviceConnection,
    import_users_from_device,
    import_attendance_from_device,
    execute_device_command,
)

# Import from api_utils
from .api_utils import (
    get_date_range,
    success_response,
    error_response,
    auto_create_employee_from_device_user,
)

__all__ = [
    # Attendance utilities
    'get_work_day_range',
    'calculate_work_hours',
    'calculate_daily_amount',
    'generate_attendance_from_logs',
    
    # PyZK utilities
    'ZKDeviceConnection',
    'import_users_from_device',
    'import_attendance_from_device',
    'execute_device_command',
    
    # API utilities
    'get_date_range',
    'success_response',
    'error_response',
    'auto_create_employee_from_device_user',
]
