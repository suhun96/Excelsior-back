# Generated by Django 4.0.6 on 2022-11-30 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0008_inventorysheet_doc_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorysheet',
            name='doc_no',
            field=models.CharField(default=0, max_length=60),
        ),
    ]
