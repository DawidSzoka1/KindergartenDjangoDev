# Generated by Django 4.2.3 on 2023-07-11 19:32

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('director', '0012_alter_kid_start'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kid',
            name='start',
            field=models.DateField(default=datetime.datetime(2023, 7, 11, 19, 32, 51, 852842, tzinfo=datetime.timezone.utc)),
        ),
    ]
