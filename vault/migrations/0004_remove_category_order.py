from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("vault", "0003_category_project_only"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="vaultcategory",
            name="order",
        ),
        migrations.AlterModelOptions(
            name="vaultcategory",
            options={"ordering": ["project__customer__name", "project__key", "name"]},
        ),
    ]
