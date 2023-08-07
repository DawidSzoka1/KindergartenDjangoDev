# Generated by Django 4.2.3 on 2023-08-07 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('director', '0019_remove_kid_group_remove_kid_kid_meals_and_more'),
        ('children', '0001_initial'),
        ('teacher', '0002_teacher_role_teacher_salary'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='group',
            field=models.ManyToManyField(to='children.groups'),
        ),
        migrations.AddField(
            model_name='teacher',
            name='principal',
            field=models.ManyToManyField(to='director.director'),
        ),
    ]