# Generated by Django 3.2.24 on 2024-02-28 13:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0004_school_school_adress'),
    ]

    operations = [
        migrations.RenameField(
            model_name='school',
            old_name='school_adress',
            new_name='school_address',
        ),
    ]