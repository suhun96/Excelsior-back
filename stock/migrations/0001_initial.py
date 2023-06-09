# Generated by Django 4.0.6 on 2023-01-09 15:31

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        ('companies', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SerialCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sheet_id', models.IntegerField()),
                ('product_id', models.IntegerField()),
                ('code', models.CharField(max_length=100)),
                ('status', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'serial_codes',
            },
        ),
        migrations.CreateModel(
            name='SerialCodeTitle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('status', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'serial_code_titles',
            },
        ),
        migrations.CreateModel(
            name='Sheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=30)),
                ('company_id', models.IntegerField(default=1)),
                ('status', models.BooleanField(default=True)),
                ('etc', models.CharField(max_length=500)),
                ('date', models.DateField(default=datetime.datetime(2023, 1, 9, 15, 31, 56, 572627))),
                ('related_sheet_id', models.IntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'sheet',
            },
        ),
        migrations.CreateModel(
            name='StockByWarehouse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('warehouse_code', models.CharField(max_length=20)),
                ('stock_quantity', models.IntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
                ('sheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.sheet')),
            ],
            options={
                'db_table': 'stock_by_warehouse',
            },
        ),
        migrations.CreateModel(
            name='SheetLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sheet_id', models.IntegerField()),
                ('user_name', models.CharField(max_length=50)),
                ('type', models.CharField(max_length=30)),
                ('status', models.BooleanField(default=True)),
                ('etc', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='companies.company')),
            ],
            options={
                'db_table': 'sheet_logs',
            },
        ),
        migrations.CreateModel(
            name='SheetCompositionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit_price', models.IntegerField(default=0)),
                ('quantity', models.IntegerField(default=0)),
                ('warehouse_code', models.CharField(max_length=20)),
                ('location', models.CharField(max_length=300)),
                ('etc', models.CharField(max_length=300)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
                ('sheet_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sheet_log', to='stock.sheetlog')),
            ],
            options={
                'db_table': 'sheet_log_composition',
            },
        ),
        migrations.CreateModel(
            name='SheetComposition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit_price', models.IntegerField(default=0)),
                ('quantity', models.IntegerField(default=0)),
                ('warehouse_code', models.CharField(max_length=20)),
                ('location', models.CharField(max_length=300)),
                ('etc', models.CharField(max_length=300)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
                ('sheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.sheet')),
            ],
            options={
                'db_table': 'sheet_detail',
            },
        ),
        migrations.CreateModel(
            name='SerialCodeValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contents', models.CharField(max_length=255)),
                ('date', models.DateTimeField(auto_now=True)),
                ('serial_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='serial_code_value', to='stock.serialcode')),
                ('title', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.serialcodetitle')),
                ('user', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'serial_code_value',
            },
        ),
        migrations.CreateModel(
            name='QuantityByWarehouse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('warehouse_code', models.CharField(max_length=20)),
                ('total_quantity', models.IntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
            ],
            options={
                'db_table': 'quantity_by_warehouse',
            },
        ),
        migrations.CreateModel(
            name='ProductPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inbound_price', models.IntegerField(default=0)),
                ('outbound_price', models.IntegerField(default=0)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='companies.company')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
            ],
            options={
                'db_table': 'product_price',
            },
        ),
        migrations.CreateModel(
            name='MovingAverageMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('average_price', models.IntegerField()),
                ('custom_price', models.IntegerField(null=True)),
                ('total_quantity', models.IntegerField()),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
            ],
            options={
                'db_table': 'moving_average_method',
            },
        ),
    ]
