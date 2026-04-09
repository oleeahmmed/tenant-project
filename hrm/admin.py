from django.contrib import admin

from .models import (
    AttendanceLocation,
    AttendanceLog,
    AttendanceRecord,
    Department,
    DeviceUser,
    Employee,
    EmployeeAttendanceLocation,
    EmployeeShiftDateRange,
    EmployeeShiftException,
    EmployeeShiftWeekday,
    Holiday,
    JobTitle,
    LeaveRequest,
    LeaveType,
    LocationAttendancePolicy,
    Notice,
    OvertimeRequest,
    Shift,
    TCPSyncLog,
    ZKDevice,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "code", "parent", "created_at")
    list_filter = ("tenant",)
    search_fields = ("name", "code")


@admin.register(JobTitle)
class JobTitleAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "department")
    list_filter = ("tenant",)
    search_fields = ("name",)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "start_time", "end_time", "is_active")
    list_filter = ("tenant", "is_active", "is_night_shift")
    search_fields = ("code", "name")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_code",
        "full_name",
        "tenant",
        "department",
        "job_title",
        "status",
        "hire_date",
    )
    list_filter = ("tenant", "status", "department")
    search_fields = ("employee_code", "full_name", "email", "zk_user_id")
    raw_id_fields = ("user", "reports_to")


@admin.register(EmployeeShiftWeekday)
class EmployeeShiftWeekdayAdmin(admin.ModelAdmin):
    list_display = ("employee", "weekday", "shift")
    list_filter = ("employee__tenant",)
    search_fields = ("employee__full_name", "employee__employee_code")


@admin.register(EmployeeShiftDateRange)
class EmployeeShiftDateRangeAdmin(admin.ModelAdmin):
    list_display = ("employee", "start_date", "end_date", "shift")
    list_filter = ("employee__tenant",)
    search_fields = ("employee__full_name", "note")


@admin.register(EmployeeShiftException)
class EmployeeShiftExceptionAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "shift")
    list_filter = ("employee__tenant",)
    search_fields = ("employee__full_name", "note")


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_paid", "requires_approval", "default_days_per_year")
    list_filter = ("tenant", "is_paid")


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "leave_type", "start_date", "end_date", "status", "created_at")
    list_filter = ("status", "leave_type__tenant")
    search_fields = ("employee__full_name", "employee__employee_code")
    raw_id_fields = ("reviewed_by",)


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "start_date", "end_date")
    list_filter = ("tenant",)
    search_fields = ("name",)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "tenant", "is_pinned", "is_active", "created_at")
    list_filter = ("tenant", "is_active", "is_pinned")
    search_fields = ("title", "body")
    raw_id_fields = ("created_by",)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "status", "check_in", "check_out")
    list_filter = ("status", "employee__tenant")
    search_fields = ("employee__full_name", "employee__employee_code")
    date_hierarchy = "date"


@admin.register(OvertimeRequest)
class OvertimeRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "work_date", "hours", "status", "created_at")
    list_filter = ("status", "employee__tenant")
    search_fields = ("employee__full_name", "employee__employee_code")
    raw_id_fields = ("reviewed_by",)


@admin.register(LocationAttendancePolicy)
class LocationAttendancePolicyAdmin(admin.ModelAdmin):
    list_display = ("tenant", "checkin_mode", "max_accuracy_meters", "record_invalid_attempts")
    list_filter = ("checkin_mode",)


@admin.register(ZKDevice)
class ZKDeviceAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "device_name", "tenant", "connection_type", "ip_address", "is_active", "is_online")
    list_filter = ("tenant", "connection_type", "is_active")
    search_fields = ("serial_number", "device_name", "ip_address")


@admin.register(DeviceUser)
class DeviceUserAdmin(admin.ModelAdmin):
    list_display = ("device", "user_id", "name", "is_active")
    list_filter = ("device__tenant",)
    search_fields = ("user_id", "name", "device__serial_number")


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ("punch_time", "user_id", "device", "source", "punch_type")
    list_filter = ("source", "device__tenant")
    search_fields = ("user_id", "device__serial_number")
    date_hierarchy = "punch_time"


@admin.register(TCPSyncLog)
class TCPSyncLogAdmin(admin.ModelAdmin):
    list_display = ("device", "sync_type", "status", "records_synced", "created_at")
    list_filter = ("status", "sync_type", "device__tenant")


@admin.register(AttendanceLocation)
class AttendanceLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "latitude", "longitude", "radius_m", "is_active")
    list_filter = ("tenant", "is_active")


@admin.register(EmployeeAttendanceLocation)
class EmployeeAttendanceLocationAdmin(admin.ModelAdmin):
    list_display = ("employee", "location", "is_primary")
    list_filter = ("location__tenant",)
