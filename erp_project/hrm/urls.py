# ==================== hrm/urls.py ====================
"""
URL configuration for HRM app - Report Views & Guides
"""
from django.urls import path, include
from hrm.report_views import (
    AttendanceLogReportView, 
    DailyAttendanceReportView,
)

# Guide views
from hrm.views.guides import (
    EmployeeManagementGuideView,
    DeviceSetupGuideView,
    AttendanceManagementGuideView,
    LeaveManagementGuideView,
    SalaryPayrollGuideView,
)

app_name = 'hrm'

urlpatterns = [
    # ==================== ADMIN REPORTS ====================
    path('reports/attendance-log/', AttendanceLogReportView.as_view(), name='attendance-log-report'),
    path('reports/daily-attendance/', DailyAttendanceReportView.as_view(), name='daily-attendance-report'),
    
    # ==================== GUIDE URLS ====================
    path('employee-management-guide/', EmployeeManagementGuideView.as_view(), name='employee-management-guide'),
    path('device-setup-guide/', DeviceSetupGuideView.as_view(), name='device-setup-guide'),
    path('attendance-management-guide/', AttendanceManagementGuideView.as_view(), name='attendance-management-guide'),
    path('leave-management-guide/', LeaveManagementGuideView.as_view(), name='leave-management-guide'),
    path('salary-payroll-guide/', SalaryPayrollGuideView.as_view(), name='salary-payroll-guide'),
    
    # Device API (ADMS & PyZK)
    path('device/', include('hrm.api.urls')),
]
