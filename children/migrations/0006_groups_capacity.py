# Generated by Django 4.2.3 on 2023-08-09 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0005_remove_groups_teacher'),
    ]

    operations = [
        migrations.AddField(
            model_name='groups',
            name='capacity',
            field=models.IntegerField(null=True),
        ),
    ]
