# Generated by Django 4.2.3 on 2023-08-16 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0030_alter_presencemodel_day'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presencemodel',
            name='day',
            field=models.DateField(auto_created=True),
        ),
    ]
