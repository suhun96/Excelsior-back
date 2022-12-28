# Generated by Django 4.0.6 on 2022-12-27 17:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_alter_productetcdesc_table_and_more'),
        ('stock', '0012_serialinsheetcomposition'),
    ]

    operations = [
        migrations.CreateModel(
            name='SheetLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sheet_id', models.IntegerField()),
                ('user_name', models.CharField(max_length=50)),
                ('type', models.CharField(max_length=30)),
                ('company_code', models.CharField(max_length=20)),
                ('status', models.BooleanField(default=True)),
                ('etc', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'sheet_logs',
            },
        ),
        migrations.AlterField(
            model_name='sheet',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterModelTable(
            name='sheetcomposition',
            table='sheet_detail',
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
    ]