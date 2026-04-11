from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Department(models.Model):
    """
    Organizational unit within a tenant (e.g. Engineering, HR, Sales).
    Optional parent supports a simple hierarchy.
    """

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="hrm_departments",
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "name")]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.parent_id:
            if self.pk and self.parent_id == self.pk:
                raise ValidationError({"parent": "Department cannot be parent of itself."})
            if self.tenant_id and self.parent.tenant_id != self.tenant_id:
                raise ValidationError({"parent": "Parent department must belong to same tenant."})


class JobTitle(models.Model):
    """Position / designation; optionally tied to a default department."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="hrm_job_titles",
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="job_titles",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "name")]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.department_id and self.tenant_id and self.department.tenant_id != self.tenant_id:
            raise ValidationError({"department": "Department must belong to same tenant."})


class Shift(models.Model):
    """
    Named work band (start/end) per tenant — used as default, weekly pattern, or date rules.
    """

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="hrm_shifts",
    )
    name = models.CharField(max_length=120)
    code = models.CharField(
        max_length=50,
        help_text="Short code unique within the workspace, e.g. MORN, NIGHT.",
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_minutes = models.PositiveSmallIntegerField(
        default=0,
        help_text="Unpaid break length inside the shift window.",
    )
    is_night_shift = models.BooleanField(
        default=False,
        help_text="Spans midnight or graveyard band — for reporting only.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        unique_together = [("tenant", "code")]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Employee(models.Model):
    """
    Workforce record for the tenant. Optional link to a login User (auth_tenants)
    when this person is also a system user.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PROBATION = "probation", "Probation"
        ON_LEAVE = "on_leave", "On leave"
        TERMINATED = "terminated", "Terminated"

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="hrm_employees",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hrm_employee_profile",
    )
    employee_code = models.CharField(max_length=50, help_text="Company employee / badge ID")
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
    )
    job_title = models.ForeignKey(
        JobTitle,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
    )
    default_shift = models.ForeignKey(
        Shift,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees_as_default",
        help_text="Used when no weekly rule, date range, or one-day override applies.",
    )
    reports_to = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="direct_reports",
    )
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    notes = models.TextField(blank=True)
    zk_user_id = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="ZKTeco / device user_id — must match machine punches for this tenant.",
    )
    class WorkLocationMode(models.TextChoices):
        OFFICE = "office", "Office-first (geofence required)"
        HYBRID = "hybrid", "Hybrid (office + home zones)"
        REMOTE = "remote", "Remote (policy allows clock without fence)"

    work_location_mode = models.CharField(
        max_length=20,
        choices=WorkLocationMode.choices,
        default=WorkLocationMode.OFFICE,
        help_text="Used with tenant GPS policy for mobile check-in.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]
        unique_together = [("tenant", "employee_code")]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "zk_user_id"],
                condition=models.Q(zk_user_id__gt=""),
                name="hrm_employee_unique_tenant_zk_user_id",
            ),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.employee_code})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.reports_to_id and self.pk and self.reports_to_id == self.pk:
            raise ValidationError({"reports_to": "An employee cannot report to themselves."})
        if self.reports_to_id and self.tenant_id and self.reports_to.tenant_id != self.tenant_id:
            raise ValidationError({"reports_to": "Reporting manager must belong to same tenant."})
        if self.user_id and self.tenant_id:
            uid_tid = getattr(self.user, "tenant_id", None)
            # If the login has a workspace set, it must match this employee's tenant.
            # If unset (None), allow linking — common for accounts resolved via employee/custom role only.
            if uid_tid is not None and uid_tid != self.tenant_id:
                raise ValidationError({"user": "Linked user must belong to the same tenant."})
            clash = Employee.objects.filter(user_id=self.user_id)
            if self.pk:
                clash = clash.exclude(pk=self.pk)
            if clash.exists():
                raise ValidationError(
                    {"user": "This login is already linked to another employee record."}
                )
        if self.default_shift_id and self.tenant_id and self.default_shift.tenant_id != self.tenant_id:
            raise ValidationError({"default_shift": "Default shift must belong to this workspace."})
        if self.department_id and self.tenant_id and self.department.tenant_id != self.tenant_id:
            raise ValidationError({"department": "Department must belong to this workspace."})
        if self.job_title_id and self.tenant_id and self.job_title.tenant_id != self.tenant_id:
            raise ValidationError({"job_title": "Job title must belong to this workspace."})


