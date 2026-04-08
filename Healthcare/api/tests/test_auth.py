from django.contrib.auth.models import User
from rest_framework import status

from .base import BaseAPITestCase


class AuthTests(BaseAPITestCase):

    def test_register_user(self):
        data = {
            "username": "newpatient",
            "password": "newpass123",
            "confirm_password": "newpass123"
        }

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newpatient').exists())

    def test_login_user(self):
        data = {
            "username": "patient1",
            "password": "patient123"
        }

        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'patient1')
        self.assertEqual(response.data['is_staff'], False)

    def test_current_user_api(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        response = self.client.get(self.current_user_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'patient1')
        self.assertEqual(response.data['is_staff'], False)

    def test_change_password(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        data = {
            "old_password": "patient123",
            "new_password": "newsecure123",
            "confirm_password": "newsecure123"
        }

        response = self.client.post(self.change_password_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.patient_user.refresh_from_db()
        self.assertTrue(self.patient_user.check_password('newsecure123'))

    def test_change_password_wrong_old_password(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        data = {
            "old_password": "wrongpassword",
            "new_password": "newsecure123",
            "confirm_password": "newsecure123"
        }

        response = self.client.post(self.change_password_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)
