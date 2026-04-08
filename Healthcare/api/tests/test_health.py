from rest_framework import status

from api.models import Health
from .base import BaseAPITestCase


class HealthTests(BaseAPITestCase):

    def test_create_health_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        data = {
            'name': 'John Doe',
            'no': '12',
            'Email': 'john.doe@example.com'
        }

        response = self.client.post(self.health_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Health.objects.count(), 1)
        self.assertEqual(Health.objects.first().user, self.patient_user)

    def test_patient_can_view_own_health_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        Health.objects.create(
            user=self.patient_user,
            name='John Doe',
            no='12',
            Email='john.doe@example.com'
        )

        response = self.client.get(self.health_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # ✅ CHANGED: because paginated response returns results inside 'results'
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_patient_cannot_view_others_health_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        Health.objects.create(
            user=self.admin_user,
            name='Admin User',
            no='34',
            Email='admin.user@example.com'
        )

        response = self.client.get(self.health_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 0)
        else:
            self.assertEqual(len(response.data), 0)

    def test_duplicate_email_for_same_user_should_fail(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        Health.objects.create(
            user=self.patient_user,
            name='John Doe',
            no='12',
            Email='john.doe@example.com'
        )

        data = {
            'name': 'John Wick',
            'no': '11',
            'Email': 'john.doe@example.com'
        }

        response = self.client.post(self.health_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Health.objects.count(), 1)

    def test_unauthenticated_user_cannot_access_health_profile(self):
        response = self.client.get(self.health_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
