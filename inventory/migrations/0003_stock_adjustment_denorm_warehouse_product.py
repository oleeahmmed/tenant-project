# Denormalize stock adjustment: warehouse_code/name, product_sku/name; drop FKs.

from django.db import migrations, models


def copy_fk_to_codes(apps, schema_editor):
    StockAdjustment = apps.get_model("inventory", "StockAdjustment")
    StockAdjustmentItem = apps.get_model("inventory", "StockAdjustmentItem")
    Warehouse = apps.get_model("foundation", "Warehouse")
    Product = apps.get_model("foundation", "Product")

    for adj in StockAdjustment.objects.all().iterator():
        wid = getattr(adj, "warehouse_id", None)
        if wid:
            try:
                w = Warehouse.objects.get(pk=wid)
                adj.warehouse_code = w.code
                adj.warehouse_name = w.name
            except Warehouse.DoesNotExist:
                adj.warehouse_code = ""
                adj.warehouse_name = ""
        adj.save(update_fields=["warehouse_code", "warehouse_name"])

    for item in StockAdjustmentItem.objects.all().iterator():
        pid = getattr(item, "product_id", None)
        if pid:
            try:
                p = Product.objects.get(pk=pid)
                item.product_sku = p.sku
                item.product_name = p.name
            except Product.DoesNotExist:
                item.product_sku = ""
                item.product_name = ""
        item.save(update_fields=["product_sku", "product_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_product_price_warehouse_limits_line_totals"),
    ]

    operations = [
        migrations.AddField(
            model_name="stockadjustment",
            name="warehouse_code",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="Warehouse code (denormalized snapshot; no FK on this document).",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="stockadjustment",
            name="warehouse_name",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="stockadjustmentitem",
            name="product_sku",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="Product SKU (denormalized snapshot; no FK on this line).",
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name="stockadjustmentitem",
            name="product_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.RunPython(copy_fk_to_codes, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="stockadjustment",
            name="warehouse",
        ),
        migrations.RemoveField(
            model_name="stockadjustmentitem",
            name="product",
        ),
    ]
