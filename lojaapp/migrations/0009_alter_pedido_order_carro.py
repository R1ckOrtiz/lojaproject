# Generated by Django 4.2.16 on 2025-01-15 20:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lojaapp', '0008_alter_pedido_order_total'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedido_order',
            name='carro',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='lojaapp.carro'),
        ),
    ]
