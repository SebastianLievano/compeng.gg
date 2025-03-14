from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from courses.quizzes.api.admin.schema import CheckboxQuestionRequestSerializer
from rest_framework.response import Response
import courses.models as db
from courses.quizzes.api.admin.utils import (
    validate_user_is_ta_or_instructor_in_course,
    CustomException,
)
from courses.quizzes.api.admin.question.total_points import update_quiz_total_points
from courses.quizzes.api.admin.permissions import IsAuthenticatedCourseInstructorOrTA


@api_view(["POST"])
@permission_classes([IsAuthenticatedCourseInstructorOrTA])
def create_checkbox_question(request, course_slug: str, quiz_slug: str):
    serializer = CheckboxQuestionRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    prompt = serializer.validated_data.get("prompt")
    points = serializer.validated_data.get("points")
    order = serializer.validated_data.get("order")
    options = serializer.validated_data.get("options")
    correct_option_indices = serializer.validated_data.get("correct_option_indices")
    render_prompt_as_latex = serializer.validated_data.get("render_prompt_as_latex")

    checkbox_question = db.CheckboxQuestion.objects.create(
        prompt=prompt,
        render_prompt_as_latex=render_prompt_as_latex,
        points=points,
        order=order,
        options=options,
        correct_option_indices=correct_option_indices,
        quiz=request.quiz,
    )
    
    update_quiz_total_points(course_slug, quiz_slug)

    return Response(
        status=status.HTTP_200_OK, data={"question_id": checkbox_question.id}
    )
