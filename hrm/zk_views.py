"""ZKTeco devices, raw attendance logs, geofence locations — tenant-scoped."""

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import AttendanceLocationForm, ZKDeviceForm
from .mixins import HrmAdminMixin, HrmPageContextMixin
from .models import AttendanceLocation, AttendanceLog, DeviceUser, Employee, ZKDevice
from .utils import (
    auto_create_employee_from_device_user,
    import_attendance_from_device,
    import_users_from_device,
)


class ZKDeviceListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = ZKDevice
    template_name = "hrm/zk_device_list.html"
    context_object_name = "devices"
    page_title = "ZKTeco devices"

    def get_queryset(self):
        return ZKDevice.objects.filter(tenant=self.request.hrm_tenant).order_by(
            "-last_activity", "serial_number"
        )


class ZKDeviceCreateView(HrmAdminMixin, HrmPageContextMixin, CreateView):
    model = ZKDevice
    form_class = ZKDeviceForm
    template_name = "hrm/zk_device_form.html"
    page_title = "Add ZKTeco device"
    success_url = reverse_lazy("hrm:zk_device_list")

    def form_valid(self, form):
        form.instance.tenant = self.request.hrm_tenant
        messages.success(self.request, "Device saved.")
        return super().form_valid(form)


class ZKDeviceUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = ZKDevice
    form_class = ZKDeviceForm
    template_name = "hrm/zk_device_form.html"
    page_title = "Edit ZKTeco device"
    success_url = reverse_lazy("hrm:zk_device_list")

    def get_queryset(self):
        return ZKDevice.objects.filter(tenant=self.request.hrm_tenant)

    def form_valid(self, form):
        messages.success(self.request, "Device updated.")
        return super().form_valid(form)


