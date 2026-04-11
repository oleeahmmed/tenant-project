"""
HRM Guide Views
"""
from .employee_management_guide import EmployeeManagementGuideView
from .device_setup_guide import DeviceSetupGuideView
from .attendance_guide import AttendanceManagementGuideView
from .leave_management_guide import LeaveManagementGuideView
from .salary_payroll_guide import SalaryPayrollGuideView

__all__ = [
    'EmployeeManagementGuideView',
    'DeviceSetupGuideView',
    'AttendanceManagementGuideView',
    'LeaveManagementGuideView',
    'SalaryPayrollGuideView',
]
