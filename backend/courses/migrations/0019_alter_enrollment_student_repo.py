# Generated by Django 5.1.4 on 2025-01-03 12:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0018_alter_enrollment_student_repo'),
        ('github', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enrollment',
            name='student_repo',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enrollment', to='github.repository'),
        ),
    ]