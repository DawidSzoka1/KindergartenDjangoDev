# Generated by Django 4.2.3 on 2023-07-10 11:44

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('parent', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Groups',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Meals',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('description', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, default=500, max_digits=7)),
            ],
        ),
        migrations.CreateModel(
            name='Kid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=128)),
                ('last_name', models.CharField(default='cos', max_length=128)),
                ('gender', models.IntegerField(choices=[(1, 'Chłopiec'), (2, 'Dziewczynka')], default=1)),
                ('start', models.DateField(default=datetime.datetime(2023, 7, 10, 11, 44, 47, 688031, tzinfo=datetime.timezone.utc))),
                ('end', models.DateField(null=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=20, null=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='director.groups')),
                ('parent', models.ManyToManyField(to='parent.parent')),
                ('payment_plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='director.paymentplan')),
            ],
        ),
        migrations.CreateModel(
            name='Director',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('groups', models.ManyToManyField(to='director.groups')),
                ('kids', models.ManyToManyField(to='director.kid')),
                ('meals', models.ManyToManyField(to='director.meals')),
                ('parent', models.ManyToManyField(to='parent.parent')),
                ('payment_plan', models.ManyToManyField(to='director.paymentplan')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': [('is_director', 'True')],
            },
        ),
    ]
