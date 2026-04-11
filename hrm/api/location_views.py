from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from hrm.services.location_checkin import (
    get_or_create_location_policy,
    persist_mobile_attendance_log,
    process_mobile_checkin,
    sync_daily_record_from_log,
)
from hrm.tenant_scope import get_hrm_tenant

from .location_serializers import MobileCheckinSerializer


class EmployeeMobileCheckinView(APIView):
    """
    POST /api/hrm/mobile/check-in/
    JWT user must have an HRM Employee profile on the same tenant.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"success": False, "message": "No tenant assigned."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            emp = user.hrm_employee_profile
        except ObjectDoesNotExist:
            emp = None
        if emp is None or emp.tenant_id != tenant.id:
            return Response(
                {
                    "success": False,
                    "message": "No employee profile linked to this account.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        ser = MobileCheckinSerializer(data=request.data)
        if not ser.is_valid():
            return Response(
                {"success": False, "errors": ser.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        d = ser.validated_data
        pt = d.get("punch_time") or timezone.now()
        policy = get_or_create_location_policy(tenant)

        result = process_mobile_checkin(
            tenant=tenant,
            employee=emp,
            latitude=d.get("latitude"),
            longitude=d.get("longitude"),
            accuracy=d.get("accuracy"),
            punch_time=pt,
            punch_type=d.get("punch_type", 0),
        )

        if not result.ok and policy.reject_api_when_invalid:
            return Response(
                {
                    "success": False,
                    "message": result.message,
                    "validation_status": result.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if result.ok or (result.log_defaults and policy.record_invalid_attempts):
            log = persist_mobile_attendance_log(dict(result.log_defaults))
            if result.ok:
                sync_daily_record_from_log(emp, log)
            return Response(
                {
                    "success": result.ok,
                    "message": result.message,
                    "validation_status": log.validation_status,
                    "log_id": log.pk,
                    "matched_location": (
                        log.matched_location.name if log.matched_location_id else None
                    ),
                    "distance_m": log.distance_to_fence_m,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "message": result.message,
                "validation_status": result.status,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class LocationPolicyInfoView(APIView):
    """GET — current tenant GPS policy (for mobile apps)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response({"detail": "No tenant"}, status=403)
        p = get_or_create_location_policy(tenant)
        return Response(
            {
                "checkin_mode": p.checkin_mode,
                "max_accuracy_meters": p.max_accuracy_meters,
                "early_checkin_minutes": p.early_checkin_minutes,
                "late_checkin_minutes": p.late_checkin_minutes,
                "allow_remote_clock_without_gps": p.allow_remote_clock_without_gps,
            }
        )
