# Generated by Django 4.0.6 on 2023-01-11 16:09

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0009_alter_sheet_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sheet',
            name='date',
            field=models.DateField(default=datetime.datetime(2023, 1, 11, 16, 9, 43, 354969)),
        ),
    ]