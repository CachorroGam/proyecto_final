# Generated by Django 5.0.8 on 2024-12-03 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_alter_prestamo_dias_prestamo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='numero_membresia',
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
    ]