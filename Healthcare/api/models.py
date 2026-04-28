from django.db import models
from django.contrib.auth.models import User
import random
class Health(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10, null=True, blank=True)
    Email = models.EmailField(null=True,blank=True)

    def __str__(self):
        return self.name

class Patient(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

class Doctor(models.Model):
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    experience = models.PositiveIntegerField()
    hospital = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Finished', 'Finished'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.user.username} - Dr. {self.doctor.name} ({self.date})"

class Medicine(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()

    def __str__(self):
        return self.name

class Prescription(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    medication = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.appointment.user.username} - dr. {self.appointment.doctor.name} - {self.medication.name}"

class Bill(models.Model):

    prescription = models.OneToOneField(Prescription, on_delete=models.SET_NULL, null=True,blank=True)

    quantity = models.PositiveIntegerField(default=1)
    total_price = models.FloatField()
    billing_date = models.DateTimeField(auto_now_add=True)

    patient_name = models.CharField(max_length=100, blank=True)
    doctor_name = models.CharField(max_length=100, blank=True)
    medicine_name = models.CharField(max_length=100, blank=True)
    medicine_price = models.FloatField(blank=True, null=True)    

    def save(self, *args, **kwargs):
        if self.prescription:
            self.patient_name = self.prescription.appointment.user.username
            self.doctor_name = self.prescription.appointment.doctor.name
            self.medicine_name = self.prescription.medication.name
            self.medicine_price = self.prescription.medication.price
            self.total_price = self.medicine_price * self.quantity
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Bill for {self.medicine_name} - Total: {self.total_price}"
    
class OTP(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    otp = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expire(self):
        from django.utils import timezone
        return (timezone.now()-self.created_at).seconds > 300