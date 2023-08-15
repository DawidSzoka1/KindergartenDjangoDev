# Generated by Django 4.2.3 on 2023-08-10 12:19

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0012_presentmodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='PresenceModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.DateField(default=datetime.datetime(2023, 8, 10, 12, 19, 45, 539449, tzinfo=datetime.timezone.utc))),
                ('presenceType', models.IntegerField(choices=[(1, 'Nieobeconsc'), (2, 'Obecnosc'), (3, 'Planowana nieobecnosc'), (4, 'dzien wolny')])),
                ('kid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='children.kid')),
            ],
        ),
        migrations.DeleteModel(
            name='PresentModel',
        ),
    ]