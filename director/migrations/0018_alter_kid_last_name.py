# Generated by Django 4.2.3 on 2023-08-07 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('director', '0017_alter_groups_teachers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kid',
            name='last_name',
            field=models.CharField(max_length=128),
        ),
    ]
