# Generated by Django 2.1.5 on 2019-01-31 20:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0025_set_location_country_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipment',
            name='final_destination_location',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shipments_dest', to='shipments.Location'),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='ship_from_location',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shipments_from', to='shipments.Location'),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='ship_to_location',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shipments_to', to='shipments.Location'),
        ),
    ]
