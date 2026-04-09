from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import (
    AttendanceLocation,
    AttendanceRecord,
    Department,
    Employee,
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
    ZKDevice,
)

WEEKDAY_CHOICES = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
]


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "code", "description", "parent"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "code": forms.TextInput(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "description": forms.Textarea(
                attrs={"rows": 2, "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "parent": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
        }


class JobTitleForm(forms.ModelForm):
    class Meta:
        model = JobTitle
        fields = ["name", "department", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "department": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "description": forms.Textarea(
                attrs={"rows": 2, "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
        }


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "employee_code",
            "full_name",
            "zk_user_id",
            "work_location_mode",
            "email",
            "phone",
            "department",
            "job_title",
            "default_shift",
            "reports_to",
            "user",
            "hire_date",
            "termination_date",
            "status",
            "notes",
        ]
        widgets = {
            "employee_code": forms.TextInput(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "zk_user_id": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring",
                    "placeholder": "Same as on ZKTeco device",
                }
            ),
            "work_location_mode": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "full_name": forms.TextInput(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "department": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "job_title": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "default_shift": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "reports_to": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "user": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "hire_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "termination_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "status": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "notes": forms.Textarea(
                attrs={"rows": 3, "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["department"].queryset = Department.objects.filter(tenant=tenant)
            self.fields["job_title"].queryset = JobTitle.objects.filter(tenant=tenant)
            self.fields["default_shift"].queryset = Shift.objects.filter(tenant=tenant, is_active=True).order_by(
                "code"
            )
            rq = Employee.objects.filter(tenant=tenant)
            if self.instance.pk:
                rq = rq.exclude(pk=self.instance.pk)
            self.fields["reports_to"].queryset = rq
            from auth_tenants.models import User

            # Workspace members + current selection (so validation passes if User.tenant was unset)
            uq = User.objects.filter(tenant=tenant)
            if self.instance.pk and self.instance.user_id:
                uq = User.objects.filter(Q(tenant=tenant) | Q(pk=self.instance.user_id)).distinct()
            self.fields["user"].queryset = uq.order_by("email")
        else:
            self.fields["default_shift"].queryset = Shift.objects.none()
        self.fields["user"].required = False
        self.fields["user"].empty_label = "— No linked account —"
        self.fields["default_shift"].required = False
        self.fields["default_shift"].empty_label = "— None (use weekly / date rules only) —"


class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        fields = ["name", "is_paid", "default_days_per_year", "requires_approval"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "is_paid": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
            "default_days_per_year": forms.NumberInput(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "requires_approval": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
        }


class EmployeeSelfLeaveForm(forms.ModelForm):
    """Employee applies for leave; `employee` is set in the view."""

    class Meta:
        model = LeaveRequest
        fields = ["leave_type", "start_date", "end_date", "reason"]
        widgets = {
            "leave_type": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "reason": forms.Textarea(
                attrs={"rows": 3, "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["leave_type"].queryset = LeaveType.objects.filter(tenant=tenant)


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["employee", "leave_type", "start_date", "end_date", "reason"]
        widgets = {
            "employee": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "leave_type": forms.Select(
                attrs={"class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
            "reason": forms.Textarea(
                attrs={"rows": 3, "class": "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"}
            ),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["employee"].queryset = Employee.objects.filter(tenant=tenant)
            self.fields["leave_type"].queryset = LeaveType.objects.filter(tenant=tenant)


_ctrl = "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"


class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ["name", "start_date", "end_date", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "description": forms.Textarea(attrs={"rows": 2, "class": _ctrl}),
        }


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ["title", "body", "is_pinned", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": _ctrl}),
            "body": forms.Textarea(attrs={"rows": 6, "class": _ctrl}),
            "is_pinned": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
        }


class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ["employee", "date", "check_in", "check_out", "status", "notes"]
        widgets = {
            "employee": forms.Select(attrs={"class": _ctrl}),
            "date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "check_in": forms.TimeInput(attrs={"type": "time", "class": _ctrl}),
            "check_out": forms.TimeInput(attrs={"type": "time", "class": _ctrl}),
            "status": forms.Select(attrs={"class": _ctrl}),
            "notes": forms.Textarea(attrs={"rows": 2, "class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["employee"].queryset = Employee.objects.filter(tenant=tenant)


class AttendanceBulkForm(forms.Form):
    """Bulk attendance (no employee — IDs come from POST employee_ids)."""

    date = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date", "class": _ctrl},
        ),
    )
    check_in = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={"type": "time", "class": _ctrl}),
    )
    check_out = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={"type": "time", "class": _ctrl}),
    )
    status = forms.ChoiceField(
        choices=AttendanceRecord.Status.choices,
        widget=forms.Select(attrs={"class": _ctrl}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "class": _ctrl}),
    )


class OvertimeBulkForm(forms.Form):
    work_date = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date", "class": _ctrl},
        ),
    )
    hours = forms.DecimalField(
        min_value=0.01,
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": _ctrl, "step": "0.25", "min": "0.25"}),
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": _ctrl}),
    )


class RosterBulkForm(forms.Form):
    """Apply shift rules to many employees (IDs from POST employee_ids)."""

    RULE_DEFAULT = "default"
    RULE_WEEKDAY = "weekday"
    RULE_RANGE = "range"
    RULE_EXCEPTION = "exception"

    rule_type = forms.ChoiceField(
        choices=[
            (RULE_DEFAULT, "Set default shift (fallback)"),
            (RULE_WEEKDAY, "Weekly pattern — one weekday for all selected"),
            (RULE_RANGE, "Date range — same period for all selected"),
            (RULE_EXCEPTION, "One-day override — same date for all selected"),
        ],
        widget=forms.Select(
            attrs={
                "class": _ctrl,
                "id": "id_roster_rule_type",
            }
        ),
    )
    shift = forms.ModelChoiceField(
        queryset=Shift.objects.none(),
        required=False,
        empty_label="— Clear default / not set —",
        widget=forms.Select(attrs={"class": _ctrl}),
    )
    weekday = forms.ChoiceField(
        choices=[("", "—")] + [(str(i), lab) for i, lab in WEEKDAY_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": _ctrl, "id": "id_roster_weekday"}),
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": _ctrl}),
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": _ctrl}),
    )
    exception_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": _ctrl}),
    )
    note = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": _ctrl, "placeholder": "Optional note (range / override)"}),
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["shift"].queryset = Shift.objects.filter(tenant=tenant, is_active=True).order_by("code")
        else:
            self.fields["shift"].queryset = Shift.objects.none()

    def clean(self):
        cleaned = super().clean()
        rt = cleaned.get("rule_type")
        sh = cleaned.get("shift")
        wd_raw = cleaned.get("weekday")
        sd = cleaned.get("start_date")
        ed = cleaned.get("end_date")
        ex = cleaned.get("exception_date")

        if rt == self.RULE_DEFAULT:
            return cleaned

        if sh is None:
            raise ValidationError({"shift": "Shift is required for this rule type."})

        if rt == self.RULE_WEEKDAY:
            if not wd_raw:
                raise ValidationError({"weekday": "Select a weekday."})
            cleaned["weekday_int"] = int(wd_raw)

        if rt == self.RULE_RANGE:
            if not sd or not ed:
                raise ValidationError("Start and end dates are required for a date range.")
            if ed < sd:
                raise ValidationError({"end_date": "End date must be on or after start date."})

        if rt == self.RULE_EXCEPTION:
            if not ex:
                raise ValidationError({"exception_date": "Select the override date."})

        return cleaned


class OvertimeRequestForm(forms.ModelForm):
    class Meta:
        model = OvertimeRequest
        fields = ["employee", "work_date", "hours", "reason"]
        widgets = {
            "employee": forms.Select(attrs={"class": _ctrl}),
            "work_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "hours": forms.NumberInput(attrs={"class": _ctrl, "step": "0.25", "min": "0.25"}),
            "reason": forms.Textarea(attrs={"rows": 3, "class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["employee"].queryset = Employee.objects.filter(tenant=tenant)


class ZKDeviceForm(forms.ModelForm):
    class Meta:
        model = ZKDevice
        fields = [
            "serial_number",
            "device_name",
            "device_type",
            "connection_type",
            "ip_address",
            "port",
            "mac_address",
            "is_active",
            "tcp_timeout",
            "tcp_password",
            "push_interval",
            "heartbeat_interval",
            "timezone_offset",
        ]
        widgets = {
            "serial_number": forms.TextInput(attrs={"class": _ctrl}),
            "device_name": forms.TextInput(attrs={"class": _ctrl}),
            "device_type": forms.Select(attrs={"class": _ctrl}),
            "connection_type": forms.Select(attrs={"class": _ctrl}),
            "ip_address": forms.TextInput(attrs={"class": _ctrl}),
            "port": forms.NumberInput(attrs={"class": _ctrl}),
            "mac_address": forms.TextInput(attrs={"class": _ctrl}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
            "tcp_timeout": forms.NumberInput(attrs={"class": _ctrl}),
            "tcp_password": forms.TextInput(attrs={"class": _ctrl, "placeholder": "Numeric comm key, or empty"}),
            "push_interval": forms.NumberInput(attrs={"class": _ctrl}),
            "heartbeat_interval": forms.NumberInput(attrs={"class": _ctrl}),
            "timezone_offset": forms.NumberInput(attrs={"class": _ctrl}),
        }


class AttendanceLocationForm(forms.ModelForm):
    class Meta:
        model = AttendanceLocation
        fields = [
            "name",
            "address",
            "latitude",
            "longitude",
            "radius_m",
            "location_kind",
            "window_start",
            "window_end",
            "weekdays",
            "exclude_holidays",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "address": forms.Textarea(attrs={"rows": 2, "class": _ctrl}),
            "latitude": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "longitude": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "radius_m": forms.NumberInput(attrs={"class": _ctrl, "min": "1"}),
            "location_kind": forms.Select(attrs={"class": _ctrl}),
            "window_start": forms.TimeInput(attrs={"type": "time", "class": _ctrl}),
            "window_end": forms.TimeInput(attrs={"type": "time", "class": _ctrl}),
            "weekdays": forms.TextInput(
                attrs={
                    "class": _ctrl,
                    "placeholder": "0,1,2,3,4 = Mon–Fri",
                }
            ),
            "exclude_holidays": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
        }


class LocationAttendancePolicyForm(forms.ModelForm):
    class Meta:
        model = LocationAttendancePolicy
        fields = [
            "checkin_mode",
            "max_accuracy_meters",
            "early_checkin_minutes",
            "late_checkin_minutes",
            "record_invalid_attempts",
            "reject_api_when_invalid",
            "allow_remote_clock_without_gps",
        ]
        widgets = {
            "checkin_mode": forms.Select(attrs={"class": _ctrl}),
            "max_accuracy_meters": forms.NumberInput(attrs={"class": _ctrl, "step": "any"}),
            "early_checkin_minutes": forms.NumberInput(attrs={"class": _ctrl, "min": "0"}),
            "late_checkin_minutes": forms.NumberInput(attrs={"class": _ctrl, "min": "0"}),
            "record_invalid_attempts": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
            "reject_api_when_invalid": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
            "allow_remote_clock_without_gps": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
        }


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = [
            "name",
            "code",
            "start_time",
            "end_time",
            "break_minutes",
            "is_night_shift",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": _ctrl}),
            "code": forms.TextInput(attrs={"class": _ctrl, "placeholder": "e.g. MORN"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": _ctrl}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": _ctrl}),
            "break_minutes": forms.NumberInput(attrs={"class": _ctrl, "min": "0"}),
            "is_night_shift": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-border"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["is_active"].initial = True


class EmployeeShiftWeekdayForm(forms.ModelForm):
    class Meta:
        model = EmployeeShiftWeekday
        fields = ["employee", "weekday", "shift"]
        widgets = {
            "employee": forms.Select(attrs={"class": _ctrl}),
            "weekday": forms.Select(attrs={"class": _ctrl}),
            "shift": forms.Select(attrs={"class": _ctrl}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["weekday"].choices = WEEKDAY_CHOICES
        if tenant:
            self.fields["employee"].queryset = Employee.objects.filter(tenant=tenant).order_by(
                "full_name"
            )
            self.fields["shift"].queryset = Shift.objects.filter(tenant=tenant, is_active=True).order_by(
                "code"
            )


class EmployeeShiftDateRangeForm(forms.ModelForm):
    class Meta:
        model = EmployeeShiftDateRange
        fields = ["employee", "start_date", "end_date", "shift", "note"]
        widgets = {
            "employee": forms.Select(attrs={"class": _ctrl}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "shift": forms.Select(attrs={"class": _ctrl}),
            "note": forms.TextInput(attrs={"class": _ctrl, "placeholder": "Optional"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["employee"].queryset = Employee.objects.filter(tenant=tenant).order_by(
                "full_name"
            )
            self.fields["shift"].queryset = Shift.objects.filter(tenant=tenant, is_active=True).order_by(
                "code"
            )


class EmployeeShiftExceptionForm(forms.ModelForm):
    class Meta:
        model = EmployeeShiftException
        fields = ["employee", "date", "shift", "note"]
        widgets = {
            "employee": forms.Select(attrs={"class": _ctrl}),
            "date": forms.DateInput(attrs={"type": "date", "class": _ctrl}),
            "shift": forms.Select(attrs={"class": _ctrl}),
            "note": forms.TextInput(attrs={"class": _ctrl, "placeholder": "Optional"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["employee"].queryset = Employee.objects.filter(tenant=tenant).order_by(
                "full_name"
            )
            self.fields["shift"].queryset = Shift.objects.filter(tenant=tenant, is_active=True).order_by(
                "code"
            )
