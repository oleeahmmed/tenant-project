"""GPS policy, location reports, attendance review queue — tenant admin."""

from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, ListView, TemplateView

from .forms import LocationAttendancePolicyForm
from .mixins import HrmAdminMixin, HrmPageContextMixin
from .models import AttendanceLog, LocationAttendancePolicy


class LocationPolicyEditView(HrmAdminMixin, HrmPageContextMixin, FormView):
    template_name = "hrm/location_policy_form.html"
    form_class = LocationAttendancePolicyForm
    success_url = reverse_lazy("hrm:location_policy")
    page_title = "GPS / location policy"

    def load_policy(self):
        obj, _ = LocationAttendancePolicy.objects.get_or_create(tenant=self.request.hrm_tenant)
        return obj

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["instance"] = self.load_policy()
        return kw

    def form_valid(self, form):
        form.instance.tenant = self.request.hrm_tenant
        form.save()
        messages.success(self.request, "Policy saved.")
        return super().form_valid(form)


class LocationAttendanceReportView(HrmAdminMixin, HrmPageContextMixin, TemplateView):
    template_name = "hrm/location_attendance_report.html"
    page_title = "Location attendance report"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        g = self.request.GET
        df = (g.get("date_from") or "").strip()
        dt = (g.get("date_to") or "").strip()
        qs = AttendanceLog.objects.filter(
            tenant=tenant,
            matched_location__isnull=False,
            validation_status=AttendanceLog.ValidationStatus.VALID,
        )
        if df:
            qs = qs.filter(punch_time__date__gte=df)
        if dt:
            qs = qs.filter(punch_time__date__lte=dt)
        by_loc = (
            qs.values("matched_location__name", "validation_status")
            .annotate(total=Count("id"))
            .order_by("matched_location__name")
        )
        exceptions = (
            AttendanceLog.objects.filter(tenant=tenant)
            .filter(
                Q(
                    validation_status__in=[
                        AttendanceLog.ValidationStatus.OUT_OF_GEOFENCE,
                        AttendanceLog.ValidationStatus.LOW_ACCURACY,
                        AttendanceLog.ValidationStatus.OUTSIDE_TIME,
                        AttendanceLog.ValidationStatus.HOLIDAY,
                    ]
                )
                | Q(requires_review=True)
            )
        )
        if df:
            exceptions = exceptions.filter(punch_time__date__gte=df)
        if dt:
            exceptions = exceptions.filter(punch_time__date__lte=dt)
        ctx["by_location"] = list(by_loc)
        ctx["exception_count"] = exceptions.count()
        ctx["filter_date_from"] = df
        ctx["filter_date_to"] = dt
        return ctx


class AttendanceReviewListView(HrmAdminMixin, HrmPageContextMixin, ListView):
    model = AttendanceLog
    template_name = "hrm/attendance_review_list.html"
    context_object_name = "logs"
    page_title = "Attendance review queue"
    paginate_by = 50

    def get_queryset(self):
        tenant = self.request.hrm_tenant
        return (
            AttendanceLog.objects.filter(tenant=tenant)
            .filter(
                Q(requires_review=True)
                | Q(validation_status=AttendanceLog.ValidationStatus.PENDING_REVIEW)
            )
            .select_related("employee", "matched_location", "device")
            .order_by("-punch_time")
        )


class AttendanceReviewApproveView(HrmAdminMixin, View):
    def post(self, request, pk):
        tenant = request.hrm_tenant
        log = get_object_or_404(
            AttendanceLog.objects.filter(tenant=tenant),
            pk=pk,
        )
        action = request.POST.get("action")
        note = (request.POST.get("note") or "").strip()
        log.review_note = note
        log.reviewed_by = request.user
        from django.utils import timezone as dj_tz

        log.reviewed_at = dj_tz.now()
        if action == "approve":
            log.validation_status = AttendanceLog.ValidationStatus.OVERRIDE_OK
            log.review_status = "approved"
            log.requires_review = False
            messages.success(request, "Punch approved (override).")
        else:
            log.review_status = "rejected"
            log.requires_review = False
            messages.info(request, "Review closed as rejected.")
        log.save()
        return redirect("hrm:attendance_review_list")


location_policy = LocationPolicyEditView.as_view()
location_attendance_report = LocationAttendanceReportView.as_view()
attendance_review_list = AttendanceReviewListView.as_view()
attendance_review_action = AttendanceReviewApproveView.as_view()
