# Generated by Django 4.2.3 on 2023-08-09 22:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0008_groups_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groups',
            name='image',
            field=models.ImageField(null=True, upload_to='groups_foto'),
        ),
    ]
