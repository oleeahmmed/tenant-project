# ==================== zktest/utils/pyzk_utils.py ====================
"""
PyZK (TCP) utilities
Used by api/pyzk_views.py
"""

import logging
from datetime import datetime
from django.utils import timezone
from django.db import IntegrityError

logger = logging.getLogger(__name__)


# =============================================================================
# PyZK Connection Manager
# =============================================================================

class ZKDeviceConnection:
    """
    PyZK wrapper for TCP connection to ZKTeco devices
    
    Usage:
        with ZKDeviceConnection(ip='192.168.1.201', port=4370) as conn:
            users = conn.get_users()
            attendance = conn.get_attendance()
    """
    
    def __init__(self, ip, port=4370, timeout=5, password=0):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.password = password
        self.conn = None
        self.zk = None
        
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
    
    def connect(self):
        """Establish TCP connection to device"""
        try:
            from zk import ZK
            self.zk = ZK(self.ip, port=self.port, timeout=self.timeout, password=self.password)
            self.conn = self.zk.connect()
            logger.info(f"[PyZK] Connected to {self.ip}:{self.port}")
            return True
        except ImportError:
            logger.error("[PyZK] pyzk library not installed. Run: pip install pyzk")
            raise ImportError("pyzk library not installed. Run: pip install pyzk")
        except Exception as e:
            logger.error(f"[PyZK] Connection failed to {self.ip}:{self.port} - {str(e)}")
            raise ConnectionError(f"Cannot connect to device at {self.ip}:{self.port}: {str(e)}")
    
    def disconnect(self):
        """Disconnect from device"""
        if self.conn:
            try:
                self.conn.disconnect()
                logger.info(f"[PyZK] Disconnected from {self.ip}")
            except Exception as e:
                logger.warning(f"[PyZK] Disconnect error: {str(e)}")
    
    def get_device_info(self):
        """Get device information"""
        if not self.conn:
            raise ConnectionError("Not connected to device")
        
        try:
            return {
                'serial_number': self.conn.get_serialnumber(),
                'device_name': self.conn.get_device_name(),
                'platform': self.conn.get_platform(),
                'firmware_version': self.conn.get_firmware_version(),
                'mac_address': self.conn.get_mac(),
            }
        except Exception as e:
            logger.error(f"[PyZK] Get device info error: {str(e)}")
            return {}
    
    def get_users(self):
        """Get all users from device"""
        if not self.conn:
            raise ConnectionError("Not connected to device")
        
        try:
            users = self.conn.get_users()
            logger.info(f"[PyZK] Found {len(users)} users on device")
            return users
        except Exception as e:
            logger.error(f"[PyZK] Get users error: {str(e)}")
            return []
    
    def get_attendance(self):
        """Get all attendance records from device"""
        if not self.conn:
            raise ConnectionError("Not connected to device")
        
        try:
            attendance = self.conn.get_attendance()
            logger.info(f"[PyZK] Found {len(attendance)} attendance records")
            return attendance
        except Exception as e:
            logger.error(f"[PyZK] Get attendance error: {str(e)}")
            return []
    
    def set_user(self, uid, name, privilege=0, password='', card_number='', user_id=''):
        """Add or update user on device"""
        if not self.conn:
            raise ConnectionError("Not connected to device")
        
        try:
            self.conn.set_user(
                uid=uid,
                name=name,
                privilege=privilege,
                password=password,
                card=card_number,
                user_id=user_id or str(uid)
            )
            logger.info(f"[PyZK] User {uid} set successfully")
            return True
        except Exception as e:
            logger.error(f"[PyZK] Set user error: {str(e)}")
            return False
    
    def delete_user(self, uid=0, user_id=''):
        """Delete user from device"""
        if not self.conn:
            raise ConnectionError("Not connected to device")
        
        try:
            self.conn.delete_user(uid=uid, user_id=user_id)
            logger.info(f"[PyZK] User {uid or user_id} deleted")
            return True
        except Exception as e:
            logger.error(f"[PyZK] Delete user error: {str(e)}")
            return False
    
    def clear_attendance(self):
        """Clear all attendance records from device"""
        if not self.conn:
            raise ConnectionError("Not connected to device")
        
        try:
            self.conn.clear_attendance()
            logger.info(f"[PyZK] Attendance cleared")
            return True
        except Exception as e:
            logger.error(f"[PyZK] Clear attendance error: {str(e)}")
            return False
    
    def restart(self):
        """Restart device"""
        if not self.conn:
            raise ConnectionError("Not connected to device")
        
        try:
            self.conn.restart()
            logger.info(f"[PyZK] Device restart command sent")
            return True
        except Exception as e:
            logger.error(f"[PyZK] Restart error: {str(e)}")
            return False
    
    def sync_time(self):
        """Sync device time with server"""
        if not self.conn:
            raise ConnectionError("Not connected to device")
        
        try:
            self.conn.set_time(datetime.now())
            logger.info(f"[PyZK] Time synced")
            return True
        except Exception as e:
            logger.error(f"[PyZK] Sync time error: {str(e)}")
            return False
    
    def get_time(self):
        """Get device time"""
        if not self.conn:
            raise ConnectionError("Not connected to device")
        
        try:
            return self.conn.get_time()
        except Exception as e:
            logger.error(f"[PyZK] Get time error: {str(e)}")
            return None


# =============================================================================
# PyZK Helper Functions
# =============================================================================

