# Generated by Django 4.2.3 on 2023-08-09 23:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('director', '0025_remove_groupphotos_principal_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupphotos',
            name='principal',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='director.director'),
        ),
    ]
