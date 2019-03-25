# Generated by Django 2.1.5 on 2019-03-15 11:57

import apps.eth.fields
import apps.jobs.models
import apps.utils
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import enumfields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0008_auto_20180918_1640'),
    ]

    operations = [
        migrations.CreateModel(
            name='AsyncAction',
            fields=[
                ('id', models.CharField(default=apps.utils.random_id, max_length=36, primary_key=True, serialize=False)),
                ('user_id', models.CharField(blank=True, max_length=36, null=True)),
                ('action_type', enumfields.fields.EnumIntegerField(default=0, enum=apps.jobs.models.AsyncActionType)),
                ('vault_hash', apps.eth.fields.HashField(blank=True, default='', max_length=66, validators=[django.core.validators.RegexValidator(message='Invalid hash.', regex='^0x([A-Fa-f0-9]{64})$')])),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('async_job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='jobs.AsyncJob')),
            ],
            options={
                'ordering': ('created_at',),
            },
        ),
    ]