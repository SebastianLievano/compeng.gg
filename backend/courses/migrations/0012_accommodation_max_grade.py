# Generated by Django 5.0.7 on 2024-09-19 11:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0011_alter_accommodation_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='accommodation',
            name='max_grade',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]