def import_users_from_device(device):
    """
    Import users from device via TCP - ONLY NEW USERS
    
    Args:
        device: ZKDevice instance
    
    Returns:
        dict: Import result
    """
    from hrm.models import DeviceUser
    
    if not device.ip_address:
        return {'success': False, 'error': 'Device IP address not configured'}
    
    result = {
        'success': False,
        'total': 0,
        'imported': 0,
        'skipped': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        with ZKDeviceConnection(
            ip=device.ip_address,
            port=device.port,
            timeout=device.tcp_timeout,
            password=int(device.tcp_password) if device.tcp_password else 0
        ) as conn:
            users = conn.get_users()
            result['total'] = len(users)
            
            for user in users:
                try:
                    user_id = str(user.user_id)
                    
                    # Check if exists - SKIP if yes
                    if DeviceUser.objects.filter(device=device, user_id=user_id).exists():
                        result['skipped'] += 1
                        continue
                    
                    # Create NEW user only
                    DeviceUser.objects.create(
                        device=device,
                        user_id=user_id,
                        name=user.name or '',
                        privilege=user.privilege or 0,
                        password=user.password or '',
                        card_number=str(user.card) if user.card else '',
                    )
                    result['imported'] += 1
                    
                except Exception as e:
                    result['failed'] += 1
                    result['errors'].append(f"User {user.user_id}: {str(e)}")
            
            # Update device stats
            device.user_count = device.users.count()
            device.last_activity = timezone.now()
            device.is_online = True
            device.save(update_fields=['user_count', 'last_activity', 'is_online'])
            
            result['success'] = True
            
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"[PyZK] User import failed: {str(e)}")
        device.is_online = False
        device.save(update_fields=['is_online'])
    
    return result


def import_attendance_from_device(device, date_from=None, date_to=None, user_id=None):
    """
    Import attendance from device via TCP - ONLY NEW RECORDS
    
    Args:
        device: ZKDevice instance
        date_from: Filter from date
        date_to: Filter to date
        user_id: Filter by user
    
    Returns:
        dict: Import result
    """
    from hrm.models import AttendanceLog
    
    if not device.ip_address:
        return {'success': False, 'error': 'Device IP address not configured'}
    
    result = {
        'success': False,
        'total': 0,
        'imported': 0,
        'skipped': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        with ZKDeviceConnection(
            ip=device.ip_address,
            port=device.port,
            timeout=device.tcp_timeout,
            password=int(device.tcp_password) if device.tcp_password else 0
        ) as conn:
            attendance = conn.get_attendance()
            
            # Filter records
            filtered_records = []
            for record in attendance:
                # Date filter
                if date_from and record.timestamp.date() < date_from:
                    continue
                if date_to and record.timestamp.date() > date_to:
                    continue
                
                # User filter
                if user_id and str(record.user_id) != user_id:
                    continue
                
                filtered_records.append(record)
            
            result['total'] = len(filtered_records)
            
            for record in filtered_records:
                try:
                    # Make timestamp timezone-aware
                    punch_time = record.timestamp
                    if timezone.is_naive(punch_time):
                        punch_time = timezone.make_aware(punch_time)
                    
                    # Try to create - skip if exists
                    _, created = AttendanceLog.objects.get_or_create(
                        device=device,
                        user_id=str(record.user_id),
                        punch_time=punch_time,
                        defaults={
                            'punch_type': record.punch if hasattr(record, 'punch') else 0,
                            'verify_type': record.status if hasattr(record, 'status') else 1,
                            'source': 'tcp',
                        }
                    )
                    
                    if created:
                        result['imported'] += 1
                    else:
                        result['skipped'] += 1
                        
                except IntegrityError:
                    result['skipped'] += 1
                except Exception as e:
                    result['failed'] += 1
                    result['errors'].append(str(e))
            
            # Update device stats
            device.transaction_count = device.attendance_logs.count()
            device.last_activity = timezone.now()
            device.is_online = True
            device.save(update_fields=['transaction_count', 'last_activity', 'is_online'])
            
            result['success'] = True
            
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"[PyZK] Attendance import failed: {str(e)}")
        device.is_online = False
        device.save(update_fields=['is_online'])
    
    return result


def execute_device_command(device, command_type):
    """
    Execute command on device via TCP
    
    Args:
        device: ZKDevice instance
        command_type: Command to execute
    
    Returns:
        dict: Command result
    """
    if not device.ip_address:
        return {'success': False, 'error': 'Device IP address not configured'}
    
    result = {'success': False, 'message': ''}
    
    try:
        with ZKDeviceConnection(
            ip=device.ip_address,
            port=device.port,
            timeout=device.tcp_timeout,
            password=int(device.tcp_password) if device.tcp_password else 0
        ) as conn:
            
            if command_type == 'REBOOT':
                conn.restart()
                result['message'] = 'Device restart command sent'
                result['success'] = True
                
            elif command_type == 'UPDATE_TIME':
                conn.sync_time()
                result['message'] = 'Time synchronized'
                result['success'] = True
                
            elif command_type == 'CLEAR_LOG':
                conn.clear_attendance()
                result['message'] = 'Attendance cleared'
                result['success'] = True
                
            elif command_type == 'INFO':
                info = conn.get_device_info()
                result['data'] = info
                result['message'] = 'Device info retrieved'
                result['success'] = True
                
            else:
                result['error'] = f'Unknown command type: {command_type}'
        
        # Update device activity on success
        if result['success']:
            device.last_activity = timezone.now()
            device.is_online = True
            device.save(update_fields=['last_activity', 'is_online'])
            
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"[PyZK] Command {command_type} failed: {str(e)}")
        
        # Mark device offline on connection error
        device.is_online = False
        device.save(update_fields=['is_online'])
    
    return result
