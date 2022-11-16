
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_productd2_created_at_productd3_created_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyEtcDesc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comp_code', models.CharField(max_length=10)),
                ('contents', models.CharField(max_length=700)),
            ],
            options={
                'db_table': 'company_etc_desc',
            },
        ),
        migrations.CreateModel(
            name='CompanyEtcTitle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('status', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'company_etc_title',
            },
        ),
        migrations.DeleteModel(
            name='CompanyETC',
        ),
        migrations.AddField(
            model_name='companyetcdesc',
            name='company_etc_title',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.companyetctitle'),
        ),
    ]
