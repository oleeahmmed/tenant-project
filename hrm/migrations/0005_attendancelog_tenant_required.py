# Generated manually — enforce AttendanceLog.tenant NOT NULL

from django.db import migrations, models
import django.db.models.deletion


def _drop_orphans(apps, schema_editor):
    AttendanceLog = apps.get_model("hrm", "AttendanceLog")
    Employee = apps.get_model("hrm", "Employee")
    ZKDevice = apps.get_model("hrm", "ZKDevice")
    for row in AttendanceLog.objects.filter(tenant__isnull=True).iterator():
        tenant_id = None
        if getattr(row, "employee_id", None):
            emp = Employee.objects.filter(pk=row.employee_id).only("tenant_id").first()
            tenant_id = getattr(emp, "tenant_id", None)
        if tenant_id is None and getattr(row, "device_id", None):
            dev = ZKDevice.objects.filter(pk=row.device_id).only("tenant_id").first()
            tenant_id = getattr(dev, "tenant_id", None)
        if tenant_id is not None:
            row.tenant_id = tenant_id
            row.save(update_fields=["tenant"])
    unresolved = AttendanceLog.objects.filter(tenant__isnull=True).count()
    if unresolved:
        raise RuntimeError(
            f"Cannot enforce non-null tenant on AttendanceLog: {unresolved} row(s) still unresolved."
        )


def _noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("hrm", "0004_location_gps_policy"),
    ]

    operations = [
        migrations.RunPython(_drop_orphans, _noop),
        migrations.AlterField(
            model_name="attendancelog",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="hrm_attendance_logs",
                to="auth_tenants.tenant",
            ),
        ),
    ]
