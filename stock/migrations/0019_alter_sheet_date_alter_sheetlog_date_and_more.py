# Generated by Django 4.1.5 on 2023-02-10 22:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0018_sheetlog_date_sheetlog_timestamp_alter_sheet_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sheet',
            name='date',
            field=models.DateField(default=datetime.datetime(2023, 2, 10, 22, 46, 42, 407654)),
        ),
        migrations.AlterField(
            model_name='sheetlog',
            name='date',
            field=models.DateField(default=datetime.datetime(2023, 2, 10, 22, 46, 42, 409159)),
        ),
        migrations.AlterField(
            model_name='sheetlog',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2023, 2, 10, 22, 46, 42, 409323)),
        ),
    ]
