# Generated by Django 3.2.24 on 2024-04-24 13:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0004_auto_20240411_2340'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='image',
        ),
        migrations.CreateModel(
            name='Post_Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(null=True, upload_to='community_thumbnail')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='community.post')),
            ],
        ),
    ]