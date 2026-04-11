# Generated manually for Support module

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth_tenants", "0010_alter_permission_category_and_more"),
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
                ],
                max_length=50,
            ),
        ),
    ]
