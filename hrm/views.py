from collections import defaultdict

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    AttendanceBulkForm,
    AttendanceRecordForm,
    DepartmentForm,
    EmployeeForm,
    HolidayForm,
    JobTitleForm,
    LeaveRequestForm,
    LeaveTypeForm,
    NoticeForm,
    OvertimeBulkForm,
    OvertimeRequestForm,
)
from .mixins import (
    HrmAdminMixin,
    HrmPageContextMixin,
    PostOnlyMixin,
    WorkspaceTenantDashboardMixin,
)
from .tenant_scope import SESSION_KEY_ACTIVE_TENANT
from .models import (
    AttendanceRecord,
    Department,
    Employee,
    Holiday,
    JobTitle,
    LeaveRequest,
    LeaveType,
    Notice,
    OvertimeRequest,
)


# ── Dashboard ─────────────────────────────────────────────────────────────────


class HrmDashboardView(WorkspaceTenantDashboardMixin, HrmPageContextMixin, TemplateView):
    template_name = "hrm/dashboard.html"
    page_title = "Human Resources"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        tenant = getattr(request, "hrm_tenant", None)
        if tenant is not None and not tenant.is_module_enabled("hrm"):
            messages.error(request, "HRM module is disabled for this tenant.")
            return redirect("dashboard")
        if (
            tenant is not None
            and getattr(request.user, "role", None) in ("staff", "tenant_admin")
            and not request.user.has_tenant_permission("hrm.view")
        ):
            messages.error(request, "You do not have permission for this HRM action.")
            return redirect("dashboard")
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = self.request.hrm_tenant
        if t is None:
            from auth_tenants.models import Tenant

            ctx["departments_n"] = 0
            ctx["job_titles_n"] = 0
            ctx["employees_n"] = 0
            ctx["pending_leaves_n"] = 0
            ctx["holidays_n"] = 0
            ctx["notices_n"] = 0
            ctx["pending_overtime_n"] = 0
            ctx["hrm_needs_tenant"] = True
            ctx["hrm_tenant_choices"] = Tenant.objects.filter(is_active=True).order_by("name")
            ctx["hrm_active_tenant_id"] = self.request.session.get(SESSION_KEY_ACTIVE_TENANT)
            return ctx
        ctx["hrm_needs_tenant"] = False
        ctx["departments_n"] = Department.objects.filter(tenant=t).count()
        ctx["job_titles_n"] = JobTitle.objects.filter(tenant=t).count()
        ctx["employees_n"] = Employee.objects.filter(tenant=t).count()
        ctx["pending_leaves_n"] = LeaveRequest.objects.filter(
            employee__tenant=t, status=LeaveRequest.Status.PENDING
        ).count()
        ctx["holidays_n"] = Holiday.objects.filter(tenant=t).count()
        ctx["notices_n"] = Notice.objects.filter(tenant=t, is_active=True).count()
        ctx["pending_overtime_n"] = OvertimeRequest.objects.filter(
            employee__tenant=t, status=OvertimeRequest.Status.PENDING
        ).count()
        return ctx


class SetActiveHrmTenantView(WorkspaceTenantDashboardMixin, View):
    """POST: super_admin sets session tenant when user.tenant is empty (multi-tenant)."""

    http_method_names = ["post"]

    def post(self, request):
        if request.user.role != "super_admin":
            return HttpResponseForbidden()
        from auth_tenants.models import Tenant

        raw = request.POST.get("tenant_id")
        if not raw or not str(raw).isdigit():
            messages.error(request, "Invalid tenant.")
            return redirect("hrm:hrm_dashboard")
        tenant = Tenant.objects.filter(pk=int(raw), is_active=True).first()
        if not tenant:
            messages.error(request, "That workspace was not found.")
            return redirect("hrm:hrm_dashboard")
        request.session[SESSION_KEY_ACTIVE_TENANT] = tenant.pk
        request.session.modified = True
        messages.success(request, f"Working as: {tenant.name}")
        nxt = request.POST.get("next") or ""
        if nxt.startswith("/"):
            return redirect(nxt)
        return redirect("hrm:hrm_dashboard")


# ── API (JSON, tenant-scoped) ─────────────────────────────────────────────────


