"""
PyZK (TCP) helpers — pull users/attendance from ZKTeco devices.
Requires: pip install pyzk
"""

import logging
from datetime import datetime

from django.db import IntegrityError
from django.utils import timezone

logger = logging.getLogger(__name__)


def _tcp_password_value(device):
    raw = (device.tcp_password or "").strip()
    if not raw:
        return 0
    return int(raw) if raw.isdigit() else 0


class ZKDeviceConnection:
    """Context manager: TCP session to a ZKTeco device via pyzk."""

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
        try:
            from zk import ZK

            self.zk = ZK(self.ip, port=self.port, timeout=self.timeout, password=self.password)
            self.conn = self.zk.connect()
            logger.info("[PyZK] Connected to %s:%s", self.ip, self.port)
            return True
        except ImportError as e:
            logger.error("[PyZK] pyzk not installed: %s", e)
            raise ImportError("Install pyzk: pip install pyzk") from e
        except Exception as e:
            logger.error("[PyZK] Connection failed %s:%s — %s", self.ip, self.port, e)
            raise ConnectionError(f"Cannot connect to {self.ip}:{self.port}: {e}") from e

    def disconnect(self):
        if self.conn:
            try:
                self.conn.disconnect()
            except Exception as e:
                logger.warning("[PyZK] disconnect: %s", e)

    def get_device_info(self):
        if not self.conn:
            raise ConnectionError("Not connected")
        try:
            return {
                "serial_number": self.conn.get_serialnumber(),
                "device_name": self.conn.get_device_name(),
                "platform": self.conn.get_platform(),
                "firmware_version": self.conn.get_firmware_version(),
                "mac_address": self.conn.get_mac(),
            }
        except Exception as e:
            logger.error("[PyZK] get_device_info: %s", e)
            return {}

    def get_users(self):
        if not self.conn:
            raise ConnectionError("Not connected")
        return self.conn.get_users()

    def get_attendance(self):
        if not self.conn:
            raise ConnectionError("Not connected")
        return self.conn.get_attendance()

    def clear_attendance(self):
        if not self.conn:
            raise ConnectionError("Not connected")
        return self.conn.clear_attendance()

    def restart(self):
        if not self.conn:
            raise ConnectionError("Not connected")
        return self.conn.restart()

    def sync_time(self):
        if not self.conn:
            raise ConnectionError("Not connected")
        return self.conn.set_time(datetime.now())


def import_users_from_device(device):
    from hrm.models import DeviceUser, TCPSyncLog

    if not device.ip_address:
        return {"success": False, "error": "Device IP address not configured"}
    if not device.supports_tcp():
        return {"success": False, "error": "Device is not configured for TCP (PyZK)"}

    log = TCPSyncLog.objects.create(
        device=device,
        sync_type=TCPSyncLog.SyncType.USERS,
        status=TCPSyncLog.Status.RUNNING,
        started_at=timezone.now(),
    )
    result = {
        "success": False,
        "total": 0,
        "imported": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
    }

    try:
        with ZKDeviceConnection(
            ip=str(device.ip_address),
            port=device.port,
            timeout=device.tcp_timeout,
            password=_tcp_password_value(device),
        ) as conn:
            users = conn.get_users()
            result["total"] = len(users)
            for user in users:
                try:
                    uid = str(user.user_id)
                    if DeviceUser.objects.filter(device=device, user_id=uid).exists():
                        result["skipped"] += 1
                        continue
                    DeviceUser.objects.create(
                        device=device,
                        user_id=uid,
                        name=getattr(user, "name", "") or "",
                        privilege=getattr(user, "privilege", 0) or 0,
                        password=getattr(user, "password", "") or "",
                        card_number=str(user.card) if getattr(user, "card", None) else "",
                    )
                    result["imported"] += 1
                except Exception as e:
                    result["failed"] += 1
                    result["errors"].append(f"User {getattr(user, 'user_id', '?')}: {e}")

            device.user_count = device.device_users.count()
            device.last_activity = timezone.now()
            device.is_online = True
            device.save(update_fields=["user_count", "last_activity", "is_online", "updated_at"])
            result["success"] = True

            log.status = TCPSyncLog.Status.COMPLETED
            log.records_found = result["total"]
            log.records_synced = result["imported"]
            log.records_failed = result["failed"]
            log.completed_at = timezone.now()
            log.save()
    except Exception as e:
        result["error"] = str(e)
        logger.exception("[PyZK] import_users_from_device")
        device.is_online = False
        device.save(update_fields=["is_online", "updated_at"])
        log.status = TCPSyncLog.Status.FAILED
        log.error_message = str(e)[:2000]
        log.completed_at = timezone.now()
        log.save()

    return result


