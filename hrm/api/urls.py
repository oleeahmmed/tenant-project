from django.urls import path

from . import location_views, pyzk_views

app_name = "hrm_api"

urlpatterns = [
    path("mobile/check-in/", location_views.EmployeeMobileCheckinView.as_view(), name="mobile_checkin"),
    path("mobile/location-policy/", location_views.LocationPolicyInfoView.as_view(), name="mobile_location_policy"),
    path(
        "pyzk/devices/<int:device_id>/fetch-users/",
        pyzk_views.PyZKFetchUsersView.as_view(),
        name="pyzk_fetch_users",
    ),
    path(
        "pyzk/devices/<int:device_id>/import-users/",
        pyzk_views.PyZKImportUsersView.as_view(),
        name="pyzk_import_users",
    ),
    path(
        "pyzk/devices/<int:device_id>/fetch-attendance/",
        pyzk_views.PyZKFetchAttendanceView.as_view(),
        name="pyzk_fetch_attendance",
    ),
    path(
        "pyzk/devices/<int:device_id>/import-attendance/",
        pyzk_views.PyZKImportAttendanceView.as_view(),
        name="pyzk_import_attendance",
    ),
]
