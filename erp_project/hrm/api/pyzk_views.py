# ==================== zktest/api/pyzk_views.py ====================
"""
PyZK (TCP) API Views
Handles old ZKTeco devices via TCP/IP connection using pyzk library
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from hrm.models import ZKDevice, DeviceUser
from .pyzk_serializers import (
    PyZKUserFetchSerializer,
    PyZKAttendanceFetchSerializer,
)
from hrm.utils import (
    import_users_from_device,
    import_attendance_from_device,
    get_date_range,
    success_response,
    error_response,
    auto_create_employee_from_device_user,
    ZKDeviceConnection,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PyZK API Views
# =============================================================================

class PyZKFetchUsersView(APIView):
    """
    Fetch users from device via TCP
    POST /api/pyzk/devices/<device_id>/fetch-users/
    
    Body:
    {
        "import_new": true,
        "auto_create_employees": true
    }
    """
    
    def post(self, request, device_id):
        try:
            device = ZKDevice.objects.get(pk=device_id)
            
            if not device.supports_tcp():
                return Response(
                    error_response('Device does not support TCP connection'),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = PyZKUserFetchSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    error_response('Invalid parameters', errors=serializer.errors),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            import_new = serializer.validated_data.get('import_new', True)
            auto_create_employees = serializer.validated_data.get('auto_create_employees', True)
            
            # Fetch and optionally import
            if import_new:
                result = import_users_from_device(device)
                
                # Auto-create employees
                if auto_create_employees and result.get('success') and result['imported'] > 0:
                    employees_created = 0
                    new_users = DeviceUser.objects.filter(device=device)
                    
                    for du in new_users:
                        emp = auto_create_employee_from_device_user(du)
                        if emp:
                            employees_created += 1
                    
                    result['employees_created'] = employees_created
                
                if result.get('success'):
                    return Response(success_response(
                        message=f"Fetched {result['total']} users, imported {result['imported']} new users",
                        data=result
                    ))
                else:
                    return Response(
                        error_response(result.get('error', 'Fetch failed'), data=result),
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
            else:
                # Just fetch, don't import
                try:
                    with ZKDeviceConnection(
                        ip=device.ip_address,
                        port=device.port,
                        timeout=device.tcp_timeout,
                        password=int(device.tcp_password) if device.tcp_password else 0
                    ) as conn:
                        users = conn.get_users()
                        
                        users_data = [{
                            'user_id': str(u.user_id),
                            'name': u.name or '',
                            'privilege': u.privilege or 0,
                            'card_number': str(u.card) if u.card else ''
                        } for u in users]
                        
                        return Response(success_response(
                            message=f'Fetched {len(users)} users from device',
                            data={'total': len(users), 'users': users_data}
                        ))
                        
                except Exception as e:
                    return Response(
                        error_response(f'Failed to fetch users: {str(e)}'),
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                
        except ZKDevice.DoesNotExist:
            return Response(
                error_response('Device not found'),
                status=status.HTTP_404_NOT_FOUND
            )


class PyZKImportUsersView(APIView):
    """
    Import users from device (explicit import)
    POST /api/pyzk/devices/<device_id>/import-users/
    
    Body:
    {
        "auto_create_employees": true
    }
    """
    
    def post(self, request, device_id):
        try:
            device = ZKDevice.objects.get(pk=device_id)
            
            if not device.supports_tcp():
                return Response(
                    error_response('Device does not support TCP connection'),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            auto_create_employees = request.data.get('auto_create_employees', True)
            
            # Import users
            result = import_users_from_device(device)
            
            # Auto-create employees
            if auto_create_employees and result.get('success') and result['imported'] > 0:
                employees_created = 0
                new_users = DeviceUser.objects.filter(device=device)
                
                for du in new_users:
                    emp = auto_create_employee_from_device_user(du)
                    if emp:
                        employees_created += 1
                
                result['employees_created'] = employees_created
            
            if result.get('success'):
                return Response(success_response(
                    message=f"Imported {result['imported']} new users",
                    data=result
                ))
            else:
                return Response(
                    error_response(result.get('error', 'Import failed'), data=result),
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
        except ZKDevice.DoesNotExist:
            return Response(
                error_response('Device not found'),
                status=status.HTTP_404_NOT_FOUND
            )


class PyZKFetchAttendanceView(APIView):
    """
    Fetch attendance from device via TCP
    POST /api/pyzk/devices/<device_id>/fetch-attendance/
    
    Body:
    {
        "date_range": "today|7days|30days|month|custom",
        "date_from": "2024-01-01",
        "date_to": "2024-01-31",
        "user_id": "123",
        "import_new": true
    }
    """
    
    def post(self, request, device_id):
        try:
            device = ZKDevice.objects.get(pk=device_id)
            
            if not device.supports_tcp():
                return Response(
                    error_response('Device does not support TCP connection'),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = PyZKAttendanceFetchSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    error_response('Invalid parameters', errors=serializer.errors),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            date_range_type = serializer.validated_data.get('date_range', 'today')
            user_id_filter = serializer.validated_data.get('user_id')
            import_new = serializer.validated_data.get('import_new', True)
            
            # Get date range
            if date_range_type == 'custom':
                date_from = serializer.validated_data.get('date_from')
                date_to = serializer.validated_data.get('date_to')
            else:
                date_from, date_to = get_date_range(date_range_type)
            
            # Fetch and optionally import
            if import_new:
                result = import_attendance_from_device(device, date_from, date_to, user_id_filter)
                result['date_range'] = {'from': str(date_from), 'to': str(date_to)}
                
                if result.get('success'):
                    return Response(success_response(
                        message=f"Fetched {result['total']} records, imported {result['imported']} new records",
                        data=result
                    ))
                else:
                    return Response(
                        error_response(result.get('error', 'Fetch failed'), data=result),
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
            else:
                # Just fetch, don't import
                try:
                    with ZKDeviceConnection(
                        ip=device.ip_address,
                        port=device.port,
                        timeout=device.tcp_timeout,
                        password=int(device.tcp_password) if device.tcp_password else 0
                    ) as conn:
                        attendance = conn.get_attendance()
                        
                        # Filter
                        filtered = []
                        for record in attendance:
                            if date_from and record.timestamp.date() < date_from:
                                continue
                            if date_to and record.timestamp.date() > date_to:
                                continue
                            if user_id_filter and str(record.user_id) != user_id_filter:
                                continue
                            
                            filtered.append({
                                'user_id': str(record.user_id),
                                'punch_time': record.timestamp.isoformat(),
                                'punch_type': record.punch if hasattr(record, 'punch') else 0,
                                'verify_type': record.status if hasattr(record, 'status') else 1,
                            })
                        
                        return Response(success_response(
                            message=f'Fetched {len(filtered)} attendance records',
                            data={
                                'total': len(filtered),
                                'date_range': {'from': str(date_from), 'to': str(date_to)},
                                'records': filtered
                            }
                        ))
                        
                except Exception as e:
                    return Response(
                        error_response(f'Failed to fetch attendance: {str(e)}'),
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                
        except ZKDevice.DoesNotExist:
            return Response(
                error_response('Device not found'),
                status=status.HTTP_404_NOT_FOUND
            )


class PyZKImportAttendanceView(APIView):
    """
    Import ALL attendance from device (explicit import)
    POST /api/pyzk/devices/<device_id>/import-attendance/
    
    Body:
    {
        "clear_after_sync": false
    }
    """
    
    def post(self, request, device_id):
        try:
            device = ZKDevice.objects.get(pk=device_id)
            
            if not device.supports_tcp():
                return Response(
                    error_response('Device does not support TCP connection'),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            clear_after_sync = request.data.get('clear_after_sync', False)
            
            # Import all attendance
            result = import_attendance_from_device(device)
            
            # Clear device if requested
            if clear_after_sync and result.get('success') and result['imported'] > 0:
                try:
                    with ZKDeviceConnection(
                        ip=device.ip_address,
                        port=device.port,
                        timeout=device.tcp_timeout,
                        password=int(device.tcp_password) if device.tcp_password else 0
                    ) as conn:
                        conn.clear_attendance()
                        result['device_cleared'] = True
                        logger.info(f"[PyZK] Cleared attendance on device after sync")
                except Exception as e:
                    result['clear_error'] = str(e)
            
            if result.get('success'):
                return Response(success_response(
                    message=f"Imported {result['imported']} new attendance records",
                    data=result
                ))
            else:
                return Response(
                    error_response(result.get('error', 'Import failed'), data=result),
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
        except ZKDevice.DoesNotExist:
            return Response(
                error_response('Device not found'),
                status=status.HTTP_404_NOT_FOUND
            )
