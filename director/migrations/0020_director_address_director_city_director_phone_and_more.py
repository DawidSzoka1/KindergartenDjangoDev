# Generated by Django 4.2.3 on 2023-08-08 16:19

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('director', '0019_remove_kid_group_remove_kid_kid_meals_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='director',
            name='address',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='director',
            name='city',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='director',
            name='phone',
            field=models.CharField(max_length=17, null=True, unique=True, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+99 999 999 999'. Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')]),
        ),
        migrations.AddField(
            model_name='director',
            name='zip_code',
            field=models.CharField(max_length=6, null=True, validators=[django.core.validators.RegexValidator(message='Must be valid zipcode in formats or 12-123', regex='^(^[0-9]{2}(?:-[0-9]{3})?$)?$)')]),
        ),
    ]
