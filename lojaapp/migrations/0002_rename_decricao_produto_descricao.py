# Generated by Django 5.1.4 on 2025-01-10 13:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lojaapp', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='produto',
            old_name='decricao',
            new_name='descricao',
        ),
    ]
