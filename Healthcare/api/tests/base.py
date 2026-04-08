from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from api.models import Bill, Doctor, Appointment, Medicine, Prescription


class BaseAPITestCase(APITestCase):
    def setUp(self):
        # Admin user
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='admin123'
        )
        self.admin_user.is_staff = True
        self.admin_user.save()

        # Normal patient user
        self.patient_user = User.objects.create_user(
            username='patient1',
            password='patient123'
        )

        # Another patient user (useful for permission tests)
        self.other_patient_user = User.objects.create_user(
            username='patient2',
            password='patient456'
        )

        # Tokens
        self.admin_token = Token.objects.create(user=self.admin_user)
        self.patient_token = Token.objects.create(user=self.patient_user)
        self.other_patient_token = Token.objects.create(user=self.other_patient_user)

        # Common doctor
        self.doctor = Doctor.objects.create(
            name='Dr. Strange',
            specialization='Cardiology',
            experience=10,
            hospital='City Hospital'
        )

        # Common URLs
        self.register_url = '/api/register/'
        self.login_url = '/api/login/'
        self.current_user_url = '/api/current_user/'
        self.change_password_url = '/api/change_password/'
        self.doctor_url = '/api/doctor/'
        self.appointment_url = '/api/appointment/'
        self.prescription_url = '/api/prescription/'
        self.medicine_url = '/api/medicine/'
        self.bill_url = '/api/bill/'
        self.health_url = '/api/healthcenter/'

    # -----------------------------
    # Helper Methods
    # -----------------------------

    def create_future_datetime(self, days=1):
        return timezone.now() + timedelta(days=days)

    def create_appointment(self, user=None, doctor=None, date=None, status='Pending'):
        if user is None:
            user = self.patient_user
        if doctor is None:
            doctor = self.doctor
        if date is None:
            date = timezone.now() + timedelta(days=2)

        return Appointment.objects.create(
            user=user,
            doctor=doctor,
            date=date,
            status=status
        )

    def create_medicine(self, name='Paracetamol', price=10):
        return Medicine.objects.create(
            name=name,
            price=price
        )

    def create_prescription(self, appointment=None, medication=None, dosage='2 times a day'):
        if appointment is None:
            appointment = self.create_appointment(status='Approved')
        if medication is None:
            medication = self.create_medicine()

        return Prescription.objects.create(
            appointment=appointment,
            medication=medication,
            dosage=dosage
        )

    def create_bill(self, prescription=None, quantity=1):
        if prescription is None:
            prescription = self.create_prescription()
        
        return Bill.objects.create(
            prescription=prescription,
            quantity=quantity,
            total_price=0
        )