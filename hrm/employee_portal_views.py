"""Self-service HRM page: map check-in/out, leave apply, recent history."""

from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView, View

from .forms import EmployeeSelfLeaveForm
from .mixins import EmployeePortalMixin, HrmPageContextMixin, PostOnlyMixin
from .models import AttendanceLog, Employee, LeaveRequest, LeaveType
from .services.location_checkin import (
    get_or_create_location_policy,
    persist_mobile_attendance_log,
    process_mobile_checkin,
    sync_daily_record_from_log,
)


def _bar_pct(total: int, taken: int, due: int) -> tuple[float, float, float]:
    s = total + taken + due
    if s <= 0:
        return (33.33, 33.33, 33.34)
    return (
        round(100.0 * total / s, 2),
        round(100.0 * taken / s, 2),
        round(100.0 * due / s, 2),
    )


def _leave_summaries(employee: Employee, tenant) -> tuple[dict, list[dict]]:
    """Overall totals + per leave-type rows for dashboard bars."""
    types = list(LeaveType.objects.filter(tenant=tenant).order_by("name"))
    rows: list[dict] = []
    sum_total = 0
    sum_taken = 0
    for lt in types:
        cap = lt.default_days_per_year or 0
        approved = LeaveRequest.objects.filter(
            employee=employee,
            leave_type=lt,
            status=LeaveRequest.Status.APPROVED,
        )
        taken = 0
        for req in approved:
            taken += (req.end_date - req.start_date).days + 1
        due = max(0, cap - taken) if cap else 0
        p1, p2, p3 = _bar_pct(cap, taken, due)
        rows.append(
            {
                "name": lt.name,
                "total": cap,
                "taken": taken,
                "due": due,
                "has_cap": lt.default_days_per_year is not None,
                "pct_total": p1,
                "pct_taken": p2,
                "pct_due": p3,
            }
        )
        sum_total += cap
        sum_taken += taken
    due_all = max(0, sum_total - sum_taken)
    o1, o2, o3 = _bar_pct(sum_total, sum_taken, due_all)
    overall = {
        "total": sum_total,
        "taken": sum_taken,
        "due": due_all,
        "pct_total": o1,
        "pct_taken": o2,
        "pct_due": o3,
    }
    return overall, rows


class EmployeeDashboardView(EmployeePortalMixin, HrmPageContextMixin, TemplateView):
    template_name = "hrm/employee_dashboard.html"
    page_title = "My HRM"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        request = self.request
        user = request.user
        tenant = request.hrm_tenant
        policy = get_or_create_location_policy(tenant)

        emp = Employee.objects.filter(user_id=user.pk).first()
        portal_preview = emp is None or emp.tenant_id != tenant.id

        lat, lng = 23.8103, 90.4125
        if not portal_preview:
            link = (
                emp.attendance_locations.select_related("location")
                .filter(location__is_active=True)
                .first()
            )
            if link:
                lat = float(link.location.latitude)
                lng = float(link.location.longitude)

        if portal_preview:
            z1, z2, z3 = _bar_pct(0, 0, 0)
            overall = {
                "total": 0,
                "taken": 0,
                "due": 0,
                "pct_total": z1,
                "pct_taken": z2,
                "pct_due": z3,
            }
            leave_rows = []
            recent_logs = AttendanceLog.objects.none()
            recent_requests = LeaveRequest.objects.none()
            leave_form = None
        else:
            overall, leave_rows = _leave_summaries(emp, tenant)
            recent_logs = (
                AttendanceLog.objects.filter(employee=emp, tenant=tenant)
                .select_related("matched_location")
                .order_by("-punch_time")[:25]
            )
            recent_requests = LeaveRequest.objects.filter(employee=emp).order_by("-created_at")[:8]
            leave_form = EmployeeSelfLeaveForm(tenant=tenant)

        ctx.update(
            {
                "employee": emp,
                "portal_preview": portal_preview,
                "location_policy": policy,
                "map_default_lat": lat,
                "map_default_lng": lng,
                "leave_overall": overall,
                "leave_rows": leave_rows,
                "recent_logs": recent_logs,
                "recent_leave_requests": recent_requests,
                "leave_form": leave_form,
            }
        )
        return ctx


class EmployeeCheckinView(EmployeePortalMixin, PostOnlyMixin, View):
    def post(self, request, *args, **kwargs):
        tenant = request.hrm_tenant
        emp = Employee.objects.filter(user_id=request.user.pk).first()
        if tenant is None or emp is None or emp.tenant_id != tenant.id:
            messages.error(
                request,
                "Check-in needs your user linked to an Employee on this workspace (Employees → edit → User).",
            )
            return redirect("hrm:employee_home")

        try:
            lat = request.POST.get("latitude")
            lng = request.POST.get("longitude")
            acc = request.POST.get("accuracy")
            lat_f = float(lat) if lat not in (None, "") else None
            lng_f = float(lng) if lng not in (None, "") else None
            acc_f = float(acc) if acc not in (None, "") else None
        except (TypeError, ValueError):
            messages.error(request, "Invalid location data.")
            return redirect("hrm:employee_home")

        try:
            punch_type = int(request.POST.get("punch_type") or "0")
        except ValueError:
            punch_type = 0

        policy = get_or_create_location_policy(tenant)
        pt = timezone.now()
        result = process_mobile_checkin(
            tenant=tenant,
            employee=emp,
            latitude=lat_f,
            longitude=lng_f,
            accuracy=acc_f,
            punch_time=pt,
            punch_type=punch_type,
        )

        if not result.ok and policy.reject_api_when_invalid:
            messages.error(request, result.message)
            return redirect("hrm:employee_home")

        if result.ok or (result.log_defaults and policy.record_invalid_attempts):
            log = persist_mobile_attendance_log(dict(result.log_defaults))
            if result.ok:
                _sync_daily_record_from_log(emp, log)
                messages.success(request, result.message)
            else:
                messages.warning(
                    request,
                    f"{result.message} (Recorded for review.)",
                )
        else:
            messages.error(request, result.message)

        return redirect("hrm:employee_home")


class EmployeeLeaveSubmitView(EmployeePortalMixin, PostOnlyMixin, View):
    def post(self, request, *args, **kwargs):
        tenant = request.hrm_tenant
        emp = Employee.objects.filter(user_id=request.user.pk).first()
        if emp is None or tenant is None or emp.tenant_id != tenant.id:
            messages.error(
                request,
                "Leave requests need your user linked to an Employee on this workspace.",
            )
            return redirect("hrm:employee_home")
        form = EmployeeSelfLeaveForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.employee = emp
            if obj.leave_type.requires_approval:
                obj.status = LeaveRequest.Status.PENDING
            else:
                obj.status = LeaveRequest.Status.APPROVED
                obj.reviewed_by = request.user
                obj.reviewed_at = timezone.now()
            obj.save()
            if obj.status == LeaveRequest.Status.APPROVED:
                messages.success(request, "Leave submitted and auto-approved.")
            else:
                messages.success(request, "Leave request submitted.")
        else:
            for errs in form.errors.values():
                for e in errs:
                    messages.error(request, e)
        return redirect("hrm:employee_home")
