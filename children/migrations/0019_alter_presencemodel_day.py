# Generated by Django 4.2.3 on 2023-08-14 11:57

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0018_groups_yearbook_alter_presencemodel_day'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presencemodel',
            name='day',
            field=models.DateField(default=datetime.datetime(2023, 8, 14, 11, 57, 11, 21627, tzinfo=datetime.timezone.utc)),
        ),
    ]