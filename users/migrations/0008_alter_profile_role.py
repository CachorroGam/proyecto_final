# Generated by Django 5.0.8 on 2024-12-01 03:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_profile_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='role',
            field=models.CharField(choices=[('Administrador', 'Administrador'), ('Lector', 'Lector'), ('Empleado', 'Empleado')], default='Lector', max_length=50),
        ),
    ]
