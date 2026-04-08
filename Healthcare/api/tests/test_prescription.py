from rest_framework import status
from api.models import Prescription, Bill
from .base import BaseAPITestCase


class PrescriptionTests(BaseAPITestCase):

    def test_admin_can_create_prescription(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        appointment = self.create_appointment(status='Approved')
        medicine = self.create_medicine()

        data = {
            "appointment": appointment.id,
            "medication": medicine.id,
            "dosage": "Take twice daily"
        }

        response = self.client.post(self.prescription_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Prescription.objects.count(), 1)
        self.assertEqual(response.data['dosage'], "Take twice daily")

    def test_patient_cannot_create_prescription(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        appointment = self.create_appointment(status='Approved')
        medicine = self.create_medicine()

        data = {
            "appointment": appointment.id,
            "medication": medicine.id,
            "dosage": "Take once daily"
        }

        response = self.client.post(self.prescription_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_prescription_for_unapproved_appointment_should_fail(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        appointment = self.create_appointment(status='Pending')
        medicine = self.create_medicine()

        data = {
            "appointment": appointment.id,
            "medication": medicine.id,
            "dosage": "Take after food"
        }

        response = self.client.post(self.prescription_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patient_can_view_own_prescriptions(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        appointment = self.create_appointment(user=self.patient_user, status='Approved')
        medicine = self.create_medicine()
        self.create_prescription(appointment=appointment, medication=medicine)

        response = self.client.get(self.prescription_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_admin_can_view_all_prescriptions(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        appointment = self.create_appointment(status='Approved')
        medicine = self.create_medicine()
        self.create_prescription(appointment=appointment, medication=medicine)

        response = self.client.get(self.prescription_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 1)
        else:
            self.assertGreaterEqual(len(response.data), 1)

    def test_admin_can_update_prescription_if_bill_not_exists(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        prescription = self.create_prescription()

        new_medicine = self.create_medicine(name='Ibuprofen', price=20)

        data = {
            "appointment": prescription.appointment.id,
            "medication": new_medicine.id,
            "dosage": "Updated dosage"
        }

        response = self.client.put(f'{self.prescription_url}{prescription.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dosage'], "Updated dosage")

    def test_admin_can_delete_prescription_if_bill_not_exists(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        prescription = self.create_prescription()

        response = self.client.delete(f'{self.prescription_url}{prescription.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Prescription.objects.filter(id=prescription.id).exists())

    def test_patient_cannot_delete_prescription(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        prescription = self.create_prescription()

        response = self.client.delete(f'{self.prescription_url}{prescription.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_update_prescription_if_bill_exists(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        prescription = self.create_prescription()
        Bill.objects.create(
            prescription=prescription,
            quantity=2,
            total_price=20
        )

        new_medicine = self.create_medicine(name='NewMed', price=15)

        data = {
            "appointment": prescription.appointment.id,
            "medication": new_medicine.id,
            "dosage": "Cannot update this"
        }

        response = self.client.put(f'{self.prescription_url}{prescription.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_delete_prescription_if_bill_exists(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        prescription = self.create_prescription()
        Bill.objects.create(
            prescription=prescription,
            quantity=2,
            total_price=20
        )

        response = self.client.delete(f'{self.prescription_url}{prescription.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Prescription.objects.filter(id=prescription.id).exists())
