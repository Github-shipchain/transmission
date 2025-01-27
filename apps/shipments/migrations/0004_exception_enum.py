# Generated by Django 2.2.4 on 2019-11-08 14:55

import apps.shipments.models
from django.db import migrations
import enumfields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0003_add_asset_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalshipment',
            name='exception',
            field=enumfields.fields.EnumIntegerField(default=0, enum=apps.shipments.models.ExceptionType),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='exception',
            field=enumfields.fields.EnumIntegerField(default=0, enum=apps.shipments.models.ExceptionType),
        ),
    ]
