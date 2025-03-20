from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from courses.quizzes.api.admin.schema import (
    WrittenResponseQuestionRequestSerializer,
)
from rest_framework.response import Response
import courses.models as db
from courses.quizzes.api.admin.permissions import IsAuthenticatedCourseInstructorOrTA


@api_view(["POST"])
@permission_classes([IsAuthenticatedCourseInstructorOrTA])
def edit_written_response_question(
    request, course_slug: str, quiz_slug: str, written_response_question_id: str
):
    # TODO: validate quiz matches question
    written_response_question = db.WrittenResponseQuestion.objects.get(
        id=written_response_question_id
    )
    serializer = WrittenResponseQuestionRequestSerializer(
        written_response_question, data=request.data, partial=True
    )

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    return Response(status=status.HTTP_204_NO_CONTENT)
