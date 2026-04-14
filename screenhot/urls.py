from django.urls import path

from . import views

app_name = "screenhot"

urlpatterns = [
    path("", views.ScreenhotDashboardView.as_view(), name="dashboard"),
    path("live-monitor/", views.ScreenhotLiveMonitorPageView.as_view(), name="live_monitor_page"),
    path("screenshots/", views.ScreenhotScreenshotListPageView.as_view(), name="screenshot_list_page"),
    path("attendance/", views.ScreenhotAttendanceListPageView.as_view(), name="attendance_list_page"),
    path("videos/", views.ScreenhotVideoJobListPageView.as_view(), name="video_job_list_page"),
]
