# Generated by Django 4.2.3 on 2023-08-24 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0002_remove_groups_photo_groups_photo'),
        ('blog', '0005_remove_post_image_post_is_active_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='title',
        ),
        migrations.RemoveField(
            model_name='post',
            name='group',
        ),
        migrations.AddField(
            model_name='post',
            name='group',
            field=models.ManyToManyField(to='groups.groups'),
        ),
    ]
