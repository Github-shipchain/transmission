# Generated by Django 2.1.7 on 2019-06-06 18:27

import apps.eth.fields
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eth', '0007_eth_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactionreceipt',
            name='loom_tx_hash',
            field=apps.eth.fields.HashField(db_index=True, default='', max_length=66, null=True, validators=[django.core.validators.RegexValidator(message='Invalid hash.', regex='^0x([A-Fa-f0-9]{64})$')]),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='chain_id',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='transactionreceipt',
            name='logs_bloom',
            field=models.CharField(max_length=514, null=True),
        ),
    ]
