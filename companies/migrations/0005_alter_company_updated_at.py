# Generated by Django 4.0.6 on 2022-11-18 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0004_company_created_at_company_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='updated_at',
            field=models.DateField(auto_now=True),
        ),
    ]