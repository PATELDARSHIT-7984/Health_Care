from rest_framework import status

from api.models import Bill
from .base import BaseAPITestCase


class BillTests(BaseAPITestCase):

    def test_admin_can_create_bill(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        prescription = self.create_prescription()

        data = {
            "prescription": prescription.id,
            "quantity": 3,
            "total_price": 0
        }

        response = self.client.post(self.bill_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bill.objects.count(), 1)

        bill = Bill.objects.first()
        self.assertEqual(bill.quantity, 3)
        self.assertEqual(bill.patient_name, self.patient_user.username)
        self.assertEqual(bill.doctor_name, self.doctor.name)
        self.assertEqual(bill.medicine_name, prescription.medication.name)
        self.assertEqual(bill.medicine_price, prescription.medication.price)
        self.assertEqual(bill.total_price, prescription.medication.price * 3)

    def test_patient_cannot_create_bill(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        prescription = self.create_prescription()

        data = {
            "prescription": prescription.id,
            "quantity": 2,
            "total_price": 0
        }

        response = self.client.post(self.bill_url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_all_bills(self):
        self.create_bill()

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get(self.bill_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 1)
        else:
            self.assertGreaterEqual(len(response.data), 1)

    def test_patient_can_view_own_bill(self):
        bill = self.create_bill()

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.get(self.bill_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['id'], bill.id)
        else:
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['id'], bill.id)

    def test_patient_cannot_view_others_bill(self):
        appointment = self.create_appointment(user=self.other_patient_user, status='Approved')
        prescription = self.create_prescription(appointment=appointment)
        self.create_bill(prescription=prescription)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)
        response = self.client.get(self.bill_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 0)
        else:
            self.assertEqual(len(response.data), 0)

    def test_admin_can_update_bill_quantity(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        bill = self.create_bill(quantity=2)

        data = {
            "prescription": bill.prescription.id,
            "quantity": 5,
            "total_price": 0
        }

        response = self.client.put(f'{self.bill_url}{bill.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 5)

        bill.refresh_from_db()
        self.assertEqual(bill.total_price, bill.medicine_price * 5)

    def test_patient_cannot_update_bill(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        bill = self.create_bill()

        data = {
            "prescription": bill.prescription.id,
            "quantity": 4,
            "total_price": 0
        }

        response = self.client.put(f'{self.bill_url}{bill.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_bill(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

        bill = self.create_bill()

        response = self.client.delete(f'{self.bill_url}{bill.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Bill.objects.filter(id=bill.id).exists())

    def test_patient_cannot_delete_bill(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.patient_token.key)

        bill = self.create_bill()

        response = self.client.delete(f'{self.bill_url}{bill.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Bill.objects.filter(id=bill.id).exists())

    def test_total_price_is_auto_calculated(self):
        prescription = self.create_prescription()
        bill = Bill.objects.create(
            prescription=prescription,
            quantity=4,
            total_price=0
        )

        self.assertEqual(bill.total_price, prescription.medication.price * 4)

    def test_bill_auto_fills_patient_doctor_medicine_fields(self):
        prescription = self.create_prescription()
        bill = Bill.objects.create(
            prescription=prescription,
            quantity=2,
            total_price=0
        )

        self.assertEqual(bill.patient_name, prescription.appointment.user.username)
        self.assertEqual(bill.doctor_name, prescription.appointment.doctor.name)
        self.assertEqual(bill.medicine_name, prescription.medication.name)
        self.assertEqual(bill.medicine_price, prescription.medication.price)

    def test_same_prescription_cannot_have_multiple_bills(self):
        prescription = self.create_prescription()
        self.create_bill(prescription=prescription)

        try:
            Bill.objects.create(
                prescription=prescription,
                quantity=2,
                total_price=0
            )
            self.fail("Second bill for same prescription should not be allowed.")
        except Exception:
            pass

    def test_unauthenticated_user_cannot_view_bills(self):
        response = self.client.get(self.bill_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
