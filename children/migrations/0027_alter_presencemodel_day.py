# Generated by Django 4.2.3 on 2023-08-15 10:52

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0026_remove_kid_kid_meals_alter_kid_payment_plan_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presencemodel',
            name='day',
            field=models.DateField(auto_created=datetime.datetime(2023, 8, 15, 10, 52, 10, 273975, tzinfo=datetime.timezone.utc)),
        ),
    ]
