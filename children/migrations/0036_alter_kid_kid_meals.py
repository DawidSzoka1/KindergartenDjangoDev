# Generated by Django 4.2.3 on 2023-08-17 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0035_remove_meals_photo_remove_meals_principal_and_more'),
        ('meals', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kid',
            name='kid_meals',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='meals.meals'),
        ),
    ]