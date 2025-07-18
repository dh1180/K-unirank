# Generated by Django 5.1.4 on 2025-05-02 04:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0014_remove_school_match_count_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='match_count',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='school',
            name='win_match_count',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='school',
            name='win_tournament_count',
            field=models.BigIntegerField(default=0),
        ),
    ]
