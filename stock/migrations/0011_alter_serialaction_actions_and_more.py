# Generated by Django 4.0.6 on 2022-12-16 09:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_product_barcode'),
        ('stock', '0010_remove_serialaction_compose_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serialaction',
            name='actions',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='serialaction',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product'),
        ),
    ]
