from django.db import migrations, models


def purge_payroll_artifacts(apps, schema_editor):
    Permission = apps.get_model("auth_tenants", "Permission")
    TenantModuleSubscription = apps.get_model("auth_tenants", "TenantModuleSubscription")
    TenantPermissionGrant = apps.get_model("auth_tenants", "TenantPermissionGrant")

    payroll_permission_ids = list(
        Permission.objects.filter(
            models.Q(category="payroll") | models.Q(codename__istartswith="payroll.")
        ).values_list("id", flat=True)
    )
    if payroll_permission_ids:
        TenantPermissionGrant.objects.filter(permission_id__in=payroll_permission_ids).delete()
        Permission.objects.filter(id__in=payroll_permission_ids).delete()

    TenantModuleSubscription.objects.filter(module_code="payroll").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth_tenants", "0012_screenhot_module"),
    ]

    operations = [
        migrations.AlterField(
            model_name="permission",
            name="category",
            field=models.CharField(
                choices=[
                    ("foundation", "Foundation"),
                    ("inventory", "Inventory"),
                    ("finance", "Finance"),
                    ("purchase", "Purchase"),
                    ("sales", "Sales"),
                    ("production", "Production"),
                    ("jiraclone", "Jira clone"),
                    ("chat", "Chat"),
                    ("pos", "POS"),
                    ("hrm", "HRM"),
                    ("recruitment", "Recruitment"),
                    ("support", "Support"),
                    ("screenhot", "Screenhot"),
                    ("auth_tenants", "Tenant Auth"),
                    ("system", "System"),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="tenantmodulesubscription",
            name="module_code",
            field=models.CharField(
                choices=[
                    ("hrm", "HRM"),
                    ("recruitment", "Recruitment"),
                    ("inventory", "Inventory"),
                    ("finance", "Finance"),
                    ("purchase", "Purchase"),
                    ("sales", "Sales"),
                    ("production", "Production"),
                    ("jiraclone", "Jira clone"),
                    ("chat", "Chat"),
                    ("pos", "POS"),
                    ("support", "Support"),
                    ("screenhot", "Screenhot"),
                ],
                max_length=50,
            ),
        ),
        migrations.RunPython(purge_payroll_artifacts, migrations.RunPython.noop),
    ]
