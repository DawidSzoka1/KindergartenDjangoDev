# Generated by Django 4.2.3 on 2023-08-15 11:03

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0027_alter_presencemodel_day'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presencemodel',
            name='day',
            field=models.DateField(auto_created=datetime.datetime(2023, 8, 15, 11, 3, 18, 924941, tzinfo=datetime.timezone.utc)),
        ),
    ]