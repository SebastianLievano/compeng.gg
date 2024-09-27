from django.test import TestCase
from unittest import mock
import courses.models as db
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from tests.utils import create_offering

class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = self.get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_dashboard_view(self):
        course_name='ece496'
        offering_name='fall 2024'
        
        offering = create_offering(
            course_name=course_name,
            offering_name=offering_name
        )
        
        student_role = db.Role.objects.create(kind=db.Role.Kind.STUDENT, offering=offering)
        
        enrollment = db.Enrollment.objects.create(
            user=self.user,
            role=student_role,
        )
        
        response = self.client.get('/api/v0/dashboard/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        
        expected_offerings = [
            {
                'id': str(offering.id),
                'name': str(offering),
                'slug': offering.course.slug,
                'role': str(enrollment.role),
            }
        ]
        
        self.assertEqual(response.data['offerings'], expected_offerings)

