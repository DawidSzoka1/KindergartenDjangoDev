# Generated by Django 4.2.3 on 2023-08-14 16:14

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0024_alter_presencemodel_day'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presencemodel',
            name='day',
            field=models.DateField(auto_created=datetime.datetime(2023, 8, 14, 16, 14, 38, 916392, tzinfo=datetime.timezone.utc)),
        ),
    ]
