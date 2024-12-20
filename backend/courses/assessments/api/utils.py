import courses.models as db
from uuid import UUID
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from typing import (
    Optional,
    Union,
    Type
)


def get_existing_answer_object(
    answer_model: Union[
        Type[db.MultipleChoiceAnswer],
        Type[db.CheckboxAnswer],
        Type[db.CodingAnswer],
        Type[db.WrittenResponseAnswer],
    ],
    question_id: UUID,
    user_id: int,
) -> Optional[
        Union[
            db.MultipleChoiceAnswer,
            db.CheckboxAnswer,
            db.CodingAnswer,
            db.WrittenResponseAnswer,
        ]
    ]:
    try:
        answer_object = answer_model.objects.get(
            question_id=question_id,
            assessment_submission__user_id=user_id
        )
        return answer_object
    except answer_model.DoesNotExist:
        return None


def get_assessment_submission_or_error_response(
    request_at: datetime, user_id: int, assessment_slug: str
) -> Union[db.AssessmentSubmission, Response]:
    try:
        assessment_submission = db.AssessmentSubmission.objects.get(
            assessment_slug=assessment_slug,
            user_id=user_id,
        )
    except db.AssessmentSubmission.DoesNotExist:
        return Response(
            {'error': 'Assessment submission not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request_at > assessment_submission.completed_at:
        return Response(
            {'error': 'The assessment has already been completed'},
            status=status.HTTP_403_FORBIDDEN
        )
        
    return assessment_submission
