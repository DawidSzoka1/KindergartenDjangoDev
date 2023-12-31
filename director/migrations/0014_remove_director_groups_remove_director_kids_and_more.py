# Generated by Django 4.2.3 on 2023-07-12 13:25

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('parent', '0005_alter_parenta_options'),
        ('director', '0013_alter_kid_start'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='director',
            name='groups',
        ),
        migrations.RemoveField(
            model_name='director',
            name='kids',
        ),
        migrations.RemoveField(
            model_name='director',
            name='meals',
        ),
        migrations.RemoveField(
            model_name='director',
            name='parent_profiles',
        ),
        migrations.RemoveField(
            model_name='director',
            name='payment_plan',
        ),
        migrations.AlterField(
            model_name='kid',
            name='start',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='director',
            name='groups',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='director.groups'),
        ),
        migrations.AddField(
            model_name='director',
            name='kids',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='director.kid'),
        ),
        migrations.AddField(
            model_name='director',
            name='meals',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='director.meals'),
        ),
        migrations.AddField(
            model_name='director',
            name='parent_profiles',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='parent.parenta'),
        ),
        migrations.AddField(
            model_name='director',
            name='payment_plan',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='director.paymentplan'),
        ),
    ]
