from django.db import migrations


def backfill_category_customer(apps, schema_editor):
    VaultCategory = apps.get_model("vault", "VaultCategory")
    for category in VaultCategory.objects.select_related("project").all():
        if category.customer_id is None and category.project_id and category.project.customer_id:
            category.customer_id = category.project.customer_id
            category.save(update_fields=["customer"])


class Migration(migrations.Migration):
    dependencies = [
        ("vault", "0007_alter_vaultcategory_options_alter_vaultentry_options_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_category_customer, migrations.RunPython.noop),
    ]