class LeaveType(models.Model):
    """Configurable leave categories (annual, sick, unpaid, etc.)."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="hrm_leave_types",
    )
    name = models.CharField(max_length=100)
    is_paid = models.BooleanField(default=True)
    default_days_per_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Optional cap for reporting; not enforced automatically.",
    )
    requires_approval = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "name")]

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    """Time-off request workflow."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="leave_requests",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_leave_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.full_name} — {self.leave_type.name} ({self.start_date})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date must be on or after start date."})
        if self.employee_id and self.leave_type_id:
            if self.employee.tenant_id != self.leave_type.tenant_id:
                raise ValidationError("Employee and leave type must belong to the same tenant.")
        if self.employee_id and self.start_date and self.end_date:
            overlap_qs = LeaveRequest.objects.filter(
                employee=self.employee,
                status__in=[LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED],
                start_date__lte=self.end_date,
                end_date__gte=self.start_date,
            )
            if self.pk:
                overlap_qs = overlap_qs.exclude(pk=self.pk)
            if overlap_qs.exists():
                raise ValidationError(
                    "This leave overlaps with an existing pending/approved request."
                )
        if (
            self.employee_id
            and self.leave_type_id
            and self.start_date
            and self.end_date
            and self.leave_type.default_days_per_year is not None
        ):
            year_start = self.start_date.replace(month=1, day=1)
            year_end = self.start_date.replace(month=12, day=31)
            used_days = 0
            yearly = LeaveRequest.objects.filter(
                employee=self.employee,
                leave_type=self.leave_type,
                status__in=[LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED],
                start_date__lte=year_end,
                end_date__gte=year_start,
            )
            if self.pk:
                yearly = yearly.exclude(pk=self.pk)
            for req in yearly:
                used_days += (req.end_date - req.start_date).days + 1
            requested_days = (self.end_date - self.start_date).days + 1
            if used_days + requested_days > int(self.leave_type.default_days_per_year):
                raise ValidationError(
                    f"Annual leave cap exceeded for {self.leave_type.name}."
                )


class Holiday(models.Model):
    """Company / public holidays visible in the tenant calendar."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="hrm_holidays",
    )
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_date", "name"]

    def __str__(self):
        return f"{self.name} ({self.start_date})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date must be on or after start date."})


class Notice(models.Model):
    """Internal announcements for the organization."""

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="hrm_notices",
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hrm_notices_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title


class AttendanceRecord(models.Model):
    """Daily attendance punch / status per employee."""

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        HALF_DAY = "half_day", "Half day"
        ON_LEAVE = "on_leave", "On leave"
        HOLIDAY = "holiday", "Holiday"

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "employee__full_name"]
        unique_together = [("employee", "date")]

    def __str__(self):
        return f"{self.employee.full_name} — {self.date}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.check_in and self.check_out and self.check_out < self.check_in:
            raise ValidationError({"check_out": "Check-out must be after check-in."})


class OvertimeRequest(models.Model):
    """Extra hours worked — approval workflow."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="overtime_requests",
    )
    work_date = models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_overtime_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.full_name} — {self.work_date} ({self.hours}h)"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        from decimal import Decimal

        if self.hours is not None and self.hours <= Decimal("0"):
            raise ValidationError({"hours": "Hours must be greater than zero."})


class EmployeeShiftWeekday(models.Model):
    """
    Fixed shift for a weekday (Python: Monday=0 … Sunday=6), per employee.
    """

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="shift_weekday_rules",
    )
    weekday = models.PositiveSmallIntegerField(
        help_text="0=Monday … 6=Sunday (same as date.weekday()).",
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name="weekday_assignments",
    )

    class Meta:
        ordering = ["employee_id", "weekday"]
        unique_together = [("employee", "weekday")]

    def __str__(self):
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        wn = names[self.weekday] if 0 <= self.weekday <= 6 else str(self.weekday)
        return f"{self.employee.full_name} · {wn} → {self.shift.code}"

    def clean(self):
        if self.shift_id and self.employee_id and self.shift.tenant_id != self.employee.tenant_id:
            raise ValidationError({"shift": "Shift must belong to the same workspace as the employee."})
        if self.weekday is not None and not (0 <= self.weekday <= 6):
            raise ValidationError({"weekday": "Weekday must be 0–6."})


