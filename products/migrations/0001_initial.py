# Generated by Django 4.0.6 on 2022-11-22 18:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0008_alter_user_updated_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='InboundOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_code', models.CharField(max_length=5)),
                ('etc', models.CharField(blank=True, max_length=3000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'inbound_order',
            },
        ),
        migrations.CreateModel(
            name='OutboundOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_code', models.CharField(max_length=5)),
                ('etc', models.CharField(blank=True, max_length=3000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'outbound_order',
            },
        ),
        migrations.CreateModel(
            name='ProductD1',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_code', models.CharField(max_length=10)),
                ('productgroup_code', models.CharField(max_length=10)),
                ('productgroup_num', models.CharField(max_length=10)),
                ('quantity', models.IntegerField()),
                ('safe_quantity', models.IntegerField()),
                ('keyword', models.CharField(max_length=150)),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'productD1',
            },
        ),
        migrations.CreateModel(
            name='ProductD2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_code', models.CharField(max_length=10)),
                ('productgroup_code', models.CharField(max_length=10)),
                ('productgroup_num', models.CharField(max_length=10)),
                ('quantity', models.IntegerField()),
                ('safe_quantity', models.IntegerField()),
                ('keyword', models.CharField(max_length=150)),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'productD2',
            },
        ),
        migrations.CreateModel(
            name='ProductD3',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_code', models.CharField(max_length=10)),
                ('productgroup_code', models.CharField(max_length=10)),
                ('productgroup_num', models.CharField(max_length=10)),
                ('quantity', models.IntegerField()),
                ('safe_quantity', models.IntegerField()),
                ('keyword', models.CharField(max_length=150)),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'productD3',
            },
        ),
        migrations.CreateModel(
            name='ProductEtcTitle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('status', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'product_etc_title',
            },
        ),
        migrations.CreateModel(
            name='ProductGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('code', models.CharField(max_length=10)),
                ('etc', models.CharField(max_length=3000)),
                ('status', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'product_groups',
            },
        ),
        migrations.CreateModel(
            name='ProductHis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10)),
                ('barcode', models.CharField(max_length=20)),
                ('status', models.IntegerField()),
                ('price', models.BigIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'product_his',
            },
        ),
        migrations.CreateModel(
            name='ProductEtcDesc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_code', models.CharField(max_length=10)),
                ('contents', models.CharField(max_length=700)),
                ('product_etc_title', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.productetctitle')),
            ],
            options={
                'db_table': 'product_etc_desc',
            },
        ),
        migrations.CreateModel(
            name='ProductD3Composition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('com_quan', models.IntegerField()),
                ('productD1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.productd1')),
                ('productD2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.productd2')),
                ('productD3', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.productd3')),
            ],
            options={
                'db_table': 'productD3_composition',
            },
        ),
        migrations.CreateModel(
            name='ProductD2Composition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('productD1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.productd1')),
                ('productD2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.productd2')),
            ],
            options={
                'db_table': 'productD2_composition',
            },
        ),
        migrations.CreateModel(
            name='OutboundQuantity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_code', models.CharField(max_length=40)),
                ('outbound_price', models.BigIntegerField()),
                ('outbound_quantity', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('outbound_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.outboundorder')),
            ],
            options={
                'db_table': 'outbound_quantity',
            },
        ),
        migrations.CreateModel(
            name='InboundQuantity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_code', models.CharField(max_length=10)),
                ('inbound_price', models.BigIntegerField()),
                ('inbound_quantity', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('inbound_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.inboundorder')),
            ],
            options={
                'db_table': 'inbound_quantity',
            },
        ),
    ]