def import_attendance_from_device(device, date_from=None, date_to=None, user_id=None):
    from hrm.models import AttendanceLog, TCPSyncLog

    if not device.ip_address:
        return {"success": False, "error": "Device IP address not configured"}
    if not device.supports_tcp():
        return {"success": False, "error": "Device is not configured for TCP (PyZK)"}

    log = TCPSyncLog.objects.create(
        device=device,
        sync_type=TCPSyncLog.SyncType.ATTENDANCE,
        status=TCPSyncLog.Status.RUNNING,
        started_at=timezone.now(),
    )
    result = {
        "success": False,
        "total": 0,
        "imported": 0,
        "skipped": 0,
        "failed": 0,
        "errors": [],
    }

    try:
        with ZKDeviceConnection(
            ip=str(device.ip_address),
            port=device.port,
            timeout=device.tcp_timeout,
            password=_tcp_password_value(device),
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
                if user_id and str(getattr(record, "user_id", "")) != str(user_id):
                    continue
                filtered.append(record)

            result["total"] = len(filtered)
            for record in filtered:
                try:
                    punch_time = record.timestamp
                    if timezone.is_naive(punch_time):
                        punch_time = timezone.make_aware(punch_time)
                    punch = getattr(record, "punch", 0)
                    status_v = getattr(record, "status", 1)
                    _, created = AttendanceLog.objects.get_or_create(
                        device=device,
                        user_id=str(record.user_id),
                        punch_time=punch_time,
                        defaults={
                            "tenant_id": device.tenant_id,
                            "punch_type": punch if punch is not None else 0,
                            "verify_type": status_v if status_v is not None else 1,
                            "source": AttendanceLog.Source.TCP,
                            "validation_status": AttendanceLog.ValidationStatus.DEVICE_SYNC,
                        },
                    )
                    if created:
                        result["imported"] += 1
                    else:
                        result["skipped"] += 1
                except IntegrityError:
                    result["skipped"] += 1
                except Exception as e:
                    result["failed"] += 1
                    result["errors"].append(str(e))

            device.transaction_count = device.attendance_logs.count()
            device.last_activity = timezone.now()
            device.is_online = True
            device.save(
                update_fields=["transaction_count", "last_activity", "is_online", "updated_at"]
            )
            result["success"] = True

            log.status = TCPSyncLog.Status.COMPLETED
            log.records_found = result["total"]
            log.records_synced = result["imported"]
            log.records_failed = result["failed"]
            log.completed_at = timezone.now()
            log.save()
    except Exception as e:
        result["error"] = str(e)
        logger.exception("[PyZK] import_attendance_from_device")
        device.is_online = False
        device.save(update_fields=["is_online", "updated_at"])
        log.status = TCPSyncLog.Status.FAILED
        log.error_message = str(e)[:2000]
        log.completed_at = timezone.now()
        log.save()

    return result


def execute_device_command(device, command_type):
    if not device.ip_address:
        return {"success": False, "error": "Device IP address not configured"}
    if not device.supports_tcp():
        return {"success": False, "error": "Device is not configured for TCP (PyZK)"}

    out = {"success": False, "message": ""}
    try:
        with ZKDeviceConnection(
            ip=str(device.ip_address),
            port=device.port,
            timeout=device.tcp_timeout,
            password=_tcp_password_value(device),
        ) as conn:
            if command_type == "REBOOT":
                conn.restart()
                out["message"] = "Restart command sent"
                out["success"] = True
            elif command_type == "UPDATE_TIME":
                conn.sync_time()
                out["message"] = "Device time synchronized"
                out["success"] = True
            elif command_type == "CLEAR_LOG":
                conn.clear_attendance()
                out["message"] = "Attendance cleared on device"
                out["success"] = True
            elif command_type == "INFO":
                out["data"] = conn.get_device_info()
                out["message"] = "Device info retrieved"
                out["success"] = True
            else:
                out["error"] = f"Unknown command: {command_type}"
        if out.get("success"):
            device.last_activity = timezone.now()
            device.is_online = True
            device.save(update_fields=["last_activity", "is_online", "updated_at"])
    except Exception as e:
        out["error"] = str(e)
        device.is_online = False
        device.save(update_fields=["is_online", "updated_at"])
    return out