class ZKDeviceDeleteView(HrmAdminMixin, HrmPageContextMixin, DeleteView):
    model = ZKDevice
    template_name = "hrm/zk_device_confirm_delete.html"
    success_url = reverse_lazy("hrm:zk_device_list")
    page_title = "Remove device"

    def get_queryset(self):
        return ZKDevice.objects.filter(tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Device removed.")
        return super().delete(request, *args, **kwargs)


class ZKSyncUsersView(HrmAdminMixin, View):
    def post(self, request, pk):
        device = get_object_or_404(ZKDevice, pk=pk, tenant=request.hrm_tenant)
        if not device.supports_tcp():
            messages.error(request, "This device is not set to TCP (PyZK).")
            return redirect("hrm:zk_device_list")
        result = import_users_from_device(device)
        if result.get("success"):
            ac = request.POST.get("auto_employees", "1")
            if ac == "1":
                n = 0
                for du in DeviceUser.objects.filter(device=device):
                    if auto_create_employee_from_device_user(du):
                        n += 1
                messages.success(
                    request,
                    f"Imported users: {result.get('imported', 0)} new, "
                    f"{result.get('skipped', 0)} existing. Employees created: {n}.",
                )
            else:
                messages.success(request, f"Imported {result.get('imported', 0)} new device users.")
        else:
            messages.error(request, result.get("error", "Sync failed."))
        return redirect("hrm:zk_device_list")


class ZKSyncAttendanceView(HrmAdminMixin, View):
    def post(self, request, pk):
        device = get_object_or_404(ZKDevice, pk=pk, tenant=request.hrm_tenant)
        if not device.supports_tcp():
            messages.error(request, "This device is not set to TCP (PyZK).")
            return redirect("hrm:zk_device_list")
        result = import_attendance_from_device(device)
        if result.get("success"):
            messages.success(
                request,
                f"Pulled {result.get('total', 0)} punches, "
                f"saved {result.get('imported', 0)} new rows.",
            )
        else:
            messages.error(request, result.get("error", "Import failed."))
        return redirect("hrm:zk_attendance_log_list")


class AttendanceLogListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = AttendanceLog
    template_name = "hrm/attendance_log_list.html"
    context_object_name = "logs"
    page_title = "Attendance logs (devices)"
    paginate_by = 100

    def get_queryset(self):
        tenant = self.request.hrm_tenant
        qs = (
            AttendanceLog.objects.filter(Q(tenant=tenant) | Q(device__tenant=tenant))
            .distinct()
            .select_related("device", "employee", "matched_location")
        )
        g = self.request.GET
        df = (g.get("date_from") or "").strip()
        dt = (g.get("date_to") or "").strip()
        if df:
            qs = qs.filter(punch_time__date__gte=df)
        if dt:
            qs = qs.filter(punch_time__date__lte=dt)
        dev = g.get("device")
        if dev and str(dev).isdigit():
            qs = qs.filter(device_id=int(dev))
        uid = (g.get("user_id") or "").strip()
        if uid:
            qs = qs.filter(user_id=uid)
        if g.get("gps") == "1":
            qs = qs.filter(latitude__isnull=False, longitude__isnull=False)
        return qs.order_by("-punch_time")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        ctx["devices"] = ZKDevice.objects.filter(tenant=tenant).order_by("serial_number")
        ctx["filter_date_from"] = (self.request.GET.get("date_from") or "").strip()
        ctx["filter_date_to"] = (self.request.GET.get("date_to") or "").strip()
        ctx["filter_device"] = (self.request.GET.get("device") or "").strip()
        ctx["filter_user_id"] = (self.request.GET.get("user_id") or "").strip()
        ctx["filter_gps"] = self.request.GET.get("gps") == "1"
        log_list = list(ctx.get("object_list") or [])
        ids = {l.user_id for l in log_list}
        names = {}
        if ids:
            names = {
                e.zk_user_id: e.full_name
                for e in Employee.objects.filter(tenant=tenant, zk_user_id__in=ids)
            }
        rows = []
        for log in log_list:
            if getattr(log, "employee_id", None):
                emp_name = log.employee.full_name
            else:
                emp_name = names.get(log.user_id, "—")
            rows.append({"log": log, "emp_name": emp_name})
        ctx["log_rows"] = rows
        return ctx


class AttendanceLocationListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = AttendanceLocation
    template_name = "hrm/attendance_location_list.html"
    context_object_name = "locations"
    page_title = "Attendance locations"

    def get_queryset(self):
        return AttendanceLocation.objects.filter(tenant=self.request.hrm_tenant).order_by("name")


class AttendanceLocationCreateView(HrmAdminMixin, HrmPageContextMixin, CreateView):
    model = AttendanceLocation
    form_class = AttendanceLocationForm
    template_name = "hrm/attendance_location_form.html"
    page_title = "Add location"
    success_url = reverse_lazy("hrm:attendance_location_list")

    def form_valid(self, form):
        form.instance.tenant = self.request.hrm_tenant
        messages.success(self.request, "Location saved.")
        return super().form_valid(form)


class AttendanceLocationUpdateView(HrmAdminMixin, HrmPageContextMixin, UpdateView):
    model = AttendanceLocation
    form_class = AttendanceLocationForm
    template_name = "hrm/attendance_location_form.html"
    page_title = "Edit location"
    success_url = reverse_lazy("hrm:attendance_location_list")

    def get_queryset(self):
        return AttendanceLocation.objects.filter(tenant=self.request.hrm_tenant)

    def form_valid(self, form):
        messages.success(self.request, "Location updated.")
        return super().form_valid(form)


class AttendanceLocationDeleteView(HrmAdminMixin, HrmPageContextMixin, DeleteView):
    model = AttendanceLocation
    template_name = "hrm/attendance_location_confirm_delete.html"
    success_url = reverse_lazy("hrm:attendance_location_list")
    page_title = "Remove location"

    def get_queryset(self):
        return AttendanceLocation.objects.filter(tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Location removed.")
        return super().delete(request, *args, **kwargs)


zk_device_list = ZKDeviceListView.as_view()
zk_device_create = ZKDeviceCreateView.as_view()
zk_device_edit = ZKDeviceUpdateView.as_view()
zk_device_delete = ZKDeviceDeleteView.as_view()
zk_sync_users = ZKSyncUsersView.as_view()
zk_sync_attendance = ZKSyncAttendanceView.as_view()
zk_attendance_log_list = AttendanceLogListView.as_view()
attendance_location_list = AttendanceLocationListView.as_view()
attendance_location_create = AttendanceLocationCreateView.as_view()
attendance_location_edit = AttendanceLocationUpdateView.as_view()
attendance_location_delete = AttendanceLocationDeleteView.as_view()
