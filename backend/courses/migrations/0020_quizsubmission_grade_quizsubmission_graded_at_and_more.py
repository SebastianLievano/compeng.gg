# Generated by Django 5.1.4 on 2025-02-25 18:17

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0019_codingquestion_alter_enrollment_student_repo_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='quizsubmission',
            name='grade',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='quizsubmission',
            name='graded_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='quizsubmission',
            name='graded_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='graded_quiz_submissions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='writtenresponsequestion',
            name='max_length',
            field=models.PositiveIntegerField(default=200, null=True),
        ),
    ]
