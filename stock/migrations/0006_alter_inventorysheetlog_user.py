# Generated by Django 4.0.6 on 2022-11-30 11:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('stock', '0005_inventorysheetlog_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorysheetlog',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user'),
        ),
    ]
