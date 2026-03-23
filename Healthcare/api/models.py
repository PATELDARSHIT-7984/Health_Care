from django.db import models
from django.contrib.auth.models import User

class Health(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    no = models.IntegerField(null=True,blank=True)
    Email = models.CharField(null=True,blank=True)

    def __str__(self):
        return self.name
    
class Patient(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

class Doctor(models.Model):
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    experience = models.IntegerField()
    hospital = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateTimeField()
    status = models.CharField(max_length=20, default='Scheduled')

    def __str__(self):
        return f"{self.user.username} - Dr. {self.doctor.name} ({self.date})"

class Prescription(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    medication = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)

    def __str__(self):
        return self.medication
    
class Medicine(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField()
    