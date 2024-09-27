from django.test import TestCase
from unittest import mock
import courses.models as db
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from tests.utils import create_offering
from rest_framework import status

class JoinTeamViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_join_team_happy_path(self):
        offering = create_offering()
        
        student_role = db.Role.objects.create(kind=db.Role.Kind.STUDENT, offering=offering)
        
        enrollment = db.Enrollment.objects.create(
            user=self.user,
            role=student_role,
        )
        
        team = db.Team.objects.create(offering=offering)
        
        request_data = {
            'team_id': team.id,
            'enrollment_id': enrollment.id,
        }
        
        enrollment.refresh_from_db()
        
        response = self.client.post('/api/v0/courses/team/join/', data=request_data)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        enrollment.refresh_from_db()
        
        self.assertEqual(enrollment.team.id, team.id)
        