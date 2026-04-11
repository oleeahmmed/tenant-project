# Generated migration for adding tax, shipping, and due fields to QuickSale

from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0012_update_quicksale_payment_method'),
    ]

    operations = [
        # Create ShippingArea model
        migrations.CreateModel(
            name='ShippingArea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('area_name', models.CharField(max_length=200, unique=True, verbose_name='Area Name')),
                ('shipping_charge', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Shipping Charge')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
            ],
            options={
                'verbose_name': 'Shipping Area',
                'verbose_name_plural': 'Shipping Areas',
                'ordering': ['area_name'],
            },
        ),
        
        # Add new fields to QuickSale
        migrations.AddField(
            model_name='quicksale',
            name='tax_percentage',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5, verbose_name='Tax %'),
        ),
        migrations.AddField(
            model_name='quicksale',
            name='tax_amount',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12, verbose_name='Tax Amount'),
        ),
        migrations.AddField(
            model_name='quicksale',
            name='shipping_area',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quick_sales', to='erp.shippingarea', verbose_name='Shipping Area'),
        ),
        migrations.AddField(
            model_name='quicksale',
            name='shipping_charge',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='Shipping Charge'),
        ),
        migrations.AddField(
            model_name='quicksale',
            name='due_amount',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12, verbose_name='Due Amount'),
        ),
        
        # Delete POSPayment model
        migrations.DeleteModel(
            name='POSPayment',
        ),
    ]
