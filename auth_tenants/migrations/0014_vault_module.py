from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth_tenants", "0013_remove_payroll_module"),
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
                    ("vault", "Vault"),
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
                    ("vault", "Vault"),
                    ("chat", "Chat"),
                    ("pos", "POS"),
                    ("support", "Support"),
                    ("screenhot", "Screenhot"),
                ],
                max_length=50,
            ),
        ),
    ]
