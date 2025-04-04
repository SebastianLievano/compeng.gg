import os
from django.conf import settings
from uuid import uuid4
from django.db import models
from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from compeng_gg.django.github.models import Repository
from runner.models import Runner, Task


class Institution(models.Model):
    slug = models.SlugField(max_length=50)
    name = models.CharField(max_length=50)
    verified_discord_role_id = models.BigIntegerField(blank=True, null=True)
    first_year_discord_role_id = models.BigIntegerField(blank=True, null=True)
    second_year_discord_role_id = models.BigIntegerField(blank=True, null=True)
    third_year_discord_role_id = models.BigIntegerField(blank=True, null=True)
    fourth_year_discord_role_id = models.BigIntegerField(blank=True, null=True)
    grad_student_discord_role_id = models.BigIntegerField(blank=True, null=True)
    faculty_discord_role_id = models.BigIntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if Offering.objects.filter(course__institution=self,
                                   active=False) \
                           .exists():
            return reverse('courses:archive_institution',
                            kwargs={'institution_slug': self.slug})
        raise NoReverseMatch(f'{self} has no archived offerings')

    class Meta:
        ordering = ['slug']

class Course(models.Model):

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
    )
    slug = models.SlugField(max_length=50)
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=80)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if Offering.objects.filter(course=self, active=False).exists():
            return reverse('courses:archive_course', kwargs={
                'institution_slug': self.institution.slug,
                'course_slug': self.slug,
            })
        raise NoReverseMatch(f'{self} has no archived offerings')

    class Meta:
        ordering = ['slug']

class Offering(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
    )
    slug = models.SlugField(max_length=50)
    name = models.CharField(max_length=50)
    start = models.DateField()
    end = models.DateField()
    active = models.BooleanField()
    external_id = models.BigIntegerField(blank=True, null=True)
    runner_repo = models.ForeignKey(
        Repository,
        on_delete=models.SET_NULL,
        related_name="offering_runner",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.name} {self.course}'

    def full_slug(self):
        return f'{self.slug}-{self.course.slug}'

    def get_absolute_url(self):
        if self.active:
            return reverse('courses:course', kwargs={'course_slug': self.course.slug})
        else:
            return reverse('courses:archive_offering', kwargs={
                'institution_slug': self.course.institution.slug,
                'course_slug': self.course.slug,
                'offering_slug': self.slug,
            })

    class Meta:
        ordering = ['-start', 'slug']

class OfferingTeamsSettings(models.Model):
    offering = models.OneToOneField(
        Offering,
        on_delete=models.CASCADE,
    )
    max_team_size = models.IntegerField(default=3)
    formation_deadline = models.DateTimeField(blank=True, null=True)

class Assignment(models.Model):

    class Kind(models.IntegerChoices):
        TESTS = 1
        LEADERBOARD = 2

    offering = models.ForeignKey(
        Offering,
        on_delete=models.CASCADE,
    )
    kind = models.IntegerField(choices=Kind)
    runner = models.ForeignKey(
        Runner,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    slug = models.SlugField(max_length=50)
    name = models.CharField(max_length=50)
    due_date = models.DateTimeField()
    files = models.JSONField()
    external_id = models.BigIntegerField(blank=True, null=True)

    is_private_released = models.BooleanField(default=False)
    public_total = models.FloatField(blank=True, null=True)
    private_total = models.FloatField(blank=True, null=True)
    overall_total = models.FloatField(blank=True, null=True)
    external_total = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f'{self.offering} - {self.name}'

    class Meta:
        ordering = ['-due_date']

class Role(models.Model):

    class Kind(models.IntegerChoices):
        INSTRUCTOR = 1, _('Instructor')
        TA = 2, _('TA')
        STUDENT = 3, _('Student')
        AUDIT = 4, _('Audit')

    kind = models.IntegerField(choices=Kind)
    offering = models.ForeignKey(
        Offering,
        on_delete=models.CASCADE,
    )
    discord_role_id = models.BigIntegerField(blank=True, null=True)
    github_team_slug = models.CharField(max_length=128, blank=True, null=False)

    def __str__(self):
        return f'{self.offering} {self.get_kind_display()}'

    class Meta:
        unique_together = ['kind', 'offering']

class Member(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
    )
    external_id = models.BigIntegerField()

    def __str__(self):
        return f'{self.user} ({self.external_id})'

    class Meta:
        unique_together = ['institution', 'external_id']



class Enrollment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
    )
    student_repo = models.OneToOneField(
        Repository,
        on_delete=models.SET_NULL,
        related_name="enrollment",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.user} - {self.role}'

    class Meta:
        unique_together = ['user', 'role']


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255, blank=False, null=False)
    created_at = models.DateTimeField(default=timezone.now)
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE, related_name='teams')
    github_team_slug = models.CharField(max_length=255, blank=False, null=False)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'offering'], name='unique_team_name_per_offering')
        ]

class TeamMember(models.Model):
    class MembershipType(models.TextChoices):
        MEMBER = "MEMBER", _("Member")
        LEADER = "LEADER", _("Leader")
        REQUESTED_TO_JOIN = "REQUESTED_TO_JOIN", _("Requested to Join")

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    membership_type = models.CharField(
        choices=MembershipType.choices,
        max_length=max(len(choice.value) for choice in MembershipType),
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')


class AssignmentTask(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )
    public_grade = models.FloatField(blank=True, null=True)
    private_grade = models.FloatField(blank=True, null=True)
    overall_grade = models.FloatField(blank=True, null=True)
    before_due_date = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user} - {self.assignment} - {self.task}'