class HrmEmployeeSearchAPIView(HrmAdminMixin, View):
    """Autocomplete: ?q= & optional ?department= (id or 'none')."""

    def get(self, request):
        tenant = request.hrm_tenant
        q = (request.GET.get("q") or "").strip()
        dept = request.GET.get("department")
        qs = (
            Employee.objects.filter(tenant=tenant)
            .exclude(status=Employee.Status.TERMINATED)
            .select_related("department")
        )
        if q:
            qs = qs.filter(Q(full_name__icontains=q) | Q(employee_code__icontains=q))
        if dept == "none":
            qs = qs.filter(department__isnull=True)
        elif dept and str(dept).isdigit():
            qs = qs.filter(department_id=int(dept))
        qs = qs.order_by("full_name")[:40]
        results = [
            {
                "id": e.pk,
                "label": f"{e.full_name} ({e.employee_code})",
                "department_id": e.department_id,
                "department_name": e.department.name if e.department else None,
            }
            for e in qs
        ]
        return JsonResponse({"results": results})


class HrmEmployeePickerAPIView(HrmAdminMixin, View):
    """Departments + employees for checkbox UI (excludes terminated)."""

    def get(self, request):
        tenant = request.hrm_tenant
        rows = list(
            Employee.objects.filter(tenant=tenant)
            .exclude(status=Employee.Status.TERMINATED)
            .values("id", "employee_code", "full_name", "department_id")
            .order_by("full_name")
        )
        by_dept = defaultdict(list)
        unassigned = []
        for row in rows:
            item = {
                "id": row["id"],
                "code": row["employee_code"],
                "name": row["full_name"],
            }
            did = row["department_id"]
            if did is None:
                unassigned.append(item)
            else:
                by_dept[did].append(item)

        departments = []
        for d in Department.objects.filter(tenant=tenant).order_by("name"):
            departments.append(
                {
                    "id": d.pk,
                    "name": d.name,
                    "employees": by_dept.get(d.pk, []),
                }
            )
        return JsonResponse({"departments": departments, "unassigned": unassigned})


# ── Departments ─────────────────────────────────────────────────────────────


class DepartmentListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = Department
    template_name = "hrm/department_list.html"
    context_object_name = "departments"
    page_title = "Departments"

    def get_queryset(self):
        return Department.objects.filter(tenant=self.request.hrm_tenant).select_related("parent")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = DepartmentForm()
        form.fields["parent"].queryset = Department.objects.filter(tenant=self.request.hrm_tenant)
        ctx["form"] = form
        return ctx


