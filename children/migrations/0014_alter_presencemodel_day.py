# Generated by Django 4.2.3 on 2023-08-10 12:55

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0013_presencemodel_delete_presentmodel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presencemodel',
            name='day',
            field=models.DateField(default=datetime.datetime(2023, 8, 10, 12, 55, 58, 717171, tzinfo=datetime.timezone.utc)),
        ),
    ]