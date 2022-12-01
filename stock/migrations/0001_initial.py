# Generated by Django 4.0.6 on 2022-12-01 15:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventorySheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('doc_no', models.CharField(default=0, max_length=60)),
                ('is_inbound', models.CharField(max_length=30)),
                ('company_code', models.CharField(max_length=20)),
                ('warehouse_code', models.CharField(max_length=10)),
                ('unit_price', models.IntegerField(default=0)),
                ('before_quantity', models.IntegerField(default=0)),
                ('after_quantity', models.IntegerField(default=0)),
                ('quantity', models.IntegerField(default=0)),
                ('etc', models.CharField(max_length=500)),
                ('status', models.BooleanField(default=True)),
                ('created_at', models.DateField(auto_now=True)),
                ('updated_at', models.DateField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'inventory_sheet',
            },
        ),
        migrations.CreateModel(
            name='TotalProductQuantity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_quantity', models.IntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
            ],
            options={
                'db_table': 'inventory_quantity',
            },
        ),
        migrations.CreateModel(
            name='ProductPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_code', models.CharField(max_length=10)),
                ('inbound_price', models.IntegerField(default=0)),
                ('outbound_price', models.IntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
            ],
            options={
                'db_table': 'inventory_price',
            },
        ),
        migrations.CreateModel(
            name='InventorySheetLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('process_type', models.CharField(max_length=100)),
                ('is_inbound', models.CharField(max_length=30)),
                ('company_code', models.CharField(max_length=20)),
                ('warehouse_code', models.CharField(max_length=10)),
                ('unit_price', models.IntegerField(default=0)),
                ('before_quantity', models.IntegerField(default=0)),
                ('after_quantity', models.IntegerField(default=0)),
                ('quantity', models.IntegerField(default=0)),
                ('etc', models.CharField(max_length=500)),
                ('status', models.BooleanField(default=False)),
                ('created_at', models.DateField(auto_now=True)),
                ('updated_at', models.DateField(auto_now=True)),
                ('inventorysheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.inventorysheet')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'inventory_sheet_log',
            },
        ),
    ]