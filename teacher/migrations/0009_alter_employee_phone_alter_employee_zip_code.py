# Generated by Django 4.2.3 on 2023-08-09 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0008_rename_teacher_employee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='phone',
            field=models.CharField(max_length=17, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='zip_code',
            field=models.CharField(max_length=6, null=True),
        ),
    ]
