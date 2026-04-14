from django.views.generic import TemplateView

from .mixins import ScreenhotDashboardAccessMixin, ScreenhotPageContextMixin
from .models import AttendanceRecord, ScreenshotRecord, VideoJob


class ScreenhotDashboardView(ScreenhotDashboardAccessMixin, ScreenhotPageContextMixin, TemplateView):
    template_name = "screenhot/dashboard.html"
    page_title = "Screenhot"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "hrm_tenant", None)
        if tenant is None:
            ctx["stats"] = {"screenshots": 0, "attendance_open": 0, "video_jobs": 0}
            return ctx
        ctx["stats"] = {
            "screenshots": ScreenshotRecord.objects.filter(tenant=tenant).count(),
            "attendance_open": AttendanceRecord.objects.filter(tenant=tenant, check_out__isnull=True).count(),
            "video_jobs": VideoJob.objects.filter(tenant=tenant).count(),
        }
        return ctx


class ScreenhotScreenshotListPageView(ScreenhotDashboardAccessMixin, ScreenhotPageContextMixin, TemplateView):
    template_name = "screenhot/screenshot_list.html"
    page_title = "Screenshots"


class ScreenhotAttendanceListPageView(ScreenhotDashboardAccessMixin, ScreenhotPageContextMixin, TemplateView):
    template_name = "screenhot/attendance_list.html"
    page_title = "Attendance"


class ScreenhotVideoJobListPageView(ScreenhotDashboardAccessMixin, ScreenhotPageContextMixin, TemplateView):
    template_name = "screenhot/video_job_list.html"
    page_title = "Video jobs"


class ScreenhotLiveMonitorPageView(ScreenhotDashboardAccessMixin, ScreenhotPageContextMixin, TemplateView):
    template_name = "screenhot/live_monitor.html"
    page_title = "Live monitor"
