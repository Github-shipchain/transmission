# Generated by Django 2.0.9 on 2018-11-19 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0017_shipment_moderator_wallet_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipment',
            name='vault_uri',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