class DepartmentCreateView(HrmAdminMixin, PostOnlyMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    success_url = reverse_lazy("hrm:department_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault("data", self.request.POST)
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        try:
            self.object.save()
            messages.success(self.request, "Department created.")
        except Exception:
            messages.error(self.request, "Could not save department (duplicate name?).")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors in the form.")
        return redirect(self.success_url)


class DepartmentUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = "hrm/department_edit.html"
    context_object_name = "department"
    page_title = "Edit department"
    success_url = reverse_lazy("hrm:department_list")

    def get_queryset(self):
        return Department.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["parent"].queryset = Department.objects.filter(
            tenant=self.request.hrm_tenant
        ).exclude(pk=self.object.pk)
        return form

    def form_valid(self, form):
        messages.success(self.request, "Department updated.")
        return super().form_valid(form)


class DepartmentDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = Department
    success_url = reverse_lazy("hrm:department_list")

    def get_queryset(self):
        return Department.objects.filter(tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f"Department “{name}” removed.")
        return response


# ── Job titles ────────────────────────────────────────────────────────────────


class JobTitleListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = JobTitle
    template_name = "hrm/job_title_list.html"
    context_object_name = "job_titles"
    page_title = "Job titles"

    def get_queryset(self):
        return JobTitle.objects.filter(tenant=self.request.hrm_tenant).select_related("department")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = JobTitleForm()
        form.fields["department"].queryset = Department.objects.filter(tenant=self.request.hrm_tenant)
        ctx["form"] = form
        return ctx


class JobTitleCreateView(HrmAdminMixin, PostOnlyMixin, CreateView):
    model = JobTitle
    form_class = JobTitleForm
    success_url = reverse_lazy("hrm:job_title_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault("data", self.request.POST)
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        try:
            self.object.save()
            messages.success(self.request, "Job title created.")
        except Exception:
            messages.error(self.request, "Could not save job title (duplicate name?).")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors in the form.")
        return redirect(self.success_url)


class JobTitleUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = JobTitle
    form_class = JobTitleForm
    template_name = "hrm/job_title_edit.html"
    context_object_name = "job_title"
    page_title = "Edit job title"
    success_url = reverse_lazy("hrm:job_title_list")

    def get_queryset(self):
        return JobTitle.objects.filter(tenant=self.request.hrm_tenant)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["department"].queryset = Department.objects.filter(
            tenant=self.request.hrm_tenant
        )
        return form

    def form_valid(self, form):
        messages.success(self.request, "Job title updated.")
        return super().form_valid(form)


class JobTitleDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = JobTitle
    success_url = reverse_lazy("hrm:job_title_list")

    def get_queryset(self):
        return JobTitle.objects.filter(tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f"Job title “{name}” removed.")
        return response


# ── Employees ─────────────────────────────────────────────────────────────────


class EmployeeListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = Employee
    template_name = "hrm/employee_list.html"
    context_object_name = "employees"
    page_title = "Employees"

    def get_queryset(self):
        return Employee.objects.filter(tenant=self.request.hrm_tenant).select_related(
            "department", "job_title", "user"
        )


class EmployeeCreateView(HrmAdminMixin, HrmPageContextMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "hrm/employee_form.html"
    success_url = reverse_lazy("hrm:employee_list")
    page_title = "Add employee"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Employee created.")
        return redirect(self.success_url)


class EmployeeUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "hrm/employee_form.html"
    context_object_name = "employee"
    success_url = reverse_lazy("hrm:employee_list")
    page_title = "Edit employee"

    def get_queryset(self):
        return Employee.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Employee updated.")
        return super().form_valid(form)


class EmployeeDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = Employee
    success_url = reverse_lazy("hrm:employee_list")

    def get_queryset(self):
        return Employee.objects.filter(tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.full_name
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f"{name} removed from directory.")
        return response


# ── Leave types ───────────────────────────────────────────────────────────────


class LeaveTypeListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = LeaveType
    template_name = "hrm/leave_type_list.html"
    context_object_name = "leave_types"
    page_title = "Leave types"

    def get_queryset(self):
        return LeaveType.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = LeaveTypeForm()
        return ctx


class LeaveTypeCreateView(HrmAdminMixin, PostOnlyMixin, CreateView):
    model = LeaveType
    form_class = LeaveTypeForm
    success_url = reverse_lazy("hrm:leave_type_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault("data", self.request.POST)
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        try:
            self.object.save()
            messages.success(self.request, "Leave type created.")
        except Exception:
            messages.error(self.request, "Could not save leave type (duplicate name?).")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors in the form.")
        return redirect(self.success_url)


class LeaveTypeUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = LeaveType
    form_class = LeaveTypeForm
    template_name = "hrm/leave_type_edit.html"
    context_object_name = "leave_type"
    success_url = reverse_lazy("hrm:leave_type_list")
    page_title = "Edit leave type"

    def get_queryset(self):
        return LeaveType.objects.filter(tenant=self.request.hrm_tenant)

    def form_valid(self, form):
        messages.success(self.request, "Leave type updated.")
        return super().form_valid(form)


class LeaveTypeDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = LeaveType
    success_url = reverse_lazy("hrm:leave_type_list")

    def get_queryset(self):
        return LeaveType.objects.filter(tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, f"Leave type “{name}” removed.")
            return response
        except ProtectedError:
            messages.error(
                self.request,
                "Cannot delete this leave type while leave requests still reference it.",
            )
            return redirect(self.success_url)


# ── Leave requests ────────────────────────────────────────────────────────────


class LeaveRequestListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = LeaveRequest
    template_name = "hrm/leave_request_list.html"
    context_object_name = "leaves"
    page_title = "Leave requests"

    def get_queryset(self):
        return (
            LeaveRequest.objects.filter(employee__tenant=self.request.hrm_tenant)
            .select_related("employee", "leave_type", "reviewed_by")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if "form" not in ctx:
            ctx["form"] = LeaveRequestForm(tenant=self.request.hrm_tenant)
        ctx.setdefault("leave_form_invalid", False)
        return ctx

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        form = LeaveRequestForm(request.POST, tenant=request.hrm_tenant)
        if form.is_valid():
            lr = form.save(commit=False)
            if (
                lr.employee.tenant_id != request.hrm_tenant.id
                or lr.leave_type.tenant_id != request.hrm_tenant.id
            ):
                messages.error(request, "Invalid employee or leave type.")
            else:
                if lr.leave_type.requires_approval:
                    lr.status = LeaveRequest.Status.PENDING
                else:
                    lr.status = LeaveRequest.Status.APPROVED
                    lr.reviewed_by = request.user
                    lr.reviewed_at = timezone.now()
                lr.save()
                if lr.status == LeaveRequest.Status.APPROVED:
                    messages.success(request, "Leave request recorded and auto-approved.")
                else:
                    messages.success(request, "Leave request recorded.")
                return redirect("hrm:leave_request_list")
        messages.error(request, "Please fix the errors below.")
        ctx = self.get_context_data(form=form, leave_form_invalid=True)
        return self.render_to_response(ctx)


class LeaveRequestApproveView(HrmAdminMixin, View):
    permission_codename = "hrm.leave.approve"

    def post(self, request, pk):
        tenant = request.hrm_tenant
        with transaction.atomic():
            lr = get_object_or_404(
                LeaveRequest.objects.select_for_update().select_related("employee"),
                pk=pk,
                employee__tenant=tenant,
            )
            if lr.status != LeaveRequest.Status.PENDING:
                messages.warning(request, "This request is no longer pending.")
            else:
                lr.status = LeaveRequest.Status.APPROVED
                lr.reviewed_by = request.user
                lr.reviewed_at = timezone.now()
                lr.save(update_fields=["status", "reviewed_by", "reviewed_at"])
                messages.success(request, "Leave approved.")
        return redirect("hrm:leave_request_list")

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class LeaveRequestRejectView(HrmAdminMixin, View):
    permission_codename = "hrm.leave.approve"

    def post(self, request, pk):
        tenant = request.hrm_tenant
        with transaction.atomic():
            lr = get_object_or_404(
                LeaveRequest.objects.select_for_update().select_related("employee"),
                pk=pk,
                employee__tenant=tenant,
            )
            if lr.status != LeaveRequest.Status.PENDING:
                messages.warning(request, "This request is no longer pending.")
            else:
                lr.status = LeaveRequest.Status.REJECTED
                lr.reviewed_by = request.user
                lr.reviewed_at = timezone.now()
                lr.save(update_fields=["status", "reviewed_by", "reviewed_at"])
                messages.success(request, "Leave rejected.")
        return redirect("hrm:leave_request_list")

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


# ── Holidays ──────────────────────────────────────────────────────────────────


class HolidayListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = Holiday
    template_name = "hrm/holiday_list.html"
    context_object_name = "holidays"
    page_title = "Holidays"

    def get_queryset(self):
        return Holiday.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = HolidayForm()
        return ctx


class HolidayCreateView(HrmAdminMixin, PostOnlyMixin, CreateView):
    model = Holiday
    form_class = HolidayForm
    success_url = reverse_lazy("hrm:holiday_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault("data", self.request.POST)
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Holiday saved.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors in the form.")
        return redirect(self.success_url)


class HolidayUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = Holiday
    form_class = HolidayForm
    template_name = "hrm/holiday_edit.html"
    context_object_name = "holiday"
    success_url = reverse_lazy("hrm:holiday_list")
    page_title = "Edit holiday"

    def get_queryset(self):
        return Holiday.objects.filter(tenant=self.request.hrm_tenant)

    def form_valid(self, form):
        messages.success(self.request, "Holiday updated.")
        return super().form_valid(form)


class HolidayDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = Holiday
    success_url = reverse_lazy("hrm:holiday_list")

    def get_queryset(self):
        return Holiday.objects.filter(tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f"Holiday “{name}” removed.")
        return response


# ── Notices ───────────────────────────────────────────────────────────────────


class NoticeListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = Notice
    template_name = "hrm/notice_list.html"
    context_object_name = "notices"
    page_title = "Notices"

    def get_queryset(self):
        return Notice.objects.filter(tenant=self.request.hrm_tenant).select_related("created_by")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = NoticeForm()
        return ctx


class NoticeCreateView(HrmAdminMixin, PostOnlyMixin, CreateView):
    model = Notice
    form_class = NoticeForm
    success_url = reverse_lazy("hrm:notice_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault("data", self.request.POST)
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.created_by = self.request.user
        self.object.save()
        messages.success(self.request, "Notice published.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors in the form.")
        return redirect(self.success_url)


class NoticeUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = Notice
    form_class = NoticeForm
    template_name = "hrm/notice_edit.html"
    context_object_name = "notice"
    success_url = reverse_lazy("hrm:notice_list")
    page_title = "Edit notice"

    def get_queryset(self):
        return Notice.objects.filter(tenant=self.request.hrm_tenant)

    def form_valid(self, form):
        messages.success(self.request, "Notice updated.")
        return super().form_valid(form)


class NoticeDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = Notice
    success_url = reverse_lazy("hrm:notice_list")

    def get_queryset(self):
        return Notice.objects.filter(tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        title = self.object.title
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f"Notice “{title}” removed.")
        return response


# ── Attendance ────────────────────────────────────────────────────────────────


class AttendanceRecordListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = AttendanceRecord
    template_name = "hrm/attendance_list.html"
    context_object_name = "records"
    page_title = "Attendance"

    def get_queryset(self):
        qs = AttendanceRecord.objects.filter(
            employee__tenant=self.request.hrm_tenant
        ).select_related("employee", "employee__department")
        g = self.request.GET
        d = (g.get("date") or "").strip()
        if d:
            qs = qs.filter(date=d)
        dept = g.get("department")
        if dept == "none":
            qs = qs.filter(employee__department__isnull=True)
        elif dept and str(dept).isdigit():
            qs = qs.filter(employee__department_id=int(dept))
        st = (g.get("status") or "").strip()
        valid_status = {c.value for c in AttendanceRecord.Status}
        if st in valid_status:
            qs = qs.filter(status=st)
        return qs.order_by("-date", "employee__full_name")[:500]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["bulk_form"] = AttendanceBulkForm()
        ctx["filter_date"] = (self.request.GET.get("date") or "").strip()
        ctx["filter_department"] = (self.request.GET.get("department") or "").strip()
        ctx["filter_status"] = (self.request.GET.get("status") or "").strip()
        ctx["departments"] = Department.objects.filter(
            tenant=self.request.hrm_tenant
        ).order_by("name")
        ctx["attendance_statuses"] = AttendanceRecord.Status.choices
        return ctx


class AttendanceRecordCreateView(HrmAdminMixin, View):
    """POST: bulk attendance for one or more employees (same date / times / status)."""
    permission_codename = "hrm.attendance.manage"

    def post(self, request):
        tenant = request.hrm_tenant
        bulk_form = AttendanceBulkForm(request.POST)
        raw_ids = request.POST.getlist("employee_ids")
        ids = []
        for x in raw_ids:
            s = str(x).strip()
            if s.isdigit():
                ids.append(int(s))
        ids = list(dict.fromkeys(ids))

        if not bulk_form.is_valid():
            messages.error(request, "Please fix the attendance form errors.")
            return redirect("hrm:attendance_list")
        if not ids:
            messages.error(request, "Select at least one employee.")
            return redirect("hrm:attendance_list")

        valid = set(
            Employee.objects.filter(tenant=tenant, pk__in=ids)
            .exclude(status=Employee.Status.TERMINATED)
            .values_list("pk", flat=True)
        )
        if valid != set(ids):
            messages.error(request, "One or more employees are invalid or inactive.")
            return redirect("hrm:attendance_list")

        d = bulk_form.cleaned_data
        n = 0
        try:
            with transaction.atomic():
                for eid in sorted(valid):
                    AttendanceRecord.objects.update_or_create(
                        employee_id=eid,
                        date=d["date"],
                        defaults={
                            "check_in": d["check_in"],
                            "check_out": d["check_out"],
                            "status": d["status"],
                            "notes": d["notes"] or "",
                        },
                    )
                    n += 1
        except ValidationError as exc:
            err = (
                "; ".join(exc.messages)
                if hasattr(exc, "messages")
                else getattr(exc, "message", str(exc))
            )
            messages.error(request, err or "Could not save attendance.")
            return redirect("hrm:attendance_list")

        messages.success(request, f"Attendance saved for {n} employee(s).")
        return redirect("hrm:attendance_list")


class AttendanceRecordUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = AttendanceRecord
    form_class = AttendanceRecordForm
    template_name = "hrm/attendance_edit.html"
    context_object_name = "record"
    success_url = reverse_lazy("hrm:attendance_list")
    page_title = "Edit attendance"
    permission_codename = "hrm.attendance.manage"

    def get_queryset(self):
        return AttendanceRecord.objects.filter(employee__tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        emp = form.cleaned_data.get("employee")
        if emp and emp.tenant_id != self.request.hrm_tenant.id:
            messages.error(self.request, "Invalid employee.")
            return redirect(self.success_url)
        messages.success(self.request, "Attendance updated.")
        return super().form_valid(form)


class AttendanceRecordDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = AttendanceRecord
    success_url = reverse_lazy("hrm:attendance_list")
    permission_codename = "hrm.attendance.manage"

    def get_queryset(self):
        return AttendanceRecord.objects.filter(employee__tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, "Attendance entry removed.")
        return response


class AttendanceBulkActionView(HrmAdminMixin, View):
    """POST: bulk_action=delete + attendance_ids[] + optional next (return path)."""

    http_method_names = ["post"]
    permission_codename = "hrm.attendance.manage"

    def post(self, request):
        action = (request.POST.get("bulk_action") or "").strip()
        raw = request.POST.getlist("attendance_ids")
        ids = []
        for x in raw:
            s = str(x).strip()
            if s.isdigit():
                ids.append(int(s))
        ids = list(dict.fromkeys(ids))
        tenant = request.hrm_tenant

        def redirect_back():
            nxt = (request.POST.get("next") or "").strip()
            if nxt.startswith("/") and not nxt.startswith("//"):
                return redirect(nxt)
            return redirect("hrm:attendance_list")

        if not ids or action != "delete":
            messages.error(request, "Select at least one row and choose delete.")
            return redirect_back()

        qs = AttendanceRecord.objects.filter(
            pk__in=ids,
            employee__tenant=tenant,
        )
        n = qs.count()
        qs.delete()
        messages.success(request, f"Removed {n} attendance record(s).")
        return redirect_back()


# ── Overtime ────────────────────────────────────────────────────────────────────


class OvertimeRequestListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = OvertimeRequest
    template_name = "hrm/overtime_list.html"
    context_object_name = "overtimes"
    page_title = "Overtime"

    def get_queryset(self):
        qs = OvertimeRequest.objects.filter(
            employee__tenant=self.request.hrm_tenant
        ).select_related("employee", "employee__department", "reviewed_by")
        g = self.request.GET
        d = (g.get("date") or "").strip()
        if d:
            qs = qs.filter(work_date=d)
        dept = g.get("department")
        if dept == "none":
            qs = qs.filter(employee__department__isnull=True)
        elif dept and str(dept).isdigit():
            qs = qs.filter(employee__department_id=int(dept))
        st = (g.get("status") or "").strip()
        if st in (
            OvertimeRequest.Status.PENDING,
            OvertimeRequest.Status.APPROVED,
            OvertimeRequest.Status.REJECTED,
        ):
            qs = qs.filter(status=st)
        return qs.order_by("-work_date", "-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["bulk_form"] = OvertimeBulkForm()
        ctx["filter_date"] = (self.request.GET.get("date") or "").strip()
        ctx["filter_department"] = (self.request.GET.get("department") or "").strip()
        ctx["filter_status"] = (self.request.GET.get("status") or "").strip()
        ctx["departments"] = Department.objects.filter(
            tenant=self.request.hrm_tenant
        ).order_by("name")
        return ctx


class OvertimeRequestCreateView(HrmAdminMixin, View):
    """POST: bulk overtime rows for one or more employees (same date / hours / reason)."""
    permission_codename = "hrm.overtime.manage"

    def post(self, request):
        tenant = request.hrm_tenant
        bulk_form = OvertimeBulkForm(request.POST)
        raw_ids = request.POST.getlist("employee_ids")
        ids = []
        for x in raw_ids:
            s = str(x).strip()
            if s.isdigit():
                ids.append(int(s))
        ids = list(dict.fromkeys(ids))

        if not bulk_form.is_valid():
            messages.error(request, "Please fix the overtime form errors.")
            return redirect("hrm:overtime_list")
        if not ids:
            messages.error(request, "Select at least one employee.")
            return redirect("hrm:overtime_list")

        valid = set(
            Employee.objects.filter(tenant=tenant, pk__in=ids)
            .exclude(status=Employee.Status.TERMINATED)
            .values_list("pk", flat=True)
        )
        if valid != set(ids):
            messages.error(request, "One or more employees are invalid or inactive.")
            return redirect("hrm:overtime_list")

        d = bulk_form.cleaned_data
        n = 0
        try:
            with transaction.atomic():
                for eid in sorted(valid):
                    OvertimeRequest.objects.create(
                        employee_id=eid,
                        work_date=d["work_date"],
                        hours=d["hours"],
                        reason=d["reason"] or "",
                    )
                    n += 1
        except ValidationError as exc:
            err = (
                "; ".join(exc.messages)
                if hasattr(exc, "messages")
                else getattr(exc, "message", str(exc))
            )
            messages.error(request, err or "Could not save overtime.")
            return redirect("hrm:overtime_list")

        messages.success(request, f"Overtime submitted for {n} employee(s).")
        return redirect("hrm:overtime_list")


class OvertimeRequestUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = OvertimeRequest
    form_class = OvertimeRequestForm
    template_name = "hrm/overtime_edit.html"
    context_object_name = "overtime"
    success_url = reverse_lazy("hrm:overtime_list")
    page_title = "Edit overtime"
    permission_codename = "hrm.overtime.manage"

    def get_queryset(self):
        return OvertimeRequest.objects.filter(employee__tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Overtime request updated.")
        return super().form_valid(form)


class OvertimeRequestDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = OvertimeRequest
    success_url = reverse_lazy("hrm:overtime_list")
    permission_codename = "hrm.overtime.manage"

    def get_queryset(self):
        return OvertimeRequest.objects.filter(employee__tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, "Overtime request removed.")
        return response


class OvertimeApproveView(HrmAdminMixin, View):
    permission_codename = "hrm.overtime.approve"

    def post(self, request, pk):
        with transaction.atomic():
            ot = get_object_or_404(
                OvertimeRequest.objects.select_for_update().select_related("employee"),
                pk=pk,
                employee__tenant=request.hrm_tenant,
            )
            if ot.status != OvertimeRequest.Status.PENDING:
                messages.warning(request, "This request is no longer pending.")
            else:
                ot.status = OvertimeRequest.Status.APPROVED
                ot.reviewed_by = request.user
                ot.reviewed_at = timezone.now()
                ot.save(update_fields=["status", "reviewed_by", "reviewed_at"])
                messages.success(request, "Overtime approved.")
        return redirect("hrm:overtime_list")

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class OvertimeRejectView(HrmAdminMixin, View):
    permission_codename = "hrm.overtime.approve"

    def post(self, request, pk):
        with transaction.atomic():
            ot = get_object_or_404(
                OvertimeRequest.objects.select_for_update().select_related("employee"),
                pk=pk,
                employee__tenant=request.hrm_tenant,
            )
            if ot.status != OvertimeRequest.Status.PENDING:
                messages.warning(request, "This request is no longer pending.")
            else:
                ot.status = OvertimeRequest.Status.REJECTED
                ot.reviewed_by = request.user
                ot.reviewed_at = timezone.now()
                ot.save(update_fields=["status", "reviewed_by", "reviewed_at"])
                messages.success(request, "Overtime rejected.")
        return redirect("hrm:overtime_list")

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class OvertimeBulkActionView(HrmAdminMixin, View):
    """POST: bulk_action=approve|reject|delete + overtime_ids[] + optional next (return path)."""

    http_method_names = ["post"]
    permission_codename = "hrm.overtime.manage"

    def post(self, request):
        action = (request.POST.get("bulk_action") or "").strip()
        raw = request.POST.getlist("overtime_ids")
        ids = []
        for x in raw:
            s = str(x).strip()
            if s.isdigit():
                ids.append(int(s))
        ids = list(dict.fromkeys(ids))
        tenant = request.hrm_tenant

        def redirect_back():
            nxt = (request.POST.get("next") or "").strip()
            if nxt.startswith("/") and not nxt.startswith("//"):
                return redirect(nxt)
            return redirect("hrm:overtime_list")

        if not ids or action not in ("approve", "reject", "delete"):
            messages.error(request, "Select at least one row and choose an action.")
            return redirect_back()

        qs = OvertimeRequest.objects.filter(
            pk__in=ids,
            employee__tenant=tenant,
        )

        if action == "delete":
            n = qs.count()
            qs.delete()
            messages.success(request, f"Removed {n} overtime record(s).")
            return redirect_back()

        now = timezone.now()
        pending = qs.select_for_update().filter(status=OvertimeRequest.Status.PENDING)
        n_ok = 0
        with transaction.atomic():
            for ot in pending:
                if action == "approve":
                    ot.status = OvertimeRequest.Status.APPROVED
                else:
                    ot.status = OvertimeRequest.Status.REJECTED
                ot.reviewed_by = request.user
                ot.reviewed_at = now
                ot.save(update_fields=["status", "reviewed_by", "reviewed_at"])
                n_ok += 1

        skipped = qs.count() - n_ok
        verb = "Approved" if action == "approve" else "Rejected"
        messages.success(request, f"{verb} {n_ok} request(s).")
        if skipped:
            messages.warning(
                request,
                f"{skipped} row(s) were not pending and were skipped.",
            )
        return redirect_back()


# Aliases for URL backwards compatibility (function names)
set_active_hrm_tenant = SetActiveHrmTenantView.as_view()
hrm_dashboard = HrmDashboardView.as_view()
department_list = DepartmentListView.as_view()
department_create = DepartmentCreateView.as_view()
department_edit = DepartmentUpdateView.as_view()
department_delete = DepartmentDeleteView.as_view()
job_title_list = JobTitleListView.as_view()
job_title_create = JobTitleCreateView.as_view()
job_title_edit = JobTitleUpdateView.as_view()
job_title_delete = JobTitleDeleteView.as_view()
employee_list = EmployeeListView.as_view()
employee_create = EmployeeCreateView.as_view()
employee_edit = EmployeeUpdateView.as_view()
employee_delete = EmployeeDeleteView.as_view()
leave_type_list = LeaveTypeListView.as_view()
leave_type_create = LeaveTypeCreateView.as_view()
leave_type_edit = LeaveTypeUpdateView.as_view()
leave_type_delete = LeaveTypeDeleteView.as_view()
leave_request_list = LeaveRequestListView.as_view()
leave_request_approve = LeaveRequestApproveView.as_view()
leave_request_reject = LeaveRequestRejectView.as_view()
holiday_list = HolidayListView.as_view()
holiday_create = HolidayCreateView.as_view()
holiday_edit = HolidayUpdateView.as_view()
holiday_delete = HolidayDeleteView.as_view()
notice_list = NoticeListView.as_view()
notice_create = NoticeCreateView.as_view()
notice_edit = NoticeUpdateView.as_view()
notice_delete = NoticeDeleteView.as_view()
attendance_list = AttendanceRecordListView.as_view()
attendance_create = AttendanceRecordCreateView.as_view()
attendance_edit = AttendanceRecordUpdateView.as_view()
attendance_delete = AttendanceRecordDeleteView.as_view()
attendance_bulk_action = AttendanceBulkActionView.as_view()
overtime_list = OvertimeRequestListView.as_view()
overtime_create = OvertimeRequestCreateView.as_view()
overtime_edit = OvertimeRequestUpdateView.as_view()
overtime_delete = OvertimeRequestDeleteView.as_view()
overtime_approve = OvertimeApproveView.as_view()
overtime_reject = OvertimeRejectView.as_view()
overtime_bulk_action = OvertimeBulkActionView.as_view()
