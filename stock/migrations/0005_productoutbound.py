# Generated by Django 4.0.6 on 2022-11-28 15:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
        ('stock', '0004_alter_productprice_company_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductOutbound',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_code', models.CharField(max_length=20)),
                ('warehouse_code', models.CharField(max_length=20)),
                ('unit_price', models.IntegerField(default=0)),
                ('quantity', models.IntegerField(default=0)),
                ('etc', models.CharField(max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
            ],
            options={
                'db_table': 'product_outbound',
            },
        ),
    ]
