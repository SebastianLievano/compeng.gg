# Generated by Django 5.1.4 on 2025-01-26 22:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0025_remove_accommodation_max_grade'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='external_id',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
