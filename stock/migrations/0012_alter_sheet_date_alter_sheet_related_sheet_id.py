# Generated by Django 4.0.6 on 2023-01-12 13:29

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0011_alter_sheet_company_alter_sheet_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sheet',
            name='date',
            field=models.DateField(default=datetime.datetime(2023, 1, 12, 13, 29, 41, 184183)),
        ),
        migrations.AlterField(
            model_name='sheet',
            name='related_sheet_id',
            field=models.IntegerField(null=True),
        ),
    ]