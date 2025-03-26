from courses.quizzes.api.admin.permissions import IsAuthenticatedCourseInstructorOrTA
import courses.models as db
from rest_framework.decorators import api_view, permission_classes
from uuid import UUID
from django.http import FileResponse
from courses.quizzes.api.permissions import StudentCanViewQuiz
from rest_framework.permissions import BasePermission

class IsInstructorOrTAOrCanViewQuiz(BasePermission):
    """
    Permission that allows access if the user is an instructor/TA or has student quiz view permission
    """
    def has_permission(self, request, view):
        return (IsAuthenticatedCourseInstructorOrTA().has_permission(request, view) or 
                StudentCanViewQuiz().has_permission(request, view))

@api_view(["GET"])
@permission_classes([IsInstructorOrTAOrCanViewQuiz])
def get_quiz_question_image(
    request, course_slug: str, quiz_slug: str, question_image_id: UUID
):
    quiz = request.quiz

    quiz_image = db.QuizQuestionImage.objects.get(id=question_image_id, quiz=quiz)

    return FileResponse(quiz_image.image.open(), content_type="image/jpeg")
