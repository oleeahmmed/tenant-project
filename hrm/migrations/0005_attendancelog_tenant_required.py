# Generated manually — enforce AttendanceLog.tenant NOT NULL

from django.db import migrations, models
import django.db.models.deletion


def _drop_orphans(apps, schema_editor):
    AttendanceLog = apps.get_model("hrm", "AttendanceLog")
    AttendanceLog.objects.filter(tenant__isnull=True).delete()


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
