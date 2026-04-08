from rest_framework import status
from api.models import Doctor

from .base import BaseAPITestCase


class DoctorTests(BaseAPITestCase):

    def test_admin_can_create_doctor(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        data = {
            "name": "Dr. House",
            "specialization": "Neurology",
            "experience": 15,
            "hospital": "Care Hospital"
        }

        response = self.client.post(self.doctor_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Doctor.objects.filter(name='Dr. House').exists())

    def test_patient_cannot_create_doctor(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        data = {
            "name": "Dr. Fake",
            "specialization": "Skin",
            "experience": 5,
            "hospital": "Fake Hospital"
        }

        response = self.client.post(self.doctor_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_view_doctors(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        response = self.client.get(self.doctor_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_unauthenticated_user_cannot_view_doctors(self):
        response = self.client.get(self.doctor_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def admin_user_can_update_doctor(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        data = {
            "name": "Dr. Strange Updated",
            "specialization": "Cardiology",
            "experience": 12,
            "hospital": "City Hospital"
        }

        response = self.client.put(f"{self.doctor_url}{self.doctor.id}/", data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.name, "Dr. Strange Updated")

    def patient_user_cannot_update_doctor(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        data = {
            "name": "Dr. Strange Updated",
            "specialization": "Cardiology",
            "experience": 12,
            "hospital": "City Hospital"
        }

        response = self.client.put(f"{self.doctor_url}{self.doctor.id}/", data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def admin_user_can_delete_doctor(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        response = self.client.delete(f"{self.doctor_url}{self.doctor.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Doctor.objects.filter(id=self.doctor.id).exists())
    
