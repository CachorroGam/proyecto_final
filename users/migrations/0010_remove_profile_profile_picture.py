# Generated by Django 5.0.8 on 2024-12-01 19:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_profile_profile_picture'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='profile_picture',
        ),
    ]