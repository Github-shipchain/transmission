# Generated by Django 2.2.4 on 2019-09-06 13:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('imports', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='shipmentimport',
            options={'ordering': ('-created_at',)},
        ),
    ]
