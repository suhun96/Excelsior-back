# Generated by Django 4.0.6 on 2023-01-10 17:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_remove_product_productgroup_code_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='product_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.productgroup'),
        ),
    ]
