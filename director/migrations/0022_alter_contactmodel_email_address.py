# Generated by Django 4.2.3 on 2023-08-08 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('director', '0021_remove_director_address_remove_director_city_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contactmodel',
            name='email_address',
            field=models.EmailField(max_length=254, null=True),
        ),
    ]