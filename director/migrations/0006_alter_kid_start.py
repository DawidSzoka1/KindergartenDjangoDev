# Generated by Django 4.2.3 on 2023-07-10 15:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('director', '0005_alter_kid_start'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kid',
            name='start',
            field=models.DateField(default=datetime.datetime(2023, 7, 10, 15, 25, 54, 669270, tzinfo=datetime.timezone.utc)),
        ),
    ]
