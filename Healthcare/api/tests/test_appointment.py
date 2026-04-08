from django.utils import timezone
from datetime import timedelta
from rest_framework import status

from api.models import Appointment, Prescription, Medicine, Bill
from .base import BaseAPITestCase


class AppointmentTests(BaseAPITestCase):

    def test_patient_can_create_appointment(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        future_date = timezone.now() + timedelta(days=1)

        data = {
            "doctor": self.doctor.id,
            "date": future_date
        }

        response = self.client.post(self.appointment_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(Appointment.objects.first().user, self.patient_user)

    def test_past_appointment_should_fail(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        past_date = timezone.now() - timedelta(days=1)

        data = {
            "doctor": self.doctor.id,
            "date": past_date
        }

        response = self.client.post(self.appointment_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', response.data)

    def test_duplicate_same_slot_should_fail(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        future_date = timezone.now() + timedelta(days=2)

        Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=future_date,
            status='Pending'
        )

        data = {
            "doctor": self.doctor.id,
            "date": future_date
        }

        response = self.client.post(self.appointment_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', response.data)

    def test_unauthenticated_user_cannot_create_appointment(self):
        future_date = timezone.now() + timedelta(days=1)

        data = {
            "doctor": self.doctor.id,
            "date": future_date
        }

        response = self.client.post(self.appointment_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patient_can_view_own_appointments(self):
        Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Pending'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.get(self.appointment_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_admin_can_view_all_appointments(self):
        Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Pending'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get(self.appointment_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 1)
        else:
            self.assertGreaterEqual(len(response.data), 1)

    def test_patient_can_update_own_pending_appointment(self):
        appointment = Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Pending'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        new_date = timezone.now() + timedelta(days=3)

        data = {
            "date": new_date,
        }

        response = self.client.patch(f'{self.appointment_url}{appointment.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patient_cannot_update_approved_appointment(self):
        appointment = Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Approved'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        new_date = timezone.now() + timedelta(days=3)

        data = {
            "date": new_date
        }

        response = self.client.patch(f'{self.appointment_url}{appointment.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
 
    def test_patient_cannot_update_other_users_appointment(self):
        from django.contrib.auth.models import User

        other_user = User.objects.create_user(username='otheruser', password='other123')

        appointment = Appointment.objects.create(
            user=other_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Pending'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        new_date = timezone.now() + timedelta(days=3)

        data = {
            "date": new_date
        }

        response = self.client.patch(f'{self.appointment_url}{appointment.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_patient_cannot_change_status(self):
        appointment = Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Pending'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        data = {
            "status": "Approved"
        }

        response = self.client.patch(f'{self.appointment_url}{appointment.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)

    def test_admin_can_update_status(self):
        appointment = Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Pending'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        data = {
            "doctor": self.doctor.id,
            "date": appointment.date,
            "status": "Approved"
        }

        response = self.client.put(f'{self.appointment_url}{appointment.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'Approved')

    def test_admin_cannot_finish_without_prescription(self):
        appointment = Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Approved'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        data = {
            "doctor": self.doctor.id,
            "date": appointment.date,
            "status": "Finished"
        }

        response = self.client.put(f'{self.appointment_url}{appointment.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data)

    def test_admin_cannot_finish_without_bill(self):
        appointment = Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Approved'
        )

        medicine = Medicine.objects.create(
            name='Paracetamol',
            
            price=10
        )

        Prescription.objects.create(
            appointment=appointment,
            medication=medicine
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        data = {
            "doctor": self.doctor.id,
            "date": appointment.date,
            "status": "Finished"
        }

        response = self.client.put(f'{self.appointment_url}{appointment.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data)

    def test_admin_can_finish_with_prescription_and_bill(self):
        appointment = Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Approved'
        )

        medicine = Medicine.objects.create(
            name='Paracetamol',
            price=10
        )

        prescription = Prescription.objects.create(
            appointment=appointment,
            medication=medicine
        )

        Bill.objects.create(
            prescription=prescription,
            quantity=2,
            total_price=20
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        data = {
            "doctor": self.doctor.id,
            "date": appointment.date,
            "status": "Finished"
        }

        response = self.client.put(f'{self.appointment_url}{appointment.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'Finished')

    def test_patient_can_delete_own_appointment_if_no_prescription(self):
        appointment = Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Pending'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        response = self.client.delete(f'{self.appointment_url}{appointment.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Appointment.objects.filter(id=appointment.id).exists())

    def test_cannot_delete_appointment_if_prescription_exists(self):
        appointment = Appointment.objects.create(
            user=self.patient_user,
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            status='Approved'
        )

        medicine = Medicine.objects.create(
            name='Paracetamol',
            
            price=10
        )

        Prescription.objects.create(
            appointment=appointment,
            medication=medicine
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        response = self.client.delete(f'{self.appointment_url}{appointment.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 
        self.assertTrue(Appointment.objects.filter(id=appointment.id).exists())
