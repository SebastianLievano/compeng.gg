# Generated by Django 5.1.4 on 2025-01-19 00:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0019_alter_enrollment_student_repo'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='overall_total',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='private_total',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assignment',
            name='public_total',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assignmenttask',
            name='overall_grade',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assignmenttask',
            name='private_grade',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assignmenttask',
            name='public_grade',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
