"""
Server-side GPS / geofence validation for mobile attendance.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from django.utils import timezone

from hrm.models import (
    AttendanceLocation,
    AttendanceLog,
    Employee,
    Holiday,
    LocationAttendancePolicy,
)
from hrm.utils.geo import haversine_m


def get_or_create_location_policy(tenant) -> LocationAttendancePolicy:
    obj, _ = LocationAttendancePolicy.objects.get_or_create(
        tenant=tenant,
        defaults={},
    )
    return obj


def _is_holiday(tenant, d: dt.date) -> bool:
    return Holiday.objects.filter(
        tenant=tenant,
        start_date__lte=d,
        end_date__gte=d,
    ).exists()


def _time_to_minutes(t: dt.time) -> int:
    return t.hour * 60 + t.minute


def _punch_in_location_window(
    punch_local: dt.datetime,
    loc: AttendanceLocation,
    policy: LocationAttendancePolicy,
) -> bool:
    t = timezone.localtime(punch_local).time()
    wd = timezone.localtime(punch_local).weekday()
    if wd not in loc.weekday_set():
        return False
    if loc.window_start is None and loc.window_end is None:
        return True
    if loc.window_start is None or loc.window_end is None:
        return True
    pm = _time_to_minutes(t)
    start = _time_to_minutes(loc.window_start)
    end = _time_to_minutes(loc.window_end)
    early = policy.early_checkin_minutes
    late = policy.late_checkin_minutes
    start_e = max(0, start - early)
    end_e = min(24 * 60 - 1, end + late)
    if start <= end:
        return start_e <= pm <= end_e
    return pm >= start_e or pm <= end_e


@dataclass
class CheckinResult:
    ok: bool
    status: str
    matched_location: AttendanceLocation | None
    distance_m: float | None
    message: str
    log_defaults: dict[str, Any]


def persist_mobile_attendance_log(defaults: dict[str, Any]) -> AttendanceLog:
    tenant = defaults.pop("tenant")
    uid = defaults.pop("user_id")
    pt = defaults.pop("punch_time")
    defaults.setdefault("device", None)
    log, _ = AttendanceLog.objects.update_or_create(
        tenant=tenant,
        user_id=str(uid),
        punch_time=pt,
        device=None,
        defaults=defaults,
    )
    return log


def process_mobile_checkin(
    *,
    tenant,
    employee: Employee,
    latitude: float | None,
    longitude: float | None,
    accuracy: float | None,
    punch_time: dt.datetime,
    punch_type: int = 0,
) -> CheckinResult:
    policy = get_or_create_location_policy(tenant)
    uid = (employee.zk_user_id or "").strip() or employee.employee_code
    punch_local = punch_time
    if timezone.is_naive(punch_local):
        punch_local = timezone.make_aware(punch_local, timezone.get_current_timezone())

    d = timezone.localdate(punch_local)

    if latitude is None or longitude is None:
        if (
            policy.checkin_mode == "remote_allowed"
            and employee.work_location_mode == "remote"
            and policy.allow_remote_clock_without_gps
        ):
            return CheckinResult(
                True,
                AttendanceLog.ValidationStatus.REMOTE_NO_GPS,
                None,
                None,
                "Remote clock without GPS (policy allows).",
                {
                    "tenant": tenant,
                    "device": None,
                    "employee": employee,
                    "user_id": str(uid),
                    "punch_time": punch_local,
                    "punch_type": punch_type,
                    "verify_type": AttendanceLog.VerifyType.FACE,
                    "source": AttendanceLog.Source.MOBILE,
                    "validation_status": AttendanceLog.ValidationStatus.REMOTE_NO_GPS,
                    "requires_review": False,
                },
            )
        return CheckinResult(
            False,
            AttendanceLog.ValidationStatus.OUT_OF_GEOFENCE,
            None,
            None,
            "Latitude and longitude are required, or set employee to Remote with policy allowing no GPS.",
            {},
        )

    lat_f = float(latitude)
    lon_f = float(longitude)

    if policy.max_accuracy_meters and policy.max_accuracy_meters > 0:
        if accuracy is None or accuracy > policy.max_accuracy_meters:
            return CheckinResult(
                False,
                AttendanceLog.ValidationStatus.LOW_ACCURACY,
                None,
                None,
                f"GPS accuracy too poor (max {policy.max_accuracy_meters} m).",
                {
                    "tenant": tenant,
                    "device": None,
                    "employee": employee,
                    "user_id": str(uid),
                    "punch_time": punch_local,
                    "punch_type": punch_type,
                    "verify_type": AttendanceLog.VerifyType.FACE,
                    "source": AttendanceLog.Source.MOBILE,
                    "latitude": lat_f,
                    "longitude": lon_f,
                    "location_accuracy": accuracy,
                    "validation_status": AttendanceLog.ValidationStatus.LOW_ACCURACY,
                    "requires_review": True,
                    "review_status": "pending",
                },
            )

    links = list(
        employee.attendance_locations.select_related("location").filter(
            location__is_active=True,
            location__tenant=tenant,
        )
    )
    if not links:
        invalid = {
            "tenant": tenant,
            "device": None,
            "employee": employee,
            "user_id": str(uid),
            "punch_time": punch_local,
            "punch_type": punch_type,
            "verify_type": AttendanceLog.VerifyType.FACE,
            "source": AttendanceLog.Source.MOBILE,
            "latitude": lat_f,
            "longitude": lon_f,
            "location_accuracy": accuracy,
            "validation_status": AttendanceLog.ValidationStatus.OUT_OF_GEOFENCE,
            "requires_review": True,
            "review_status": "pending",
        }
        return CheckinResult(
            False,
            AttendanceLog.ValidationStatus.OUT_OF_GEOFENCE,
            None,
            None,
            "No geofence assigned to this employee.",
            invalid,
        )

    best_loc: AttendanceLocation | None = None
    best_dist: float | None = None

    for link in links:
        loc = link.location
        if _is_holiday(tenant, d) and getattr(loc, "exclude_holidays", True):
            continue
        if not _punch_in_location_window(punch_local, loc, policy):
            continue
        dist = haversine_m(
            lat_f,
            lon_f,
            float(loc.latitude),
            float(loc.longitude),
        )
        if dist <= loc.radius_m:
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_loc = loc

    if best_loc is not None:
        return CheckinResult(
            True,
            AttendanceLog.ValidationStatus.VALID,
            best_loc,
            best_dist,
            "Inside geofence.",
            {
                "tenant": tenant,
                "device": None,
                "employee": employee,
                "user_id": str(uid),
                "punch_time": punch_local,
                "punch_type": punch_type,
                "verify_type": AttendanceLog.VerifyType.FACE,
                "source": AttendanceLog.Source.MOBILE,
                "latitude": lat_f,
                "longitude": lon_f,
                "location_accuracy": accuracy,
                "matched_location": best_loc,
                "distance_to_fence_m": best_dist,
                "validation_status": AttendanceLog.ValidationStatus.VALID,
                "requires_review": False,
            },
        )

    nearest = None
    for link in links:
        loc = link.location
        dist = haversine_m(
            lat_f,
            lon_f,
            float(loc.latitude),
            float(loc.longitude),
        )
        if nearest is None or dist < nearest:
            nearest = dist

    invalid_defaults = {
        "tenant": tenant,
        "device": None,
        "employee": employee,
        "user_id": str(uid),
        "punch_time": punch_local,
        "punch_type": punch_type,
        "verify_type": AttendanceLog.VerifyType.FACE,
        "source": AttendanceLog.Source.MOBILE,
        "latitude": lat_f,
        "longitude": lon_f,
        "location_accuracy": accuracy,
        "distance_to_fence_m": nearest,
        "validation_status": AttendanceLog.ValidationStatus.OUT_OF_GEOFENCE,
        "requires_review": True,
        "review_status": "pending",
    }

    return CheckinResult(
        False,
        AttendanceLog.ValidationStatus.OUT_OF_GEOFENCE,
        None,
        nearest,
        "Outside all allowed geofences or outside time window.",
        invalid_defaults,
    )
