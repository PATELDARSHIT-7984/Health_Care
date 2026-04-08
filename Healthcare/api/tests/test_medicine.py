from rest_framework import status
from api.models import Medicine
from .base import BaseAPITestCase


class MedicineTests(BaseAPITestCase):

    def test_admin_can_create_medicine(self):
        data = {
            'name': 'Aspirin',
            'price': 9.99
        }

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.post('/api/medicine/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Aspirin')
        self.assertEqual(float(response.data['price']), 9.99)

    def test_patient_cannot_create_medicine(self):
        data = {
            'name': 'Ibuprofen',
            'price': 14.99
        }

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.post(self.medicine_url, data)
    
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_view_medicines(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.get(self.medicine_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_view_medicines(self):
        response = self.client.get(self.medicine_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_update_medicine(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        medicine = self.create_medicine(name='Aspirin', price=9.99)

        data = {
            'name': 'Aspirin Updated',
            'price': 12.99
        }

        response = self.client.put(f'{self.medicine_url}{medicine.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Aspirin Updated')
        self.assertEqual(float(response.data['price']), 12.99)

    def test_patient_cannot_update_medicine(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        medicine = self.create_medicine(name='Aspirin', price=9.99)

        data = {
            'name': 'Aspirin Updated',
            'price': 12.99
        }

        response = self.client.put(f'{self.medicine_url}{medicine.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_medicine(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        medicine = self.create_medicine(name='Aspirin', price=9.99)
        response = self.client.delete(f'{self.medicine_url}{medicine.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Medicine.objects.filter(id=medicine.id).exists())

    def test_patient_cannot_delete_medicine(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        medicine = self.create_medicine(name='Aspirin', price=9.99)
        response = self.client.delete(f'/api/medicine/{medicine.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Medicine.objects.filter(id=medicine.id).exists())
