# Generated by Django 4.2.3 on 2023-08-10 10:54

import director.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('director', '0029_mealphotos_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupphotos',
            name='group_photos',
            field=models.ImageField(null=True, unique=True, upload_to=director.models.user_group_path),
        ),
    ]