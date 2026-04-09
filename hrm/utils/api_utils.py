import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)


def get_date_range(range_type):
    today = timezone.now().date()
    if range_type == "today":
        return today, today
    if range_type == "7days":
        return today - timedelta(days=7), today
    if range_type == "30days":
        return today - timedelta(days=30), today
    if range_type == "month":
        return today.replace(day=1), today
    return today, today


def success_response(message="Success", data=None, **kwargs):
    response = {
        "success": True,
        "message": message,
        "timestamp": timezone.now().isoformat(),
    }
    if data is not None:
        response["data"] = data
    response.update(kwargs)
    return response


def error_response(message="Error", data=None, errors=None, **kwargs):
    response = {
        "success": False,
        "message": message,
        "timestamp": timezone.now().isoformat(),
    }
    if data is not None:
        response["data"] = data
    if errors is not None:
        response["errors"] = errors
    response.update(kwargs)
    return response


def auto_create_employee_from_device_user(device_user):
    """Create an Employee for this tenant when a device user is imported."""
    from hrm.models import Employee

    tenant_id = device_user.device.tenant_id
    uid = (device_user.user_id or "").strip()
    if not uid:
        return None
    if Employee.objects.filter(tenant_id=tenant_id, zk_user_id=uid).exists():
        return None
    name = (device_user.name or uid).strip()[:255]
    code = uid[:50]
    if Employee.objects.filter(tenant_id=tenant_id, employee_code=code).exists():
        code = f"ZK-{uid}"[:50]
    try:
        emp = Employee.objects.create(
            tenant_id=tenant_id,
            employee_code=code,
            full_name=name,
            zk_user_id=uid,
            status=Employee.Status.ACTIVE,
        )
        logger.info("Auto-created employee for zk_user_id=%s tenant=%s", uid, tenant_id)
        return emp
    except Exception as e:
        logger.exception("Failed to auto-create employee: %s", e)
        return None
