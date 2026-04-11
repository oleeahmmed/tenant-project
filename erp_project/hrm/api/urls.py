from django.urls import path
from . import api_views
from . import pyzk_views

app_name = 'hrm_api'

urlpatterns = [
    # ==========================================================================
    # ADMS Protocol Endpoints (Device Communication) - PUSH BASED
    # ==========================================================================
    
    # Main ADMS endpoints
    path('iclock/cdata', api_views.ADMSHandlerView.as_view(), name='adms_cdata'),
    path('iclock/getrequest', api_views.ADMSHandlerView.as_view(), name='adms_getrequest'),
    path('iclock/devicecmd', api_views.DeviceCommandAckView.as_view(), name='adms_devicecmd'),
    
    # Alternative paths (some devices use these)
    path('cdata', api_views.ADMSHandlerView.as_view(), name='adms_cdata_alt'),
    path('getrequest', api_views.ADMSHandlerView.as_view(), name='adms_getrequest_alt'),
    path('devicecmd', api_views.DeviceCommandAckView.as_view(), name='adms_devicecmd_alt'),
    
    # Legacy ZKTeco paths
    path('iclockpush/cdata', api_views.ADMSHandlerView.as_view(), name='adms_push_cdata'),
    path('iclockpush/getrequest', api_views.ADMSHandlerView.as_view(), name='adms_push_getrequest'),
    
    # ==========================================================================
    # REST API Endpoints - ADMS Management
    # ==========================================================================
    
    # Health & Dashboard
    path('api/health/', api_views.health_check, name='health_check'),
    path('api/dashboard/', api_views.dashboard_stats, name='dashboard_stats'),
    
    # Devices
    path('api/devices/', api_views.DeviceListView.as_view(), name='device_list'),
    path('api/devices/<int:pk>/', api_views.DeviceDetailView.as_view(), name='device_detail'),
    path('api/devices/<int:device_id>/commands/', api_views.DeviceCommandView.as_view(), name='device_commands'),
    path('api/devices/<int:device_id>/users/', api_views.DeviceUsersView.as_view(), name='device_users'),
    # TCP sync removed - use PyZK views instead (see below)
    
    # Bulk Operations
    path('api/commands/bulk/', api_views.BulkCommandView.as_view(), name='bulk_commands'),
    
    # Attendance
    path('api/attendance/', api_views.AttendanceListView.as_view(), name='attendance_list'),
    path('api/attendance/report/', api_views.AttendanceReportView.as_view(), name='attendance_report'),
    
    # Operation Logs
    path('api/operations/', api_views.OperationLogView.as_view(), name='operation_logs'),
    
    # ==========================================================================
    # PyZK (TCP) API Endpoints - PULL BASED for Old Devices
    # Only 4 Essential APIs
    # ==========================================================================
    
    # PyZK User Operations
    path('api/pyzk/devices/<int:device_id>/fetch-users/', pyzk_views.PyZKFetchUsersView.as_view(), name='pyzk_fetch_users'),
    path('api/pyzk/devices/<int:device_id>/import-users/', pyzk_views.PyZKImportUsersView.as_view(), name='pyzk_import_users'),
    
    # PyZK Attendance Operations
    path('api/pyzk/devices/<int:device_id>/fetch-attendance/', pyzk_views.PyZKFetchAttendanceView.as_view(), name='pyzk_fetch_attendance'),
    path('api/pyzk/devices/<int:device_id>/import-attendance/', pyzk_views.PyZKImportAttendanceView.as_view(), name='pyzk_import_attendance'),
    
    # ==========================================================================
    # Mobile Attendance API
    # ==========================================================================
    
    # Mobile attendance endpoints
    path('api/mobile/attendance/', api_views.MobileAttendanceView.as_view(), name='mobile_attendance'),
    path('api/mobile/attendance/history/', api_views.mobile_attendance_history, name='mobile_attendance_history'),
    path('api/mobile/attendance/today/', api_views.mobile_attendance_today, name='mobile_attendance_today'),
]
