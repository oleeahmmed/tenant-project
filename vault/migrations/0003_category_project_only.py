import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vault", "0002_simplify_entry_scope"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="vaultcategory",
            options={"ordering": ["project__customer__name", "project__key", "order", "name"]},
        ),
        migrations.AlterUniqueTogether(
            name="vaultcategory",
            unique_together={("tenant", "project", "name")},
        ),
        migrations.RemoveField(
            model_name="vaultcategory",
            name="customer",
        ),
        migrations.AlterField(
            model_name="vaultcategory",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="vault_categories",
                to="jiraclone.jiraproject",
            ),
        ),
        migrations.AlterModelOptions(
            name="vaultentry",
            options={"ordering": ["category__project__customer__name", "category__name", "name"]},
        ),
    ]
