import logging
import base64
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.db import IntegrityError
from django.db.models import Count, Min, Max, Q
from django.db.models.functions import TruncDate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

from hrm.models import (
    ZKDevice, AttendanceLog, DeviceUser, 
    DeviceCommand, OperationLog, DeviceHeartbeat,
    FingerprintTemplate, FaceTemplate
)
from .serializers import (
    ZKDeviceSerializer, ZKDeviceListSerializer, ZKDeviceCreateSerializer,
    AttendanceLogSerializer, DeviceUserSerializer,
    DeviceCommandSerializer, OperationLogSerializer,
    DeviceHeartbeatSerializer, FingerprintTemplateSerializer, FaceTemplateSerializer
)
logger = logging.getLogger(__name__)


# =============================================================================
# ADMS Protocol Handler - Main Endpoint
# =============================================================================

class ADMSHandlerView(APIView):
    """
    ZKTeco ADMS/iclock Protocol Handler
    
    Handles all ADMS device communication:
    - GET /iclock/cdata - Device handshake & get commands
    - POST /iclock/cdata - Attendance push, User sync, Operation logs
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Device Handshake & Command Retrieval"""
        sn = request.GET.get('SN', '')
        
        if not sn:
            return HttpResponse('ERROR: No SN', content_type='text/plain')
        
        device = self._get_or_create_device(request, sn)
        
        # Record heartbeat
        self._record_heartbeat(request, device)
        
        # Check for pending commands
        pending_command = self._get_pending_command(device)
        
        if pending_command:
            return self._format_command_response(pending_command)
        
        # Standard OK response with settings
        response_lines = [
            f'GET OPTION FROM: {sn}',
            f'Stamp={int(datetime.now().timestamp())}',
            f'OpStamp={int(datetime.now().timestamp())}',
            'PhotoStamp=0',
            'ErrorDelay=60',
            'Delay=30',
            'TransTimes=00:00;23:59',
            'TransInterval=1',
            'TransFlag=TransData AttLog OpLog EnrollUser EnrollFP UserPic Face',
            'Realtime=1',
            'Encrypt=0',
            'ServerVer=2.4.1',
            'PushProtVer=2.4.1',
        ]
        
        return HttpResponse('\r\n'.join(response_lines), content_type='text/plain')
    
    def post(self, request):
        """Data Push Handler"""
        sn = request.GET.get('SN', '')
        table = request.GET.get('table', '').upper()
        
        if not sn:
            return HttpResponse('ERROR: No SN', content_type='text/plain')
        
        device = self._get_or_create_device(request, sn)
        
        # Update device activity
        device.update_activity()
        
        handlers = {
            'ATTLOG': self._handle_attendance,
            'OPERLOG': self._handle_operation_log,
            'USER': self._handle_user_sync,
            'USERINFO': self._handle_user_sync,
            'FINGERTMP': self._handle_fingerprint,
            'TEMPLATEV10': self._handle_fingerprint,
            'FACE': self._handle_face,
            'BIODATA': self._handle_biodata,
            'USERPIC': self._handle_user_photo,
            'FIRSTDATA': self._handle_first_data,
            'ATTPHOTO': self._handle_attendance_photo,
            'OPTIONS': self._handle_options,
        }
        
        handler = handlers.get(table, self._handle_unknown)
        
        try:
            result = handler(request, device)
            logger.info(f"[ADMS] {sn} - {table}: {result}")
            return HttpResponse('OK', content_type='text/plain')
        except Exception as e:
            logger.error(f"[ADMS] {sn} - {table} Error: {str(e)}")
            return HttpResponse('OK', content_type='text/plain')
    
    def _get_or_create_device(self, request, sn):
        """Get or register device"""
        client_ip = self._get_client_ip(request)
        
        defaults = {
            'ip_address': client_ip,
            'last_activity': timezone.now(),
            'is_online': True,
            'push_version': request.GET.get('pushver', ''),
            'firmware_version': request.GET.get('Ver', ''),
        }
        
        # Parse additional device info from request
        options = request.GET.get('options', '')
        if options:
            self._parse_device_options(options, defaults)
        
        device, created = ZKDevice.objects.update_or_create(
            serial_number=sn,
            defaults=defaults
        )
        
        if created:
            logger.info(f"[ADMS] New device registered: {sn} from {client_ip}")
        
        return device
    
    def _parse_device_options(self, options, defaults):
        """Parse device options string"""
        try:
            parts = options.split(',')
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'UserCount':
                        defaults['user_count'] = int(value)
                    elif key == 'FPCount':
                        defaults['fp_count'] = int(value)
                    elif key == 'FaceCount':
                        defaults['face_count'] = int(value)
                    elif key == 'AttLogCount':
                        defaults['transaction_count'] = int(value)
                    elif key == 'Platform':
                        defaults['platform'] = value
                    elif key == 'OEMVendor':
                        defaults['oem_vendor'] = value
        except Exception as e:
            logger.warning(f"Error parsing device options: {e}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    def _record_heartbeat(self, request, device):
        """Record device heartbeat"""
        try:
            DeviceHeartbeat.objects.create(
                device=device,
                ip_address=self._get_client_ip(request),
                user_count=device.user_count,
                fp_count=device.fp_count,
                face_count=device.face_count,
                log_count=device.transaction_count,
            )
        except Exception as e:
            logger.warning(f"Error recording heartbeat: {e}")
    
    def _get_pending_command(self, device):
        """Get pending command"""
        return DeviceCommand.objects.filter(
            device=device,
            status='pending'
        ).order_by('created_at').first()
    
    def _format_command_response(self, command):
        """Format command for device"""
        command_map = {
            'REBOOT': f'C:{command.id}:REBOOT',
            'CLEAR_LOG': f'C:{command.id}:CLEAR LOG',
            'CLEAR_DATA': f'C:{command.id}:CLEAR DATA',
            'UPDATE_TIME': f'C:{command.id}:SET DATETIME {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'INFO': f'C:{command.id}:INFO',
            'CHECK': f'C:{command.id}:CHECK',
            'GET_USERS': f'C:{command.id}:DATA QUERY USERINFO',
            'GET_LOGS': f'C:{command.id}:DATA QUERY ATTLOG',
            'SET_USER': f'C:{command.id}:DATA UPDATE USERINFO {command.command_content}',
            'DEL_USER': f'C:{command.id}:DATA DELETE USERINFO {command.command_content}',
        }
        
        cmd_str = command_map.get(
            command.command_type, 
            f'C:{command.id}:{command.command_content}'
        )
        
        command.status = 'sent'
        command.sent_at = timezone.now()
        command.command_id = str(command.id)
        command.save()
        
        return HttpResponse(cmd_str, content_type='text/plain')
    
    def _handle_attendance(self, request, device):
        """Process attendance data"""
        body = request.body.decode('utf-8', errors='ignore')
        records_saved = 0
        
        for line in body.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                data = self._parse_attendance_line(line)
                if data:
                    AttendanceLog.objects.update_or_create(
                        device=device,
                        user_id=data['user_id'],
                        punch_time=data['punch_time'],
                        defaults={
                            'punch_type': data.get('punch_type', 0),
                            'verify_type': data.get('verify_type', 1),
                            'work_code': data.get('work_code', ''),
                            'temperature': data.get('temperature'),
                            'mask_status': data.get('mask_status', 0),
                            'raw_data': line,
                        }
                    )
                    records_saved += 1
            except IntegrityError:
                continue
            except Exception as e:
                logger.warning(f"Parse error: {line} - {str(e)}")
        
        # Update device transaction count
        device.transaction_count = device.attendance_logs.count()
        device.save(update_fields=['transaction_count'])
        
        return f"Saved {records_saved} attendance records"
    
    def _parse_attendance_line(self, line):
        """Parse attendance line - multiple formats supported"""
        parts = line.strip().split('\t')
        
        if len(parts) < 2:
            parts = line.strip().split()
        
        if len(parts) < 2:
            return None
        
        # Parse datetime
        time_str = parts[1]
        punch_time = None
        
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%d/%m/%Y %H:%M:%S']:
            try:
                punch_time = datetime.strptime(time_str, fmt)
                break
            except ValueError:
                continue
        
        if not punch_time and len(parts) >= 3:
            try:
                punch_time = datetime.strptime(f"{parts[1]} {parts[2]}", '%Y-%m-%d %H:%M:%S')
                parts = [parts[0], f"{parts[1]} {parts[2]}"] + parts[3:]
            except ValueError:
                pass
        
        if not punch_time:
            return None
        
        result = {
            'user_id': parts[0].strip(),
            'punch_time': punch_time,
            'punch_type': int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
            'verify_type': int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1,
            'work_code': parts[4] if len(parts) > 4 else '',
        }
        
        # Temperature (if available)
        if len(parts) > 6:
            try:
                temp = float(parts[6])
                if 30 < temp < 45:
                    result['temperature'] = temp
            except:
                pass
        
        return result
    
    def _handle_operation_log(self, request, device):
        """Process operation logs"""
        body = request.body.decode('utf-8', errors='ignore')
        count = 0
        
        for line in body.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    op_time = timezone.now()
                    try:
                        op_time = datetime.strptime(parts[2], '%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                    
                    # Map operation type
                    op_type_map = {
                        '0': 'OTHER',
                        '1': 'ENROLL',
                        '2': 'DELETE',
                        '3': 'UPDATE',
                        '4': 'ADMIN_LOGIN',
                        '5': 'ADMIN_LOGOUT',
                        '6': 'CLEAR',
                        '7': 'REBOOT',
                    }
                    op_type = op_type_map.get(parts[0], 'OTHER')
                    
                    OperationLog.objects.create(
                        device=device,
                        operation_type=op_type,
                        admin_id=parts[1] if len(parts) > 1 else '',
                        operation_time=op_time,
                        user_id=parts[3] if len(parts) > 3 else '',
                        raw_data=line,
                    )
                    count += 1
            except Exception as e:
                logger.warning(f"OpLog parse error: {line} - {str(e)}")
        
        return f"Saved {count} operation logs"
    

    def _handle_user_sync(self, request, device):
        """Sync user data from device"""
        body = request.body.decode('utf-8', errors='ignore')
        
        # <CHANGE> Debug: Log raw data to see what device is sending
        logger.info(f"[ADMS USER DEBUG] Device: {device.serial_number}")
        logger.info(f"[ADMS USER DEBUG] Raw body length: {len(body)}")
        logger.info(f"[ADMS USER DEBUG] Raw body: {body[:500]}")  # First 500 chars
        
        count = 0
        
        for line in body.strip().split('\n'):
            if not line.strip():
                continue
            
            # <CHANGE> Debug: Log each line
            logger.info(f"[ADMS USER DEBUG] Processing line: {line}")
            
            try:
                # ZKTeco sends data in different formats
                # Format 1: PIN\tName\tPri\tPasswd\tCard\tGrp
                # Format 2: USER PIN=xxx\tName=xxx\tPri=xxx
                
                if '=' in line:
                    # <CHANGE> Key=Value format handling
                    user_data = {}
                    pin = None
                    for part in line.replace('USER ', '').strip().split('\t'):
                        if '=' in part:
                            key, value = part.split('=', 1)
                            key = key.strip().upper()
                            value = value.strip()
                            if key == 'PIN':
                                pin = value
                            elif key == 'NAME':
                                user_data['name'] = value
                            elif key == 'PRI':
                                user_data['privilege'] = int(value) if value.isdigit() else 0
                            elif key == 'PASSWD':
                                user_data['password'] = value
                            elif key == 'CARD':
                                user_data['card_number'] = value
                            elif key == 'GRP':
                                user_data['group'] = value
                    
                    if pin:
                        DeviceUser.objects.update_or_create(
                            device=device,
                            user_id=pin,
                            defaults=user_data
                        )
                        count += 1
                        logger.info(f"[ADMS USER DEBUG] Saved user (key=value): {pin}")
                else:
                    # Tab-separated format
                    parts = line.strip().split('\t')
                    if parts and parts[0]:
                        user_data = {
                            'name': parts[1] if len(parts) > 1 else '',
                            'privilege': int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
                            'password': parts[3] if len(parts) > 3 else '',
                            'card_number': parts[4] if len(parts) > 4 else '',
                            'group': parts[5] if len(parts) > 5 else '1',
                        }
                        
                        DeviceUser.objects.update_or_create(
                            device=device,
                            user_id=parts[0].strip(),
                            defaults=user_data
                        )
                        count += 1
                        logger.info(f"[ADMS USER DEBUG] Saved user (tab): {parts[0]}")
                        
            except Exception as e:
                logger.warning(f"[ADMS USER DEBUG] Parse error: {line} - {str(e)}")
        
        # Update device user count
        device.user_count = device.users.count()
        device.save(update_fields=['user_count'])
        
        logger.info(f"[ADMS USER DEBUG] Total synced: {count} users")
        return f"Synced {count} users"
    
    def _handle_fingerprint(self, request, device):
        """Handle fingerprint template"""
        body = request.body.decode('utf-8', errors='ignore')
        count = 0
        
        for line in body.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    user_id = parts[0].strip()
                    finger_index = int(parts[1]) if parts[1].isdigit() else 0
                    
                    # Update user fingerprint status
                    DeviceUser.objects.filter(
                        device=device, user_id=user_id
                    ).update(has_fingerprint=True)
                    
                    # Store template if data available
                    if len(parts) >= 4:
                        template_data = parts[3] if len(parts) > 3 else ''
                        try:
                            binary_data = base64.b64decode(template_data) if template_data else None
                        except:
                            binary_data = template_data.encode() if template_data else None
                        
                        FingerprintTemplate.objects.update_or_create(
                            device=device,
                            user_id=user_id,
                            finger_index=finger_index,
                            defaults={
                                'template_data': binary_data,
                                'template_size': len(binary_data) if binary_data else 0,
                            }
                        )
                    count += 1
            except Exception as e:
                logger.warning(f"Fingerprint parse error: {line} - {str(e)}")
        
        device.fp_count = device.users.filter(has_fingerprint=True).count()
        device.save(update_fields=['fp_count'])
        return f"Received {count} fingerprint templates"
    
    def _handle_face(self, request, device):
        """Handle face template"""
        body = request.body.decode('utf-8', errors='ignore')
        count = 0
        
        for line in body.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    user_id = parts[0].strip()
                    face_index = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                    
                    DeviceUser.objects.filter(
                        device=device, user_id=user_id
                    ).update(has_face=True)
                    
                    # Store face template if data available
                    if len(parts) >= 3:
                        template_data = parts[2] if len(parts) > 2 else ''
                        try:
                            binary_data = base64.b64decode(template_data) if template_data else None
                        except:
                            binary_data = template_data.encode() if template_data else None
                        
                        FaceTemplate.objects.update_or_create(
                            device=device,
                            user_id=user_id,
                            face_index=face_index,
                            defaults={
                                'template_data': binary_data,
                                'template_size': len(binary_data) if binary_data else 0,
                            }
                        )
                    count += 1
            except Exception as e:
                logger.warning(f"Face parse error: {line} - {str(e)}")
        
        device.face_count = device.users.filter(has_face=True).count()
        device.save(update_fields=['face_count'])
        return f"Received {count} face templates"
    
    def _handle_biodata(self, request, device):
        """Handle biometric data (generic)"""
        return "Biodata received"
    
    def _handle_user_photo(self, request, device):
        return "User photo received"
    
    def _handle_attendance_photo(self, request, device):
        return "Attendance photo received"
    
    def _handle_first_data(self, request, device):
        return "First data received"
    
    def _handle_options(self, request, device):
        """Handle device options update"""
        body = request.body.decode('utf-8', errors='ignore')
        defaults = {}
        self._parse_device_options(body, defaults)
        
        if defaults:
            for key, value in defaults.items():
                setattr(device, key, value)
            device.save()
        
        return "Options updated"
    
    def _handle_unknown(self, request, device):
        table = request.GET.get('table', 'UNKNOWN')
        logger.warning(f"Unknown table type: {table}")
        return f"Unknown table: {table}"


class DeviceCommandAckView(APIView):
    """Command acknowledgment handler"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return self.post(request)
    
    def post(self, request):
        sn = request.GET.get('SN', '')
        cmd_id = request.GET.get('ID', '') or request.GET.get('id', '')
        cmd_return = request.GET.get('Return', '') or request.GET.get('return', '')
        
        if cmd_id:
            try:
                command = DeviceCommand.objects.get(id=int(cmd_id))
                command.status = 'executed' if cmd_return in ['0', ''] else 'failed'
                command.response = request.body.decode('utf-8', errors='ignore')
                command.return_value = int(cmd_return) if cmd_return.isdigit() else None
                command.executed_at = timezone.now()
                command.save()
                logger.info(f"[ADMS] Command {cmd_id} acknowledged: {command.status}")
            except DeviceCommand.DoesNotExist:
                logger.warning(f"[ADMS] Command {cmd_id} not found")
            except Exception as e:
                logger.error(f"[ADMS] Command ack error: {str(e)}")
        
        return HttpResponse('OK', content_type='text/plain')


# =============================================================================
# REST API Endpoints
# =============================================================================

class DeviceListView(APIView):
    """Device list and management"""
    
    def get(self, request):
        """Get all devices"""
        devices = ZKDevice.objects.all().order_by('-last_activity')
        
        # Filters
        is_active = request.GET.get('is_active')
        is_online = request.GET.get('is_online')
        device_type = request.GET.get('device_type')
        
        if is_active is not None:
            devices = devices.filter(is_active=is_active.lower() == 'true')
        if is_online is not None:
            five_min_ago = timezone.now() - timedelta(minutes=5)
            if is_online.lower() == 'true':
                devices = devices.filter(last_activity__gte=five_min_ago)
            else:
                devices = devices.filter(
                    Q(last_activity__lt=five_min_ago) | Q(last_activity__isnull=True)
                )
        if device_type:
            devices = devices.filter(device_type=device_type)
        
        serializer = ZKDeviceListSerializer(devices, many=True)
        return Response({
            'success': True,
            'count': devices.count(),
            'data': serializer.data
        })
    
    def post(self, request):
        """Manually add device"""
        serializer = ZKDeviceCreateSerializer(data=request.data)
        if serializer.is_valid():
            device = serializer.save()
            return Response({
                'success': True,
                'message': 'Device added successfully',
                'data': ZKDeviceSerializer(device).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DeviceDetailView(APIView):
    """Single device operations"""
    
    def get(self, request, pk):
        try:
            device = ZKDevice.objects.get(pk=pk)
            serializer = ZKDeviceSerializer(device)
            return Response({'success': True, 'data': serializer.data})
        except ZKDevice.DoesNotExist:
            return Response({
                'success': False, 
                'message': 'Device not found'
            }, status=404)
    
    def put(self, request, pk):
        try:
            device = ZKDevice.objects.get(pk=pk)
            serializer = ZKDeviceSerializer(device, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'success': True, 'data': serializer.data})
            return Response({
                'success': False, 
                'errors': serializer.errors
            }, status=400)
        except ZKDevice.DoesNotExist:
            return Response({
                'success': False, 
                'message': 'Device not found'
            }, status=404)
    
    def delete(self, request, pk):
        try:
            device = ZKDevice.objects.get(pk=pk)
            device.delete()
            return Response({'success': True, 'message': 'Device deleted'})
        except ZKDevice.DoesNotExist:
            return Response({
                'success': False, 
                'message': 'Device not found'
            }, status=404)


class AttendanceListView(APIView):
    """Attendance log API"""
    
    def get(self, request):
        """Get attendance logs with filters"""
        logs = AttendanceLog.objects.select_related('device').all()
        
        # Filters
        device_id = request.GET.get('device_id')
        user_id = request.GET.get('user_id')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        punch_type = request.GET.get('punch_type')
        is_synced = request.GET.get('is_synced')
        
        if device_id:
            logs = logs.filter(device_id=device_id)
        if user_id:
            logs = logs.filter(user_id=user_id)
        if date_from:
            logs = logs.filter(punch_time__date__gte=date_from)
        if date_to:
            logs = logs.filter(punch_time__date__lte=date_to)
        if punch_type is not None:
            logs = logs.filter(punch_type=int(punch_type))
        if is_synced is not None:
            logs = logs.filter(is_synced=is_synced.lower() == 'true')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 50)), 200)
        offset = (page - 1) * per_page
        
        total = logs.count()
        logs = logs[offset:offset + per_page]
        
        serializer = AttendanceLogSerializer(logs, many=True)
        
        return Response({
            'success': True,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'data': serializer.data
        })


class AttendanceReportView(APIView):
    """Attendance summary report"""
    
    def get(self, request):
        date_from = request.GET.get('date_from', timezone.now().date().isoformat())
        date_to = request.GET.get('date_to', timezone.now().date().isoformat())
        user_id = request.GET.get('user_id')
        device_id = request.GET.get('device_id')
        
        logs = AttendanceLog.objects.filter(
            punch_time__date__gte=date_from,
            punch_time__date__lte=date_to
        )
        
        if user_id:
            logs = logs.filter(user_id=user_id)
        if device_id:
            logs = logs.filter(device_id=device_id)
        
        # Group by user and date
        summary = logs.annotate(
            date=TruncDate('punch_time')
        ).values('user_id', 'date').annotate(
            punch_count=Count('id'),
            first_punch=Min('punch_time'),
            last_punch=Max('punch_time')
        ).order_by('date', 'user_id')
        
        report = []
        for item in summary:
            hours = 0
            if item['first_punch'] and item['last_punch']:
                delta = item['last_punch'] - item['first_punch']
                hours = round(delta.total_seconds() / 3600, 2)
            
            report.append({
                'user_id': item['user_id'],
                'date': item['date'],
                'first_punch': item['first_punch'],
                'last_punch': item['last_punch'],
                'punch_count': item['punch_count'],
                'total_hours': hours,
                'status': 'present' if hours > 0 else 'absent'
            })
        
        return Response({
            'success': True,
            'date_range': {'from': date_from, 'to': date_to},
            'total_records': len(report),
            'data': report
        })


class DeviceCommandView(APIView):
    """Device command management"""
    
    def get(self, request, device_id):
        """Get device command history"""
        status_filter = request.GET.get('status')
        commands = DeviceCommand.objects.filter(device_id=device_id)
        
        if status_filter:
            commands = commands.filter(status=status_filter)
        
        commands = commands[:100]
        serializer = DeviceCommandSerializer(commands, many=True)
        return Response({'success': True, 'data': serializer.data})
    
    def post(self, request, device_id):
        """Create new command"""
        try:
            device = ZKDevice.objects.get(pk=device_id)
        except ZKDevice.DoesNotExist:
            return Response({
                'success': False, 
                'message': 'Device not found'
            }, status=404)
        
        command_type = request.data.get('command_type')
        command_content = request.data.get('command_content', '')
        
        if not command_type:
            return Response({
                'success': False, 
                'message': 'command_type required'
            }, status=400)
        
        command = DeviceCommand.objects.create(
            device=device,
            command_type=command_type,
            command_content=command_content
        )
        
        return Response({
            'success': True,
            'message': f'Command {command_type} queued for {device.serial_number}',
            'data': DeviceCommandSerializer(command).data
        }, status=201)


class BulkCommandView(APIView):
    """Send command to multiple devices"""
    
    def post(self, request):
        device_ids = request.data.get('device_ids', [])
        command_type = request.data.get('command_type')
        command_content = request.data.get('command_content', '')
        
        if not device_ids or not command_type:
            return Response({
                'success': False,
                'message': 'device_ids and command_type required'
            }, status=400)
        
        devices = ZKDevice.objects.filter(id__in=device_ids, is_active=True)
        commands_created = []
        
        for device in devices:
            cmd = DeviceCommand.objects.create(
                device=device,
                command_type=command_type,
                command_content=command_content
            )
            commands_created.append(cmd.id)
        
        return Response({
            'success': True,
            'message': f'Command queued for {len(commands_created)} devices',
            'command_ids': commands_created
        }, status=201)


class DeviceUsersView(APIView):
    """Device user management"""
    
    def get(self, request, device_id):
        users = DeviceUser.objects.filter(device_id=device_id)
        
        # Filters
        is_active = request.GET.get('is_active')
        has_fp = request.GET.get('has_fingerprint')
        has_face = request.GET.get('has_face')
        
        if is_active is not None:
            users = users.filter(is_active=is_active.lower() == 'true')
        if has_fp is not None:
            users = users.filter(has_fingerprint=has_fp.lower() == 'true')
        if has_face is not None:
            users = users.filter(has_face=has_face.lower() == 'true')
        
        serializer = DeviceUserSerializer(users, many=True)
        return Response({
            'success': True,
            'count': users.count(),
            'data': serializer.data
        })


class OperationLogView(APIView):
    """Operation log API"""
    
    def get(self, request):
        logs = OperationLog.objects.select_related('device').all()
        
        device_id = request.GET.get('device_id')
        operation_type = request.GET.get('operation_type')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        if device_id:
            logs = logs.filter(device_id=device_id)
        if operation_type:
            logs = logs.filter(operation_type=operation_type)
        if date_from:
            logs = logs.filter(operation_time__date__gte=date_from)
        if date_to:
            logs = logs.filter(operation_time__date__lte=date_to)
        
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 50)), 200)
        offset = (page - 1) * per_page
        
        total = logs.count()
        logs = logs[offset:offset + per_page]
        
        serializer = OperationLogSerializer(logs, many=True)
        
        return Response({
            'success': True,
            'total': total,
            'page': page,
            'per_page': per_page,
            'data': serializer.data
        })


# =============================================================================
# Dashboard & Health Check
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """API health check"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'ZKTeco ADMS API'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    """Dashboard statistics"""
    five_min_ago = timezone.now() - timedelta(minutes=5)
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    total_devices = ZKDevice.objects.filter(is_active=True).count()
    online_devices = ZKDevice.objects.filter(
        is_active=True, 
        last_activity__gte=five_min_ago
    ).count()
    
    stats = {
        'devices': {
            'total': total_devices,
            'online': online_devices,
            'offline': total_devices - online_devices,
        },
        'users': {
            'total': DeviceUser.objects.filter(is_active=True).count(),
            'with_fingerprint': DeviceUser.objects.filter(has_fingerprint=True).count(),
            'with_face': DeviceUser.objects.filter(has_face=True).count(),
        },
        'attendance': {
            'today': AttendanceLog.objects.filter(punch_time__date=today).count(),
            'this_month': AttendanceLog.objects.filter(punch_time__date__gte=month_start).count(),
            'unique_users_today': AttendanceLog.objects.filter(
                punch_time__date=today
            ).values('user_id').distinct().count(),
        },
        'commands': {
            'pending': DeviceCommand.objects.filter(status='pending').count(),
            'executed_today': DeviceCommand.objects.filter(
                status='executed',
                executed_at__date=today
            ).count(),
        }
    }
    
    return Response({
        'success': True,
        'timestamp': timezone.now().isoformat(),
        'data': stats
    })
# DeviceTCPSyncView removed - Use PyZK views instead
# See zktest/api/pyzk_views.py for TCP sync operations




# =============================================================================
# MOBILE ATTENDANCE API
# =============================================================================

class MobileAttendanceView(APIView):
    """
    Mobile Attendance Check-in/Check-out API
    
    POST /api/hrm/mobile/attendance/
    {
        "user_id": "12345",
        "punch_type": 0,  // 0=Check In, 1=Check Out
        "latitude": 23.8103,
        "longitude": 90.4125,
        "location_accuracy": 10.5
    }
    """
    permission_classes = [AllowAny]  # Change to IsAuthenticated in production
    
    def post(self, request):
        from .serializers import MobileAttendanceSerializer, MobileAttendanceResponseSerializer
        
        serializer = MobileAttendanceSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create attendance log
            attendance_log = serializer.save()
            
            # Return response
            response_serializer = MobileAttendanceResponseSerializer(attendance_log)
            
            return Response({
                'success': True,
                'message': 'Attendance recorded successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Mobile attendance error: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_attendance_history(request):
    """
    Get attendance history for a user
    
    GET /api/hrm/mobile/attendance/history/?user_id=12345&days=7
    """
    user_id = request.GET.get('user_id')
    days = int(request.GET.get('days', 7))
    
    if not user_id:
        return Response({
            'success': False,
            'message': 'user_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get attendance logs for last N days
    start_date = timezone.now() - timedelta(days=days)
    logs = AttendanceLog.objects.filter(
        user_id=user_id,
        punch_time__gte=start_date,
        source='mobile'
    ).order_by('-punch_time')
    
    serializer = AttendanceLogSerializer(logs, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data,
        'count': logs.count()
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def mobile_attendance_today(request):
    """
    Get today's attendance for a user
    
    GET /api/hrm/mobile/attendance/today/?user_id=12345
    """
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return Response({
            'success': False,
            'message': 'user_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get today's attendance
    today = timezone.now().date()
    logs = AttendanceLog.objects.filter(
        user_id=user_id,
        punch_time__date=today
    ).order_by('punch_time')
    
    serializer = AttendanceLogSerializer(logs, many=True)
    
    # Calculate summary
    check_in = logs.filter(punch_type=0).first()
    check_out = logs.filter(punch_type=1).last()
    
    summary = {
        'date': today.isoformat(),
        'check_in': check_in.punch_time.isoformat() if check_in else None,
        'check_out': check_out.punch_time.isoformat() if check_out else None,
        'total_punches': logs.count(),
        'status': 'checked_in' if check_in and not check_out else 'checked_out' if check_out else 'not_started'
    }
    
    return Response({
        'success': True,
        'summary': summary,
        'logs': serializer.data
    })
