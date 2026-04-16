from django.urls import path

from . import views

app_name = "screenhot_api"

urlpatterns = [
    path("projects/", views.ProjectOptionsView.as_view(), name="project_options"),
    path("departments/", views.DepartmentOptionsView.as_view(), name="department_options"),
    path("employees/", views.EmployeeOptionsView.as_view(), name="employee_options"),
    path("live-monitor/", views.LiveMonitorView.as_view(), name="live_monitor"),
    path("screenshots/upload/", views.ScreenshotUploadView.as_view(), name="screenshot_upload"),
    path("screenshots/", views.ScreenshotListView.as_view(), name="screenshot_list"),
    path("screenshots/<int:screenshot_id>/", views.ScreenshotDeleteView.as_view(), name="screenshot_delete"),
    path("attendance/checkin/", views.AttendanceCheckInView.as_view(), name="attendance_checkin"),
    path("attendance/checkout/", views.AttendanceCheckOutView.as_view(), name="attendance_checkout"),
    path("attendance/activity/", views.AttendanceActivityView.as_view(), name="attendance_activity"),
    path("attendance/current/", views.AttendanceCurrentView.as_view(), name="attendance_current"),
    path("attendance/", views.AttendanceListView.as_view(), name="attendance_list"),
    path("attendance/<int:attendance_id>/", views.AttendanceDeleteView.as_view(), name="attendance_delete"),
    path("video/generate/", views.VideoGenerateView.as_view(), name="video_generate"),
    path("video/status/<int:job_id>/", views.VideoStatusView.as_view(), name="video_status"),
    path("video/jobs/", views.VideoJobListView.as_view(), name="video_jobs"),
    path("video/jobs/<int:job_id>/", views.VideoJobDeleteView.as_view(), name="video_job_delete"),
]
