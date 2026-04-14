from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth_tenants", "0011_support_module"),
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
                    ("payroll", "Payroll"),
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
                    ("payroll", "Payroll"),
                    ("support", "Support"),
                    ("screenhot", "Screenhot"),
                ],
                max_length=50,
            ),
        ),
    ]
