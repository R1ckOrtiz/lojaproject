# Generated by Django 4.2.16 on 2025-01-15 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lojaapp', '0002_rename_decricao_produto_descricao'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedido_order',
            name='subtotal',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
