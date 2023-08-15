# Generated by Django 4.2.3 on 2023-08-11 10:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0015_alter_presencemodel_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='meals',
            name='per_day',
            field=models.DecimalField(decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='presencemodel',
            name='day',
            field=models.DateField(default=datetime.datetime(2023, 8, 11, 10, 27, 51, 331047, tzinfo=datetime.timezone.utc)),
        ),
    ]