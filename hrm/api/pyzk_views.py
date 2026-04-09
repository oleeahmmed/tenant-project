from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from hrm.models import DeviceUser, ZKDevice
from hrm.utils import (
    ZKDeviceConnection,
    auto_create_employee_from_device_user,
    error_response,
    import_attendance_from_device,
    import_users_from_device,
    success_response,
)
from hrm.tenant_scope import get_hrm_tenant
from hrm.utils.api_utils import get_date_range as get_date_range_util

from .pyzk_serializers import PyZKAttendanceFetchSerializer, PyZKUserFetchSerializer
from .permissions import IsHrmTenantAdmin


def _device(request, device_id):
    t = get_hrm_tenant(request)
    if t is None:
        from django.http import Http404

        raise Http404()
    return get_object_or_404(ZKDevice, pk=device_id, tenant_id=t.id)


class PyZKFetchUsersView(APIView):
    permission_classes = [IsHrmTenantAdmin]

    def post(self, request, device_id):
        device = _device(request, device_id)
        if not device.supports_tcp():
            return Response(
                error_response("Device does not support TCP (PyZK)"),
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = PyZKUserFetchSerializer(data=request.data)
        if not ser.is_valid():
            return Response(
                error_response("Invalid parameters", errors=ser.errors),
                status=status.HTTP_400_BAD_REQUEST,
            )
        import_new = ser.validated_data.get("import_new", True)
        auto_create = ser.validated_data.get("auto_create_employees", True)

        if import_new:
            result = import_users_from_device(device)
            if auto_create and result.get("success") and result.get("imported", 0) > 0:
                n = 0
                for du in DeviceUser.objects.filter(device=device):
                    if auto_create_employee_from_device_user(du):
                        n += 1
                result["employees_created"] = n
            if result.get("success"):
                return Response(success_response(data=result))
            return Response(
                error_response(result.get("error", "Failed"), data=result),
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            with ZKDeviceConnection(
                ip=str(device.ip_address),
                port=device.port,
                timeout=device.tcp_timeout,
                password=int(device.tcp_password) if str(device.tcp_password or "").isdigit() else 0,
            ) as conn:
                users = conn.get_users()
                users_data = [
                    {
                        "user_id": str(u.user_id),
                        "name": getattr(u, "name", "") or "",
                        "privilege": getattr(u, "privilege", 0) or 0,
                        "card_number": str(u.card) if getattr(u, "card", None) else "",
                    }
                    for u in users
                ]
                return Response(
                    success_response(
                        message=f"Fetched {len(users)} users",
                        data={"total": len(users), "users": users_data},
                    )
                )
        except Exception as e:
            return Response(
                error_response(str(e)),
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class PyZKImportUsersView(APIView):
    permission_classes = [IsHrmTenantAdmin]

    def post(self, request, device_id):
        device = _device(request, device_id)
        if not device.supports_tcp():
            return Response(
                error_response("Device does not support TCP (PyZK)"),
                status=status.HTTP_400_BAD_REQUEST,
            )
        auto_create = request.data.get("auto_create_employees", True)
        result = import_users_from_device(device)
        if auto_create and result.get("success"):
            n = 0
            for du in DeviceUser.objects.filter(device=device):
                if auto_create_employee_from_device_user(du):
                    n += 1
            result["employees_created"] = n
        if result.get("success"):
            return Response(success_response(data=result))
        return Response(
            error_response(result.get("error", "Import failed"), data=result),
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class PyZKFetchAttendanceView(APIView):
    permission_classes = [IsHrmTenantAdmin]

    def post(self, request, device_id):
        device = _device(request, device_id)
        if not device.supports_tcp():
            return Response(
                error_response("Device does not support TCP (PyZK)"),
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = PyZKAttendanceFetchSerializer(data=request.data)
        if not ser.is_valid():
            return Response(
                error_response("Invalid parameters", errors=ser.errors),
                status=status.HTTP_400_BAD_REQUEST,
            )
        dr = ser.validated_data.get("date_range", "today")
        uid_f = ser.validated_data.get("user_id")
        import_new = ser.validated_data.get("import_new", True)

        if dr == "custom":
            date_from = ser.validated_data.get("date_from")
            date_to = ser.validated_data.get("date_to")
        else:
            date_from, date_to = get_date_range_util(dr)

        if import_new:
            result = import_attendance_from_device(device, date_from, date_to, uid_f)
            result["date_range"] = {"from": str(date_from), "to": str(date_to)}
            if result.get("success"):
                return Response(success_response(data=result))
            return Response(
                error_response(result.get("error", "Failed"), data=result),
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            with ZKDeviceConnection(
                ip=str(device.ip_address),
                port=device.port,
                timeout=device.tcp_timeout,
                password=int(device.tcp_password) if str(device.tcp_password or "").isdigit() else 0,
            ) as conn:
                attendance = conn.get_attendance()
                filtered = []
                for record in attendance:
                    ts = getattr(record, "timestamp", None)
                    if not ts:
                        continue
                    if date_from and ts.date() < date_from:
                        continue
                    if date_to and ts.date() > date_to:
                        continue
                    if uid_f and str(getattr(record, "user_id", "")) != str(uid_f):
                        continue
                    filtered.append(
                        {
                            "user_id": str(record.user_id),
                            "punch_time": ts.isoformat(),
                            "punch_type": getattr(record, "punch", 0),
                            "verify_type": getattr(record, "status", 1),
                        }
                    )
                return Response(
                    success_response(
                        data={
                            "total": len(filtered),
                            "date_range": {"from": str(date_from), "to": str(date_to)},
                            "records": filtered,
                        }
                    )
                )
        except Exception as e:
            return Response(error_response(str(e)), status=status.HTTP_503_SERVICE_UNAVAILABLE)


class PyZKImportAttendanceView(APIView):
    permission_classes = [IsHrmTenantAdmin]

    def post(self, request, device_id):
        device = _device(request, device_id)
        if not device.supports_tcp():
            return Response(
                error_response("Device does not support TCP (PyZK)"),
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = import_attendance_from_device(device)
        if result.get("success"):
            return Response(success_response(data=result))
        return Response(
            error_response(result.get("error", "Import failed"), data=result),
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
