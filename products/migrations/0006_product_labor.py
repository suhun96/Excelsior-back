# Generated by Django 4.0.6 on 2023-01-12 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_alter_product_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='labor',
            field=models.IntegerField(default=0, null=True),
        ),
    ]
