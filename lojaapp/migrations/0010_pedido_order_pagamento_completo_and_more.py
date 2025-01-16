# Generated by Django 4.2.16 on 2025-01-16 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lojaapp', '0009_alter_pedido_order_carro'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido_order',
            name='pagamento_completo',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AddField(
            model_name='pedido_order',
            name='pagamento_method',
            field=models.CharField(choices=[('Dinheiro Na Entrega', 'Dinheiro Na Entrega'), ('Khalti', 'Khalti')], default='Dinheiro Na Entrega', max_length=20),
        ),
    ]