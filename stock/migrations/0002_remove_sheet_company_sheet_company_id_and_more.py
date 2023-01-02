# Generated by Django 4.0.6 on 2023-01-02 13:53

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sheet',
            name='company',
        ),
        migrations.AddField(
            model_name='sheet',
            name='company_id',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='sheet',
            name='date',
            field=models.DateField(default=datetime.datetime(2023, 1, 2, 13, 53, 9, 687595)),
        ),
    ]
