"""Shift definitions and roster rules (weekly, date range, one-day) — tenant-scoped."""

import calendar
import datetime

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .forms import (
    EmployeeShiftDateRangeForm,
    EmployeeShiftExceptionForm,
    EmployeeShiftWeekdayForm,
    RosterBulkForm,
    ShiftForm,
)
from .mixins import HrmAdminMixin, HrmPageContextMixin, PostOnlyMixin
from .models import (
    Employee,
    EmployeeShiftDateRange,
    EmployeeShiftException,
    EmployeeShiftWeekday,
    Shift,
)
from .services.shift_resolution import resolve_shift_for_date

WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ── Shift master ──────────────────────────────────────────────────────────────


class ShiftListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = Shift
    template_name = "hrm/shift_list.html"
    context_object_name = "shifts"
    page_title = "Shifts"

    def get_queryset(self):
        return Shift.objects.filter(tenant=self.request.hrm_tenant).order_by("code")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = ShiftForm()
        return ctx


class ShiftCreateView(HrmAdminMixin, PostOnlyMixin, CreateView):
    model = Shift
    form_class = ShiftForm
    success_url = reverse_lazy("hrm:shift_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault("data", self.request.POST)
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        try:
            self.object.save()
            messages.success(self.request, "Shift created.")
        except Exception:
            messages.error(self.request, "Could not save shift (duplicate code?).")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the shift form.")
        return redirect(self.success_url)


class ShiftUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = Shift
    form_class = ShiftForm
    template_name = "hrm/shift_edit.html"
    context_object_name = "shift"
    page_title = "Edit shift"
    success_url = reverse_lazy("hrm:shift_list")

    def get_queryset(self):
        return Shift.objects.filter(tenant=self.request.hrm_tenant)


class ShiftDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = Shift
    success_url = reverse_lazy("hrm:shift_list")

    def get_queryset(self):
        return Shift.objects.filter(tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = self.object.code
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f"Shift “{label}” removed.")
        return response


# ── Weekly rules ──────────────────────────────────────────────────────────────


class RosterWeekdayListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = EmployeeShiftWeekday
    template_name = "hrm/roster_weekday_list.html"
    context_object_name = "rows"
    page_title = "Weekly shift patterns"

    def get_queryset(self):
        return (
            EmployeeShiftWeekday.objects.filter(employee__tenant=self.request.hrm_tenant)
            .select_related("employee", "shift")
            .order_by("employee__full_name", "weekday")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = EmployeeShiftWeekdayForm(tenant=self.request.hrm_tenant)
        ctx["form"] = f
        return ctx


class RosterWeekdayCreateView(HrmAdminMixin, PostOnlyMixin, CreateView):
    model = EmployeeShiftWeekday
    form_class = EmployeeShiftWeekdayForm
    success_url = reverse_lazy("hrm:roster_weekday_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        kwargs.setdefault("data", self.request.POST)
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        if obj.employee.tenant_id != self.request.hrm_tenant.id:
            messages.error(self.request, "Invalid employee.")
            return redirect(self.success_url)
        try:
            obj.full_clean()
            obj.save()
            messages.success(self.request, "Weekly pattern saved.")
        except Exception as e:
            messages.error(self.request, str(e) or "Could not save (duplicate weekday?).")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the form.")
        return redirect(self.success_url)


class RosterWeekdayUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = EmployeeShiftWeekday
    form_class = EmployeeShiftWeekdayForm
    template_name = "hrm/roster_weekday_edit.html"
    context_object_name = "row"
    page_title = "Edit weekly pattern"
    success_url = reverse_lazy("hrm:roster_weekday_list")

    def get_queryset(self):
        return EmployeeShiftWeekday.objects.filter(employee__tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs


class RosterWeekdayDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = EmployeeShiftWeekday
    success_url = reverse_lazy("hrm:roster_weekday_list")

    def get_queryset(self):
        return EmployeeShiftWeekday.objects.filter(employee__tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, "Weekly pattern removed.")
        return response


# ── Date ranges ──────────────────────────────────────────────────────────────


class RosterRangeListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = EmployeeShiftDateRange
    template_name = "hrm/roster_range_list.html"
    context_object_name = "rows"
    page_title = "Shift date ranges"

    def get_queryset(self):
        return (
            EmployeeShiftDateRange.objects.filter(employee__tenant=self.request.hrm_tenant)
            .select_related("employee", "shift")
            .order_by("-start_date")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = EmployeeShiftDateRangeForm(tenant=self.request.hrm_tenant)
        return ctx


class RosterRangeCreateView(HrmAdminMixin, PostOnlyMixin, CreateView):
    model = EmployeeShiftDateRange
    form_class = EmployeeShiftDateRangeForm
    success_url = reverse_lazy("hrm:roster_range_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        kwargs.setdefault("data", self.request.POST)
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        if obj.employee.tenant_id != self.request.hrm_tenant.id:
            messages.error(self.request, "Invalid employee.")
            return redirect(self.success_url)
        try:
            obj.full_clean()
            obj.save()
            messages.success(self.request, "Date range saved.")
        except Exception as e:
            messages.error(self.request, str(e) or "Could not save.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the form.")
        return redirect(self.success_url)


class RosterRangeUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = EmployeeShiftDateRange
    form_class = EmployeeShiftDateRangeForm
    template_name = "hrm/roster_range_edit.html"
    context_object_name = "row"
    page_title = "Edit date range"
    success_url = reverse_lazy("hrm:roster_range_list")

    def get_queryset(self):
        return EmployeeShiftDateRange.objects.filter(employee__tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs


class RosterRangeDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = EmployeeShiftDateRange
    success_url = reverse_lazy("hrm:roster_range_list")

    def get_queryset(self):
        return EmployeeShiftDateRange.objects.filter(employee__tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, "Date range removed.")
        return response


# ── One-day exceptions ────────────────────────────────────────────────────────


class RosterExceptionListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = EmployeeShiftException
    template_name = "hrm/roster_exception_list.html"
    context_object_name = "rows"
    page_title = "One-day shift overrides"

    def get_queryset(self):
        return (
            EmployeeShiftException.objects.filter(employee__tenant=self.request.hrm_tenant)
            .select_related("employee", "shift")
            .order_by("-date")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = EmployeeShiftExceptionForm(tenant=self.request.hrm_tenant)
        return ctx


class RosterExceptionCreateView(HrmAdminMixin, PostOnlyMixin, CreateView):
    model = EmployeeShiftException
    form_class = EmployeeShiftExceptionForm
    success_url = reverse_lazy("hrm:roster_exception_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        kwargs.setdefault("data", self.request.POST)
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        if obj.employee.tenant_id != self.request.hrm_tenant.id:
            messages.error(self.request, "Invalid employee.")
            return redirect(self.success_url)
        try:
            obj.full_clean()
            obj.save()
            messages.success(self.request, "Override saved.")
        except Exception as e:
            messages.error(self.request, str(e) or "Could not save (duplicate date?).")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the form.")
        return redirect(self.success_url)


class RosterExceptionUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = EmployeeShiftException
    form_class = EmployeeShiftExceptionForm
    template_name = "hrm/roster_exception_edit.html"
    context_object_name = "row"
    page_title = "Edit override"
    success_url = reverse_lazy("hrm:roster_exception_list")

    def get_queryset(self):
        return EmployeeShiftException.objects.filter(employee__tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs


class RosterExceptionDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = EmployeeShiftException
    success_url = reverse_lazy("hrm:roster_exception_list")

    def get_queryset(self):
        return EmployeeShiftException.objects.filter(employee__tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, "Override removed.")
        return response


# ── Preview calendar ──────────────────────────────────────────────────────────


class RosterBulkView(HrmAdminMixin, HrmPageContextMixin, TemplateView):
    """Bulk apply shift rules using the same employee picker as attendance."""

    template_name = "hrm/roster_bulk.html"
    page_title = "Bulk shift rules"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["bulk_form"] = RosterBulkForm(tenant=self.request.hrm_tenant)
        return ctx


class RosterBulkApplyView(HrmAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request):
        tenant = request.hrm_tenant
        form = RosterBulkForm(request.POST, tenant=tenant)
        raw_ids = request.POST.getlist("employee_ids")
        ids = []
        for x in raw_ids:
            s = str(x).strip()
            if s.isdigit():
                ids.append(int(s))
        ids = list(dict.fromkeys(ids))

        if not form.is_valid():
            messages.error(request, "Please fix the form and try again.")
            return redirect("hrm:roster_bulk")

        if not ids:
            messages.error(request, "Select at least one employee.")
            return redirect("hrm:roster_bulk")

        valid = set(
            Employee.objects.filter(tenant=tenant, pk__in=ids)
            .exclude(status=Employee.Status.TERMINATED)
            .values_list("pk", flat=True)
        )
        if valid != set(ids):
            messages.error(request, "One or more employees are invalid or terminated.")
            return redirect("hrm:roster_bulk")

        d = form.cleaned_data
        rt = d["rule_type"]
        sh = d.get("shift")
        nt = (d.get("note") or "").strip()

        try:
            with transaction.atomic():
                if rt == RosterBulkForm.RULE_DEFAULT:
                    Employee.objects.filter(pk__in=valid).update(default_shift=sh)
                    n = len(valid)
                elif rt == RosterBulkForm.RULE_WEEKDAY:
                    wd = d["weekday_int"]
                    for eid in sorted(valid):
                        EmployeeShiftWeekday.objects.update_or_create(
                            employee_id=eid,
                            weekday=wd,
                            defaults={"shift": sh},
                        )
                    n = len(valid)
                elif rt == RosterBulkForm.RULE_RANGE:
                    for eid in sorted(valid):
                        EmployeeShiftDateRange.objects.create(
                            employee_id=eid,
                            start_date=d["start_date"],
                            end_date=d["end_date"],
                            shift=sh,
                            note=nt,
                        )
                    n = len(valid)
                else:
                    exd = d["exception_date"]
                    for eid in sorted(valid):
                        EmployeeShiftException.objects.update_or_create(
                            employee_id=eid,
                            date=exd,
                            defaults={"shift": sh, "note": nt},
                        )
                    n = len(valid)
        except Exception as exc:
            messages.error(request, str(exc) or "Could not save roster rules.")
            return redirect("hrm:roster_bulk")

        messages.success(request, f"Applied roster rule to {n} employee(s).")
        return redirect("hrm:roster_bulk")


class RosterPreviewView(HrmAdminMixin, HrmPageContextMixin, TemplateView):
    template_name = "hrm/roster_preview.html"
    page_title = "Roster preview"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        emp_qs = Employee.objects.filter(tenant=tenant).order_by("full_name")
        ctx["employees"] = emp_qs

        emp_id = self.request.GET.get("employee")
        ym = self.request.GET.get("month")  # YYYY-MM

        today = datetime.date.today()
        if ym and len(ym) >= 7 and ym[4:5] == "-":
            try:
                y, m = int(ym[:4]), int(ym[5:7])
                month_start = datetime.date(y, m, 1)
            except ValueError:
                month_start = today.replace(day=1)
        else:
            month_start = today.replace(day=1)

        ctx["selected_month"] = month_start.strftime("%Y-%m")
        last_day = calendar.monthrange(month_start.year, month_start.month)[1]
        month_end = datetime.date(month_start.year, month_start.month, last_day)

        days = []
        d = month_start
        while d <= month_end:
            days.append(d)
            d += datetime.timedelta(days=1)
        ctx["days"] = days
        ctx["month_label"] = month_start.strftime("%B %Y")

        preview_rows = []
        employee = None
        if emp_id and str(emp_id).isdigit():
            employee = emp_qs.filter(pk=int(emp_id)).first()
        ctx["selected_employee_id"] = str(employee.pk) if employee else ""

        if employee:
            for day in days:
                sh = resolve_shift_for_date(employee, day)
                preview_rows.append(
                    {
                        "date": day,
                        "weekday": WEEKDAY_LABELS[day.weekday()],
                        "shift": sh,
                        "shift_label": (
                            f"{sh.code} ({sh.start_time.strftime('%H:%M')}–{sh.end_time.strftime('%H:%M')})"
                            if sh
                            else "—"
                        ),
                    }
                )
        ctx["preview_rows"] = preview_rows
        ctx["preview_employee"] = employee

        prev_m = (month_start.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        next_m = (month_end + datetime.timedelta(days=1)).replace(day=1)
        q = f"employee={ctx['selected_employee_id']}" if ctx["selected_employee_id"] else ""
        ctx["prev_month"] = prev_m.strftime("%Y-%m")
        ctx["next_month"] = next_m.strftime("%Y-%m")
        return ctx


class ShiftManagementGuideView(HrmAdminMixin, HrmPageContextMixin, TemplateView):
    """In-app Bangla guide: story + steps for shift & roster (dummy company example)."""

    template_name = "hrm/shift_management_guide.html"
    page_title = "শিফট ম্যানেজমেন্ট গাইড"


# URL aliases
shift_management_guide = ShiftManagementGuideView.as_view()
shift_list = ShiftListView.as_view()
shift_create = ShiftCreateView.as_view()
shift_edit = ShiftUpdateView.as_view()
shift_delete = ShiftDeleteView.as_view()
roster_weekday_list = RosterWeekdayListView.as_view()
roster_weekday_create = RosterWeekdayCreateView.as_view()
roster_weekday_edit = RosterWeekdayUpdateView.as_view()
roster_weekday_delete = RosterWeekdayDeleteView.as_view()
roster_range_list = RosterRangeListView.as_view()
roster_range_create = RosterRangeCreateView.as_view()
roster_range_edit = RosterRangeUpdateView.as_view()
roster_range_delete = RosterRangeDeleteView.as_view()
roster_exception_list = RosterExceptionListView.as_view()
roster_exception_create = RosterExceptionCreateView.as_view()
roster_exception_edit = RosterExceptionUpdateView.as_view()
roster_exception_delete = RosterExceptionDeleteView.as_view()
roster_bulk = RosterBulkView.as_view()
roster_bulk_apply = RosterBulkApplyView.as_view()
roster_preview = RosterPreviewView.as_view()
