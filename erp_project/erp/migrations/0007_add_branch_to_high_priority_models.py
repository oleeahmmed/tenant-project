# Generated migration for adding branch fields to high priority models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0006_populate_branch_fields'),
    ]

    operations = [
        # ==================== FINANCIAL MODELS ====================
        
        # IncomingPayment
        migrations.AddField(
            model_name='incomingpayment',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this payment',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='incoming_payments', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # OutgoingPayment
        migrations.AddField(
            model_name='outgoingpayment',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this payment',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='outgoing_payments', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # BankStatement
        migrations.AddField(
            model_name='bankstatement',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this statement',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='bank_statements', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # JournalEntry
        migrations.AddField(
            model_name='journalentry',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this journal entry',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='journal_entries', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # ==================== INVENTORY MODELS ====================
        
        # StockAdjustment
        migrations.AddField(
            model_name='stockadjustment',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this adjustment',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='stock_adjustments', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # GoodsIssue
        migrations.AddField(
            model_name='goodsissue',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this goods issue',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='goods_issues', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # GoodsReceipt
        migrations.AddField(
            model_name='goodsreceipt',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this goods receipt',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='goods_receipts', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # GoodsReceiptPO
        migrations.AddField(
            model_name='goodsreceiptpo',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this goods receipt',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='goods_receipt_pos', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # InventoryTransfer
        migrations.AddField(
            model_name='inventorytransfer',
            name='from_branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Source branch/warehouse',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='transfers_out', 
                to='erp.warehouse', 
                verbose_name='From Branch'
            ),
        ),
        migrations.AddField(
            model_name='inventorytransfer',
            name='to_branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Destination branch/warehouse',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='transfers_in', 
                to='erp.warehouse', 
                verbose_name='To Branch'
            ),
        ),
        
        # ==================== SALES MODELS ====================
        
        # SalesQuotation
        migrations.AddField(
            model_name='salesquotation',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this quotation',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='sales_quotations', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # SalesReturn
        migrations.AddField(
            model_name='salesreturn',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this return',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='sales_returns', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # Delivery
        migrations.AddField(
            model_name='delivery',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this delivery',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='deliveries', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # ==================== PURCHASE MODELS ====================
        
        # PurchaseQuotation
        migrations.AddField(
            model_name='purchasequotation',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this quotation',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='purchase_quotations', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
        
        # PurchaseReturn
        migrations.AddField(
            model_name='purchasereturn',
            name='branch',
            field=models.ForeignKey(
                blank=True, 
                help_text='Branch/Warehouse for this return',
                null=True, 
                on_delete=django.db.models.deletion.PROTECT, 
                related_name='purchase_returns', 
                to='erp.warehouse', 
                verbose_name='Branch'
            ),
        ),
    ]
