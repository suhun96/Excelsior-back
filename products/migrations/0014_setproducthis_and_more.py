# Generated by Django 4.0.3 on 2022-11-01 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_alter_outboundsetquantity_set_code_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SetProductHis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('use_status', models.IntegerField()),
                ('set_product_code', models.CharField(max_length=10)),
                ('price', models.BigIntegerField()),
                ('barcode', models.CharField(max_length=20)),
                ('etc', models.CharField(blank=True, max_length=3000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'set_product_his',
            },
        ),
        migrations.RenameModel(
            old_name='OutboundSetQuantity',
            new_name='OutboundSetProductQuantity',
        ),
        migrations.RenameModel(
            old_name='SetInfo',
            new_name='SetProductInfo',
        ),
        migrations.RenameModel(
            old_name='SetProduct',
            new_name='SetProductQuantity',
        ),
        migrations.RenameField(
            model_name='outboundsetproductquantity',
            old_name='set_code',
            new_name='set_product_code',
        ),
        migrations.RenameField(
            model_name='setproductinfo',
            old_name='set_code',
            new_name='set_product_code',
        ),
        migrations.RenameField(
            model_name='setproductquantity',
            old_name='set_code',
            new_name='set_product_code',
        ),
        migrations.AlterModelTable(
            name='outboundsetproductquantity',
            table='outbound_set_product_quan',
        ),
        migrations.AlterModelTable(
            name='setproductinfo',
            table='set_product_info',
        ),
        migrations.AlterModelTable(
            name='setproductquantity',
            table='set_product_quan',
        ),
    ]