class AssignmentResult(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    public_grade = models.FloatField(blank=True, null=True)
    private_grade = models.FloatField(blank=True, null=True)
    overall_grade = models.FloatField(blank=True, null=True)
    external_grade = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f'{self.user} - {self.assignment}'

    class Meta:
        unique_together = ['user', 'assignment']

class AssignmentLeaderboardEntry(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
    )
    speedup = models.IntegerField()

    def __str__(self):
        return f'{self.user} - {self.assignment} - {self.speedup}'

    class Meta:
        unique_together = ['user', 'assignment']

class AssignmentGrade(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
    )
    grade = models.IntegerField()

    def __str__(self):
        return f'{self.user} - {self.assignment} - Grade: {self.grade}'

    class Meta:
        unique_together = ['user', 'assignment']

class Accommodation(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
    )
    due_date = models.DateTimeField()

    def __str__(self):
        return f'{self.user} - {self.assignment} - {self.due_date}'

    class Meta:
        unique_together = ['user', 'assignment']


class Quiz(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    slug = models.SlugField(max_length=50)
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE, related_name='quizzes')
    title = models.TextField()
    content_viewable_after_submission = models.BooleanField(default=False)
    visible_at = models.DateTimeField()
    starts_at = models.DateTimeField() # TODO: validate ends_at > starts_at
    release_answers_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    repository = models.ForeignKey(Repository, on_delete=models.DO_NOTHING, related_name='quizzes')
    total_points = models.PositiveIntegerField(default=0)
    
    def __str__( self):
        return f"{self.title}({self.offering.slug})"
    
    class Meta:
        unique_together = ['slug', 'offering']
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"
    
class QuizAccommodation(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
    )
    visible_at = models.DateTimeField()
    starts_at = models.DateTimeField() # TODO: validate ends_at > starts_at
    ends_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'quiz'], name='quiz_accommodation_unique_user_quiz'
            )
        ]

class QuizSubmission(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='quiz_submissions')
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()
    grade = models.PositiveIntegerField(null=True)
    graded_at = models.DateTimeField(null=True)
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, related_name='graded_quiz_submissions')
    

class QuizQuestionImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order = models.PositiveIntegerField()
    image = models.ImageField(upload_to="quiz_question_images/")
    caption = models.TextField(null=True, blank=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='images')

class QuizQuestionBaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='%(class)ss')
    prompt = models.TextField()
    render_prompt_as_latex = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField()
    images = models.ManyToManyField(QuizQuestionImage)
    
    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['quiz', 'order'], name="%(class)s_unique_order_for_quiz"
            )
        ]


class QuizAnswerBaseModel(models.Model):
    quiz_submission = models.ForeignKey(QuizSubmission, on_delete=models.CASCADE, related_name='%(class)ss')
    last_updated_at = models.DateTimeField()
    comment = models.TextField(null=True, blank=True)
    grade = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['quiz_submission', 'question'], name='%(class)s_one_answer_per_question'
            )
        ]


class WrittenResponseQuestion(QuizQuestionBaseModel):
    max_length = models.PositiveIntegerField(default=200, null=True)

    

class WrittenResponseAnswer(QuizAnswerBaseModel):
    question = models.ForeignKey(WrittenResponseQuestion, on_delete=models.CASCADE, related_name='answers')
    
    response = models.TextField()

class CodingQuestion(QuizQuestionBaseModel):
    class ProgrammingLanguage(models.TextChoices):
        C_PP = "C_PP", _("C++")
        C = "C", _("C")
        PYTHON = "PYTHON", _("Python")

    starter_code = models.TextField(blank=True, null=True)
    programming_language = models.CharField(
        choices=ProgrammingLanguage.choices,
        max_length=max(len(choice.value) for choice in ProgrammingLanguage),
        blank=False,
        null=False,
    )

    files = models.JSONField()
    file_to_replace = models.TextField()
    grading_file_directory = models.TextField()



class CodingAnswer(QuizAnswerBaseModel):
    question = models.ForeignKey(CodingQuestion, on_delete=models.CASCADE, related_name="answers")
    
    solution = models.TextField()


class CodingAnswerExecution(models.Model):
    class Status(models.TextChoices):
        QUEUED = "QUEUED", _("Queued")
        IN_PROGRESS = "IN_PROGRESS", _("In Progress")
        SUCCESS = "SUCCESS", _("Success")
        FAILURE = "FAILURE", _("Failure")

    coding_answer = models.ForeignKey(CodingAnswer, on_delete=models.CASCADE, related_name="executions")
    solution = models.TextField()
    result = models.JSONField(blank=True, null=True)
    stderr = models.TextField()

    status = models.CharField(
        choices=Status.choices,
        max_length=max(len(choice.value) for choice in Status),
        blank=False,
        null=False,
    )


class MultipleChoiceQuestion(QuizQuestionBaseModel):
    options = models.JSONField() # TODO: validate this is an array
    correct_option_index = models.PositiveIntegerField()



class MultipleChoiceAnswer(QuizAnswerBaseModel):
    question = models.ForeignKey(MultipleChoiceQuestion, on_delete=models.CASCADE, related_name='answers')

    selected_answer_index = models.PositiveIntegerField()


class CheckboxQuestion(QuizQuestionBaseModel):
    options = models.JSONField() # TODO: validate this is an array
    correct_option_indices = models.JSONField(null=True) # TODO: validate this is an array



class CheckboxAnswer(QuizAnswerBaseModel):
    question = models.ForeignKey(CheckboxQuestion, on_delete=models.CASCADE, related_name='answers')
    
    selected_answer_indices = models.JSONField(null=True) # TODO: validate this is an array

class QuestionType(models.TextChoices):
    WRITTEN_RESPONSE = "WRITTEN_RESPONSE", _("Written Response")
    CODING = "CODING", _("Coding")
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE", _("Multiple Choice")
    CHECKBOX = "CHECKBOX", _("Checkbox")