class EmployeeShiftDateRange(models.Model):
    """Temporary shift for a calendar period (overrides weekday pattern, below one-day exception)."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="shift_date_ranges",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name="date_range_assignments",
    )
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-start_date", "employee_id"]

    def __str__(self):
        return f"{self.employee.full_name} {self.start_date}–{self.end_date} → {self.shift.code}"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date must be on or after start date."})
        if self.shift_id and self.employee_id and self.shift.tenant_id != self.employee.tenant_id:
            raise ValidationError({"shift": "Shift must belong to the same workspace as the employee."})
        if self.employee_id and self.start_date and self.end_date:
            overlap_qs = EmployeeShiftDateRange.objects.filter(
                employee=self.employee,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date,
            )
            if self.pk:
                overlap_qs = overlap_qs.exclude(pk=self.pk)
            if overlap_qs.exists():
                raise ValidationError(
                    "Shift date range overlaps with an existing rule for this employee."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class EmployeeShiftException(models.Model):
    """Single-date override (highest priority in resolution)."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="shift_exceptions",
    )
    date = models.DateField()
    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name="exception_assignments",
    )
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date", "employee_id"]
        unique_together = [("employee", "date")]

    def __str__(self):
        return f"{self.employee.full_name} {self.date} → {self.shift.code}"

    def clean(self):
        if self.shift_id and self.employee_id and self.shift.tenant_id != self.employee.tenant_id:
            raise ValidationError({"shift": "Shift must belong to the same workspace as the employee."})


# ── ZKTeco / PyZK (tenant-scoped) ─────────────────────────────────────────────


class ZKDevice(models.Model):
    """Biometric device — ADMS push and/or TCP (PyZK) pull."""

    class DeviceType(models.TextChoices):
        ATTENDANCE = "attendance", "Attendance device"
        ACCESS = "access", "Access control"
        MULTI = "multi", "Multi-function"

    class ConnectionType(models.TextChoices):
        ADMS = "adms", "ADMS (push)"
        TCP = "tcp", "TCP/IP (PyZK)"
        BOTH = "both", "ADMS + TCP"

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="hrm_zk_devices",
    )
    serial_number = models.CharField(max_length=50, unique=True, db_index=True)
    device_name = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.ATTENDANCE,
    )
    connection_type = models.CharField(
        max_length=20,
        choices=ConnectionType.choices,
        default=ConnectionType.ADMS,
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    port = models.IntegerField(default=4370)
    mac_address = models.CharField(max_length=20, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)
    platform = models.CharField(max_length=50, blank=True)
    push_version = models.CharField(max_length=20, blank=True)
    oem_vendor = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    user_count = models.IntegerField(default=0)
    fp_count = models.IntegerField(default=0)
    face_count = models.IntegerField(default=0)
    palm_count = models.IntegerField(default=0)
    transaction_count = models.IntegerField(default=0)
    push_interval = models.IntegerField(default=30)
    heartbeat_interval = models.IntegerField(default=60)
    timezone_offset = models.IntegerField(default=360)
    tcp_timeout = models.IntegerField(default=5)
    tcp_password = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_activity", "serial_number"]

    def __str__(self):
        return self.device_name or self.serial_number

    def update_activity(self):
        self.last_activity = timezone.now()
        self.is_online = True
        self.save(update_fields=["last_activity", "is_online", "updated_at"])

    def supports_adms(self):
        return self.connection_type in ("adms", "both")

    def supports_tcp(self):
        return self.connection_type in ("tcp", "both")


class DeviceUser(models.Model):
    """User enrolled on a ZKTeco device."""

    class Privilege(models.IntegerChoices):
        USER = 0, "User"
        ENROLLER = 2, "Enroller"
        ADMIN = 6, "Admin"
        SUPER = 14, "Super admin"

    device = models.ForeignKey(
        ZKDevice,
        on_delete=models.CASCADE,
        related_name="device_users",
    )
    user_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100, blank=True)
    privilege = models.SmallIntegerField(default=0)
    card_number = models.CharField(max_length=50, blank=True)
    password = models.CharField(max_length=20, blank=True)
    group = models.CharField(max_length=10, default="1")
    has_fingerprint = models.BooleanField(default=False)
    has_face = models.BooleanField(default=False)
    has_palm = models.BooleanField(default=False)
    fp_count = models.SmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["device", "user_id"]
        unique_together = [("device", "user_id")]

    def __str__(self):
        return self.name or self.user_id


