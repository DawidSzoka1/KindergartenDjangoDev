# Generated by Django 4.2.3 on 2023-08-24 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('director', '0034_director_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupphotos',
            name='date_created',
            field=models.DateField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='mealphotos',
            name='date_created',
            field=models.DateField(auto_now_add=True, null=True),
        ),
    ]
