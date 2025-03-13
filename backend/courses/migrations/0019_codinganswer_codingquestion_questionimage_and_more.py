# Generated by Django 5.1.4 on 2025-03-13 05:08

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0018_alter_enrollment_student_repo"),
        ("github", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CodingAnswer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("last_updated_at", models.DateTimeField()),
                ("comment", models.TextField(blank=True, null=True)),
                ("grade", models.PositiveIntegerField(blank=True, null=True)),
                ("solution", models.TextField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CodingQuestion",
            fields=[
                ("prompt", models.TextField()),
                ("points", models.PositiveIntegerField(default=1)),
                ("order", models.PositiveIntegerField()),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("starter_code", models.TextField(blank=True, null=True)),
                (
                    "programming_language",
                    models.CharField(
                        choices=[("C_PP", "C++"), ("C", "C"), ("PYTHON", "Python")],
                        max_length=6,
                    ),
                ),
                ("files", models.JSONField()),
                ("file_to_replace", models.TextField()),
                ("grading_file_directory", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="QuestionImage",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("image", models.ImageField(upload_to="question_images/")),
                (
                    "question_type",
                    models.CharField(
                        choices=[
                            ("WRITTEN_RESPONSE", "Written Response"),
                            ("CODING", "Coding"),
                            ("MULTIPLE_CHOICE", "Multiple Choice"),
                            ("CHECKBOX", "Checkbox"),
                        ],
                        max_length=16,
                    ),
                ),
                ("question_id", models.CharField(max_length=256)),
            ],
        ),
        migrations.AlterField(
            model_name="enrollment",
            name="student_repo",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="enrollment",
                to="github.repository",
            ),
        ),
        migrations.CreateModel(
            name="CodingAnswerExecution",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("solution", models.TextField()),
                ("result", models.JSONField(blank=True, null=True)),
                ("stderr", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("QUEUED", "Queued"),
                            ("IN_PROGRESS", "In Progress"),
                            ("SUCCESS", "Success"),
                            ("FAILURE", "Failure"),
                        ],
                        max_length=11,
                    ),
                ),
                (
                    "coding_answer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="executions",
                        to="courses.codinganswer",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="codinganswer",
            name="question",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="answers",
                to="courses.codingquestion",
            ),
        ),
        migrations.CreateModel(
            name="OfferingTeamsSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("max_team_size", models.IntegerField(default=3)),
                ("formation_deadline", models.DateTimeField(blank=True, null=True)),
                (
                    "offering",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="courses.offering",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Quiz",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("slug", models.SlugField()),
                ("title", models.TextField()),
                (
                    "content_viewable_after_submission",
                    models.BooleanField(default=False),
                ),
                ("visible_at", models.DateTimeField()),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("total_points", models.PositiveIntegerField(default=0)),
                (
                    "offering",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quizzes",
                        to="courses.offering",
                    ),
                ),
                (
                    "repository",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="quizzes",
                        to="github.repository",
                    ),
                ),
            ],
            options={
                "verbose_name": "Quiz",
                "verbose_name_plural": "Quizzes",
                "unique_together": {("slug", "offering")},
            },
        ),
        migrations.CreateModel(
            name="MultipleChoiceQuestion",
            fields=[
                ("prompt", models.TextField()),
                ("points", models.PositiveIntegerField(default=1)),
                ("order", models.PositiveIntegerField()),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("options", models.JSONField()),
                ("correct_option_index", models.PositiveIntegerField()),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="multiple_choice_questions",
                        to="courses.quiz",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="codingquestion",
            name="quiz",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="coding_questions",
                to="courses.quiz",
            ),
        ),
        migrations.CreateModel(
            name="CheckboxQuestion",
            fields=[
                ("prompt", models.TextField()),
                ("points", models.PositiveIntegerField(default=1)),
                ("order", models.PositiveIntegerField()),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("options", models.JSONField()),
                ("correct_option_indices", models.JSONField(null=True)),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checkbox_questions",
                        to="courses.quiz",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="QuizAccommodation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("visible_at", models.DateTimeField()),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="courses.quiz"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="QuizSubmission",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("started_at", models.DateTimeField()),
                ("completed_at", models.DateTimeField()),
                ("grade", models.PositiveIntegerField(null=True)),
                ("graded_at", models.DateTimeField(null=True)),
                (
                    "graded_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="graded_quiz_submissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quiz_submissions",
                        to="courses.quiz",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MultipleChoiceAnswer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("last_updated_at", models.DateTimeField()),
                ("comment", models.TextField(blank=True, null=True)),
                ("grade", models.PositiveIntegerField(blank=True, null=True)),
                ("selected_answer_index", models.PositiveIntegerField()),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="answers",
                        to="courses.multiplechoicequestion",
                    ),
                ),
                (
                    "quiz_submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="multiple_choice_answers",
                        to="courses.quizsubmission",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="codinganswer",
            name="quiz_submission",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="coding_question_answers",
                to="courses.quizsubmission",
            ),
        ),
        migrations.CreateModel(
            name="CheckboxAnswer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("last_updated_at", models.DateTimeField()),
                ("comment", models.TextField(blank=True, null=True)),
                ("grade", models.PositiveIntegerField(blank=True, null=True)),
                ("selected_answer_indices", models.JSONField(null=True)),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="answers",
                        to="courses.checkboxquestion",
                    ),
                ),
                (
                    "quiz_submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checkbox_answers",
                        to="courses.quizsubmission",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Team",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("github_team_slug", models.CharField(max_length=255)),
                (
                    "offering",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="teams",
                        to="courses.offering",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TeamMember",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "membership_type",
                    models.CharField(
                        choices=[
                            ("MEMBER", "Member"),
                            ("LEADER", "Leader"),
                            ("REQUESTED_TO_JOIN", "Requested to Join"),
                        ],
                        max_length=17,
                    ),
                ),
                (
                    "enrollment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="courses.enrollment",
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="members",
                        to="courses.team",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WrittenResponseQuestion",
            fields=[
                ("prompt", models.TextField()),
                ("points", models.PositiveIntegerField(default=1)),
                ("order", models.PositiveIntegerField()),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("max_length", models.PositiveIntegerField(default=200, null=True)),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="written_response_questions",
                        to="courses.quiz",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WrittenResponseAnswer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("last_updated_at", models.DateTimeField()),
                ("comment", models.TextField(blank=True, null=True)),
                ("grade", models.PositiveIntegerField(blank=True, null=True)),
                ("response", models.TextField()),
                (
                    "quiz_submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="written_response_answers",
                        to="courses.quizsubmission",
                    ),
                ),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="answers",
                        to="courses.writtenresponsequestion",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddConstraint(
            model_name="multiplechoicequestion",
            constraint=models.UniqueConstraint(
                fields=("quiz", "order"), name="unique_order_multiple_choice_question"
            ),
        ),
        migrations.AddConstraint(
            model_name="codingquestion",
            constraint=models.UniqueConstraint(
                fields=("quiz", "order"), name="unique_order_coding_question"
            ),
        ),
        migrations.AddConstraint(
            model_name="checkboxquestion",
            constraint=models.UniqueConstraint(
                fields=("quiz", "order"), name="unique_order_checkbox_question"
            ),
        ),
        migrations.AddConstraint(
            model_name="quizaccommodation",
            constraint=models.UniqueConstraint(
                fields=("user", "quiz"), name="quiz_accommodation_unique_user_quiz"
            ),
        ),
        migrations.AddConstraint(
            model_name="team",
            constraint=models.UniqueConstraint(
                fields=("name", "offering"), name="unique_team_name_per_offering"
            ),
        ),
        migrations.AddConstraint(
            model_name="writtenresponsequestion",
            constraint=models.UniqueConstraint(
                fields=("quiz", "order"), name="unique_order_written_response_question"
            ),
        ),
    ]
