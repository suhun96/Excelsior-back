# Generated by Django 4.0.6 on 2022-12-22 14:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_product_barcode'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='productetcdesc',
            table='product_custom_desc',
        ),
        migrations.AlterModelTable(
            name='productetctitle',
            table='product_custom_title',
        ),
    ]