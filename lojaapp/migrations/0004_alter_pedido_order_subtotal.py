# Generated by Django 4.2.16 on 2025-01-15 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lojaapp', '0003_alter_pedido_order_subtotal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedido_order',
            name='subtotal',
            field=models.PositiveIntegerField(),
        ),
    ]
