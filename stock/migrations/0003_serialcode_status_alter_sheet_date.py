# Generated by Django 4.0.6 on 2023-01-05 13:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0002_alter_sheet_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='serialcode',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='sheet',
            name='date',
            field=models.DateField(default=datetime.datetime(2023, 1, 5, 13, 46, 45, 42275)),
        ),
    ]
