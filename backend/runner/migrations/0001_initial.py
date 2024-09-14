# Generated by Django 5.0.7 on 2024-09-13 14:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('github_app', '0003_push_delivery_alter_push_payload'),
    ]

    operations = [
        migrations.CreateModel(
            name='Runner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.CharField(max_length=255)),
                ('command', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(choices=[(1, 'Queued'), (2, 'In Progress'), (3, 'Success'), (4, 'Failure')])),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('result', models.JSONField(blank=True, null=True)),
                ('push', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='github_app.push')),
                ('runner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='runner.runner')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
    ]