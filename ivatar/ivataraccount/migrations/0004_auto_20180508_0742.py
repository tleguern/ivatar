# Generated by Django 2.0.5 on 2018-05-08 07:42

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ivataraccount', '0003_auto_20180508_0637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confirmedemail',
            name='add_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='confirmedopenid',
            name='add_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='photo',
            name='add_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='unconfirmedemail',
            name='add_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='unconfirmedopenid',
            name='add_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]