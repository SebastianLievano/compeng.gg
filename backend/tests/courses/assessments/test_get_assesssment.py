from tests.utils import TestCasesWithUserAuth
import courses.models as db
from django.utils import timezone
from tests.utils import (
    create_assessment,
    create_assessment_submission
)
from rest_framework import status
from datetime import timedelta


class GetAssessmentTests(TestCasesWithUserAuth):
    def test_creates_new_submission_on_first_request_happy_path(self):
        requesting_user_id = self.user.id
        
        assessment = create_assessment(user_id=requesting_user_id)

        # Initially no submission should exist
        self.assertFalse(db.AssessmentSubmission.objects.filter(
            user_id=requesting_user_id,
            assessment=assessment
        ).exists())

        response = self.client.get(
            f"/api/v0/assessments/{assessment.id}/",
        )

        self.assertEqual(
            response.status_code, status.HTTP_200_OK
        )

        # After retrieving assessment for the first time, AssessmentSubmission object should be created
        self.assertTrue(db.AssessmentSubmission.objects.filter(
            user_id=requesting_user_id,
            assessment=assessment
        ).exists())


    def test_request_after_viewable_exam_completed_happy_path(self):
        requesting_user_id = self.user.id
        
        assessment = create_assessment(
            user_id=requesting_user_id,
            content_viewable_after_submission=True
        )

        # Create a assessment that is nonviewable after submission
        assessment_submission = create_assessment_submission(
            user_id=requesting_user_id,
            assessment_slug=assessment.id,
        )
        # Mark assessment as completed now
        assessment_submission.completed_at = timezone.now()
        assessment_submission.save()

        response = self.client.get(
            f"/api/v0/assessments/{assessment.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_request_after_nonviewable_exam_completed_throws_error(self):
        requesting_user_id = self.user.id
        
        assessment = create_assessment(
            user_id=requesting_user_id,
            content_viewable_after_submission=False
        )

        # Create a assessment that is nonviewable after submission
        assessment_submission = create_assessment_submission(
            user_id=requesting_user_id,
            assessment_slug=assessment.id,
        )
        # Mark assessment as completed now
        assessment_submission.completed_at = timezone.now()
        assessment_submission.save()

        response = self.client.get(
            f"/api/v0/assessments/{assessment.id}/",
        )

        expected_body = {'error': 'Assessment content cannot be viewed after submission'}

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), expected_body)

    
    def test_request_before_assessment_started_throws_error(self):
        requesting_user_id = self.user.id
        
        assessment = create_assessment(
            user_id=requesting_user_id,
            starts_at=timezone.now() + timedelta(days=1)
        )

        response = self.client.get(
            f"/api/v0/assessments/{assessment.id}/",
        )

        expected_body = {'error': 'Assessment has not started yet'}

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), expected_body)

        
    def test_returns_starter_code(self):
        requesting_user_id = self.user.id
        
        assessment = create_assessment(user_id=requesting_user_id)

        coding_question = db.CodingQuestion.objects.create(
            assessment=assessment,
            prompt='Write a function that prints "Hello World!" in Python',
            order=1,
            points=20,
            programming_language=db.CodingQuestion.ProgrammingLanguage.PYTHON,
            starter_code='print("HI!")'
        )
        
        response = self.client.get(
            f"/api/v0/assessments/{assessment.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_body = {
            'title': assessment.title,
            'end_unix_timestamp': int(assessment.ends_at.timestamp()),
            'questions': [
                {
                    'prompt': coding_question.prompt,
                    'question_type': 'CODING',
                    'points': coding_question.points,
                    'programming_language': str(coding_question.programming_language),
                    'solution': None,
                    'starter_code': coding_question.starter_code
                }
            ]
        }
        
        self.assertDictEqual(
            response.json(), expected_body
        )

    def test_returns_saved_coding_solution(self):
        requesting_user_id = self.user.id
        
        assessment = create_assessment(user_id=requesting_user_id)
        
        assessment_submission = create_assessment_submission(
            user_id=requesting_user_id,
            assessment_slug=assessment.id
        )

        coding_question = db.CodingQuestion.objects.create(
            assessment=assessment,
            prompt='Write a function that prints "Hello World!" in Python',
            order=1,
            points=20,
            programming_language=db.CodingQuestion.ProgrammingLanguage.PYTHON,
        )
        
        coding_answer = db.CodingAnswer.objects.create(
            assessment_submission=assessment_submission,
            question=coding_question,
            solution='print("Hello World!")',
            last_updated_at=timezone.now()
        )
        
        response = self.client.get(
            f"/api/v0/assessments/{assessment.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_body = {
            'title': assessment.title,
            'end_unix_timestamp': int(assessment.ends_at.timestamp()),
            'questions': [
                {
                    'prompt': coding_question.prompt,
                    'question_type': 'CODING',
                    'points': coding_question.points,
                    'programming_language': str(coding_question.programming_language),
                    'solution': coding_answer.solution,
                    'starter_code': None
                }
            ]
        }
        
        self.assertDictEqual(
            response.json(), expected_body
        )
        
    def test_returns_saved_multiple_choice_solution(self):
        requesting_user_id = self.user.id
        
        assessment = create_assessment(user_id=requesting_user_id)
        
        assessment_submission = create_assessment_submission(
            user_id=requesting_user_id,
            assessment_slug=assessment.id
        )

        multiple_choice_question = db.MultipleChoiceQuestion.objects.create(
            assessment=assessment,
            prompt='Choose the animal that flies',
            order=1,
            points=3,
            options=[
                'Deer',
                'Bird',
                'Shark'
            ],
            correct_option_index=1
        )
        
        multiple_choice_answer = db.MultipleChoiceAnswer.objects.create(
            assessment_submission=assessment_submission,
            question=multiple_choice_question,
            selected_answer_index=0,
            last_updated_at=timezone.now()
        )
        
        response = self.client.get(
            f"/api/v0/assessments/{assessment.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_body = {
            'title': assessment.title,
            'end_unix_timestamp': int(assessment.ends_at.timestamp()),
            'questions': [
                {
                    'prompt': multiple_choice_question.prompt,
                    'question_type': 'MULTIPLE_CHOICE',
                    'points': multiple_choice_question.points,
                    'options': multiple_choice_question.options,
                    'selected_answer_index': multiple_choice_answer.selected_answer_index
                },
            ]
        }
        
        self.assertDictEqual(
            response.json(), expected_body
        )
        
    def test_returns_saved_checkbox_solution(self):
        requesting_user_id = self.user.id
        
        assessment = create_assessment(user_id=requesting_user_id)
        
        assessment_submission = create_assessment_submission(
            user_id=requesting_user_id,
            assessment_slug=assessment.id
        )

        checkbox_question = db.CheckboxQuestion.objects.create(
            assessment=assessment,
            prompt='Choose all positive numbers',
            order=2,
            points=4,
            options=['-1', '-2', '3', '4'],
            correct_option_indices=[2, 3]
        )
        
        checkbox_answer = db.CheckboxAnswer.objects.create(
            assessment_submission=assessment_submission,
            question=checkbox_question,
            selected_answer_indices=[0, 1, 2],
            last_updated_at=timezone.now()
        )
        
        response = self.client.get(
            f"/api/v0/assessments/{assessment.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_body = {
            'title': assessment.title,
            'end_unix_timestamp': int(assessment.ends_at.timestamp()),
            'questions': [
                {
                    'prompt': checkbox_question.prompt,
                    'question_type': 'CHECKBOX',
                    'points': checkbox_question.points,
                    'options': checkbox_question.options,
                    'selected_answer_indices': checkbox_answer.selected_answer_indices
                },
            ]
        }
        
        self.assertDictEqual(
            response.json(), expected_body
        )
        
    def test_returns_saved_written_response_solution(self):
        requesting_user_id = self.user.id
        
        assessment = create_assessment(user_id=requesting_user_id)
        
        assessment_submission = create_assessment_submission(
            user_id=requesting_user_id,
            assessment_slug=assessment.id
        )

        written_response_question = db.WrittenResponseQuestion.objects.create(
            assessment=assessment,
            prompt="Write a poem",
            order=1,
            points=5,
            max_length=450
        )
        
        written_response_answer = db.WrittenResponseAnswer.objects.create(
            assessment_submission=assessment_submission,
            question=written_response_question,
            response="Noooooo",
            last_updated_at=timezone.now()
        )
        
        response = self.client.get(
            f"/api/v0/assessments/{assessment.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_body = {
            'title': assessment.title,
            'end_unix_timestamp': int(assessment.ends_at.timestamp()),
            'questions': [
                {
                    'prompt': written_response_question.prompt,
                    'question_type': 'WRITTEN_RESPONSE',
                    'points': written_response_question.points,
                    'max_length': written_response_question.max_length,
                    'response': written_response_answer.response
                },
            ]
        }
        
        self.assertDictEqual(
            response.json(), expected_body
        )
        
    def test_returns_question_types_in_order_happy_path(self):
        requesting_user_id = self.user.id
        
        assessment = create_assessment(user_id=requesting_user_id)

        coding_question = db.CodingQuestion.objects.create(
            assessment=assessment,
            prompt='Write a function that prints "Hello World!" in Python',
            order=4,
            points=20,
            programming_language=db.CodingQuestion.ProgrammingLanguage.PYTHON,
        )

        multiple_choice_question = db.MultipleChoiceQuestion.objects.create(
            assessment=assessment,
            prompt='Choose the animal that flies',
            order=1,
            points=3,
            options=[
                'Deer',
                'Bird',
                'Shark'
            ],
            correct_option_index=1
        )

        written_response_question = db.WrittenResponseQuestion.objects.create(
            assessment=assessment,
            prompt="Write a poem",
            order=3,
            points=5,
            max_length=450
        )
        
        checkbox_question = db.CheckboxQuestion.objects.create(
            assessment=assessment,
            prompt='Choose all positive numbers',
            order=2,
            points=4,
            options=['-1', '-2', '3', '4'],
            correct_option_indices=[2, 3]
        )

        response = self.client.get(
            f"/api/v0/assessments/{assessment.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_body = {
            'title': assessment.title,
            'end_unix_timestamp': int(assessment.ends_at.timestamp()),
            'questions': [
                {
                    'prompt': multiple_choice_question.prompt,
                    'question_type': 'MULTIPLE_CHOICE',
                    'points': multiple_choice_question.points,
                    'options': multiple_choice_question.options,
                    'selected_answer_index': None
                },
                {
                    'prompt': checkbox_question.prompt,
                    'question_type': 'CHECKBOX',
                    'points': checkbox_question.points,
                    'options': checkbox_question.options,
                    'selected_answer_indices': None
                },
                {
                    'prompt': written_response_question.prompt,
                    'question_type': 'WRITTEN_RESPONSE',
                    'points': written_response_question.points,
                    'max_length': written_response_question.max_length,
                    'response': None
                },
                {
                    'prompt': coding_question.prompt,
                    'question_type': 'CODING',
                    'points': coding_question.points,
                    'programming_language': str(coding_question.programming_language),
                    'solution': None,
                    'starter_code': coding_question.starter_code
                }
            ]
        }
        
        self.assertDictEqual(
            response.json(), expected_body
        )