class AttendanceLog(models.Model):
    """Raw punch rows from device (PyZK pull, ADMS push, mobile GPS, etc.)."""

    class PunchType(models.IntegerChoices):
        CHECK_IN = 0, "Check in"
        CHECK_OUT = 1, "Check out"
        BREAK_OUT = 2, "Break out"
        BREAK_IN = 3, "Break in"
        OT_IN = 4, "OT in"
        OT_OUT = 5, "OT out"
        PUNCH = 255, "Punch"

    class VerifyType(models.IntegerChoices):
        PASSWORD = 0, "Password"
        FINGERPRINT = 1, "Fingerprint"
        CARD = 2, "Card"
        CARD_FP = 4, "Card + fingerprint"
        CARD_PW = 6, "Card + password"
        CARD_FP_PW = 8, "Card + FP + password"
        FACE = 15, "Face"
        PALM = 20, "Palm"

    class Source(models.TextChoices):
        ADMS = "adms", "ADMS push"
        TCP = "tcp", "TCP (PyZK)"
        MOBILE = "mobile", "Mobile app"
        MANUAL = "manual", "Manual"

    class ValidationStatus(models.TextChoices):
        VALID = "valid", "Valid"
        DEVICE_SYNC = "device_sync", "Device import (no GPS rule)"
        OUT_OF_GEOFENCE = "out_of_geofence", "Outside geofence"
        LOW_ACCURACY = "low_accuracy", "GPS accuracy too poor"
        OUTSIDE_TIME = "outside_time_window", "Outside allowed time"
        HOLIDAY = "holiday_blocked", "Holiday (location excludes)"
        REMOTE_NO_GPS = "remote_no_gps", "Remote clock without GPS"
        PENDING_REVIEW = "pending_review", "Pending admin review"
        OVERRIDE_OK = "override_ok", "Override approved"

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="hrm_attendance_logs",
    )
    device = models.ForeignKey(
        ZKDevice,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="attendance_logs",
    )
    employee = models.ForeignKey(
        "Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="attendance_log_rows",
    )
    user_id = models.CharField(max_length=50, db_index=True)
    punch_time = models.DateTimeField(db_index=True)
    punch_type = models.SmallIntegerField(choices=PunchType.choices, default=PunchType.CHECK_IN)
    verify_type = models.SmallIntegerField(choices=VerifyType.choices, default=VerifyType.FINGERPRINT)
    work_code = models.CharField(max_length=20, blank=True)
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.ADMS,
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    location_accuracy = models.FloatField(null=True, blank=True)
    matched_location = models.ForeignKey(
        "AttendanceLocation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="matched_logs",
    )
    distance_to_fence_m = models.FloatField(
        null=True,
        blank=True,
        help_text="Distance to nearest allowed fence (meters), if computed.",
    )
    validation_status = models.CharField(
        max_length=30,
        choices=ValidationStatus.choices,
        default=ValidationStatus.DEVICE_SYNC,
    )
    requires_review = models.BooleanField(default=False)
    review_status = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_attendance_logs",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    mask_status = models.SmallIntegerField(default=0)
    raw_data = models.TextField(blank=True)
    is_synced = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-punch_time"]
        indexes = [
            models.Index(fields=["user_id", "punch_time"]),
            models.Index(fields=["tenant", "punch_time"]),
            models.Index(fields=["device", "created_at"]),
            models.Index(fields=["validation_status", "requires_review"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["device", "user_id", "punch_time"],
                condition=models.Q(device__isnull=False),
                name="hrm_attlog_unique_device_punch",
            ),
            models.UniqueConstraint(
                fields=["tenant", "user_id", "punch_time"],
                condition=models.Q(device__isnull=True),
                name="hrm_attlog_unique_tenant_mobile_punch",
            ),
        ]

    def __str__(self):
        return f"{self.user_id} @ {self.punch_time}"


class TCPSyncLog(models.Model):
    """History of PyZK pull operations."""

    class SyncType(models.TextChoices):
        USERS = "users", "Users"
        ATTENDANCE = "attendance", "Attendance"
        ALL = "all", "All"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    device = models.ForeignKey(
        ZKDevice,
        on_delete=models.CASCADE,
        related_name="tcp_sync_logs",
    )
    sync_type = models.CharField(max_length=20, choices=SyncType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    records_found = models.IntegerField(default=0)
    records_synced = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.device_id} {self.sync_type} {self.status}"


class LocationAttendancePolicy(models.Model):
    """Tenant-wide rules for GPS / geofence check-in."""

    class CheckinMode(models.TextChoices):
        ONSITE_ONLY = "onsite_only", "On-site only (must be inside a fence)"
        HYBRID = "hybrid", "Hybrid (office + home zones)"
        REMOTE_ALLOWED = "remote_allowed", "Remote allowed (no fence if employee is remote)"

    tenant = models.OneToOneField(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="hrm_location_policy",
    )
    checkin_mode = models.CharField(
        max_length=20,
        choices=CheckinMode.choices,
        default=CheckinMode.HYBRID,
    )
    max_accuracy_meters = models.FloatField(
        default=100.0,
        help_text="Reject GPS reads worse than this (meters); 0 = ignore accuracy.",
    )
    early_checkin_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Earliest check-in before location window opens.",
    )
    late_checkin_minutes = models.PositiveIntegerField(
        default=120,
        help_text="Latest check-in after location window ends.",
    )
    record_invalid_attempts = models.BooleanField(
        default=True,
        help_text="Store failed punches for audit / review.",
    )
    reject_api_when_invalid = models.BooleanField(
        default=False,
        help_text="If True, API returns error and does not save invalid punches.",
    )
    allow_remote_clock_without_gps = models.BooleanField(
        default=True,
        help_text="For remote employees: allow punch with no coordinates (logged as such).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Location policy — {self.tenant_id}"


class AttendanceLocation(models.Model):
    """Geofence for validating mobile / GPS punches."""

    class LocationKind(models.TextChoices):
        OFFICE = "office", "Office / branch"
        HOME = "home", "Home / remote zone"
        OTHER = "other", "Other site"

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="hrm_attendance_locations",
    )
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    radius_m = models.PositiveIntegerField(
        default=100,
        help_text="Allowed radius in meters.",
    )
    location_kind = models.CharField(
        max_length=20,
        choices=LocationKind.choices,
        default=LocationKind.OFFICE,
    )
    window_start = models.TimeField(
        null=True,
        blank=True,
        help_text="If set, punch must be within window (tenant timezone).",
    )
    window_end = models.TimeField(null=True, blank=True)
    weekdays = models.CharField(
        max_length=20,
        default="0,1,2,3,4",
        help_text="Comma-separated weekday indices: 0=Mon … 6=Sun.",
    )
    exclude_holidays = models.BooleanField(
        default=True,
        help_text="If True, punches blocked on tenant holiday calendar.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("tenant", "name")]

    def __str__(self):
        return self.name

    def weekday_set(self):
        try:
            return {int(x.strip()) for x in self.weekdays.split(",") if x.strip() != ""}
        except ValueError:
            return set()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.window_start and self.window_end and self.window_start == self.window_end:
            raise ValidationError({"window_end": "Window end must differ from window start."})
        try:
            values = [int(x.strip()) for x in str(self.weekdays).split(",") if x.strip() != ""]
        except ValueError:
            raise ValidationError({"weekdays": "Weekdays must be comma-separated integers 0-6."})
        bad = [v for v in values if v < 0 or v > 6]
        if bad:
            raise ValidationError({"weekdays": "Weekdays must be in range 0-6."})


class EmployeeAttendanceLocation(models.Model):
    """Which geofences apply to which employee (e.g. branch attendance)."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendance_locations",
    )
    location = models.ForeignKey(
        AttendanceLocation,
        on_delete=models.CASCADE,
        related_name="employee_links",
    )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("employee", "location")]

    def __str__(self):
        return f"{self.employee} — {self.location}"
