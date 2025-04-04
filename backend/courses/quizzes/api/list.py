import courses.models as db
from django.db.models import QuerySet
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from django.db.models import Subquery, Q
from courses.quizzes.schemas import (
    AllQuizzesListSerializer,
    CourseQuizzesListSerializer,
)
from typing import Optional
from courses.quizzes.api.permissions import StudentIsEnrolledInCourse


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def list_all(request) -> Response:
    user_id = request.user.id

    student_enrollments = db.Enrollment.objects.filter(
        role__kind=db.Role.Kind.STUDENT,
        user_id=user_id,
    ).values_list("role__offering", flat=True)

    all_quizzes = db.Quiz.objects.filter(
        offering__active=True,
        offering__in=student_enrollments,
    ).order_by("starts_at", "-ends_at")

    return Response(data=AllQuizzesListSerializer(all_quizzes, many=True).data)


@api_view(["GET"])
@permission_classes([StudentIsEnrolledInCourse])
def list_for_course(request, course_slug: str) -> Response:
    user_id = request.user.id

    # filter_params = Q(offering__course__slug=course_slug)
    # course_quizzes = query_quizzes(user_id=user_id, filter_params=filter_params)

    course_quizzes = db.Quiz.objects.filter(
        offering__course__slug=course_slug,
        offering__active=True,
    ).order_by("starts_at", "-ends_at")

    return Response(data=CourseQuizzesListSerializer(course_quizzes, many=True).data)
