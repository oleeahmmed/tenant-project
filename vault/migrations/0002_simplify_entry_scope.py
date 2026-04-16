from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("vault", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="vaultentry",
            name="customer",
        ),
        migrations.RemoveField(
            model_name="vaultentry",
            name="project",
        ),
        migrations.AlterModelOptions(
            name="vaultentry",
            options={"ordering": ["category__customer__name", "category__name", "name"]},
        ),
    ]
