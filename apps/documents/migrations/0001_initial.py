# Generated by Django 2.0.9 on 2018-11-14 19:52

import apps.documents.models
import apps.utils
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import enumfields.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shipments', '0015_loadshipment_vault_hash'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.CharField(default=apps.utils.random_id, max_length=36, primary_key=True, serialize=False)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('owner_id', models.CharField(max_length=36)),
                ('document_type', enumfields.fields.EnumField(default=0, enum=apps.documents.models.DocumentType, max_length=10)),
                ('file_type', enumfields.fields.EnumField(default=0, enum=apps.documents.models.FileType, max_length=10)),
                ('upload_status', enumfields.fields.EnumField(default=0, enum=apps.documents.models.UploadStatus, max_length=10)),
                ('size', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12500000)])),
                ('s3_path', models.CharField(blank=True, max_length=144, null=True)),
                ('shipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shipments.Shipment')),
            ],
        ),
    ]
