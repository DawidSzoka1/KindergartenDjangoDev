# Generated by Django 4.2.3 on 2023-08-18 14:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('director', '0032_freedaysmodel_is_active_groupphotos_is_active_and_more'),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groups',
            name='photo',
        ),
        migrations.AddField(
            model_name='groups',
            name='photo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='director.groupphotos'),
        ),
    ]