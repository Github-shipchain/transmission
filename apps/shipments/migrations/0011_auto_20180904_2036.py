# Generated by Django 2.0.7 on 2018-09-04 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0010_auto_20180830_2137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipment',
            name='chargeable_weight',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='dimensional_weight',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='gross_weight_kgs',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='volume_cbms',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=9, null=True),
        ),
    ]