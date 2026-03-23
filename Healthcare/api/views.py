from django.http import HttpResponse
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from .models import Appointment, Doctor, Health, Medicine, Patient, Prescription
from .serializers import AppointmentSerializer, DoctorSerializer, Healthserializer, MedicineSerializer, PrescriptionSerializer, RegisterSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permission import IsOwnerOrReadOnly,IsAdminOrReadOnly, IsOwnerOrAdmin
from django.db.models import Q
from drf_yasg import openapi
from rest_framework.exceptions import PermissionDenied
# we use this when we use JWTAuthentication
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

class HealthcenterView(ModelViewSet):
    queryset = Health.objects.all()
    serializer_class = Healthserializer
    # for Session or JWT this code remains a same for both Authenticatoin
    permission_classes = [IsAuthenticated,IsOwnerOrReadOnly]

    def get_queryset(self):
        return Health.objects.filter(Q(user=self.request.user))
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DoctorView(ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated,IsAdminOrReadOnly]  

class RegisterView(ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Patient.objects.all()
    serializer_class = RegisterSerializer

class AppointmentView(ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if self.request.user.is_staff:
            return Appointment.objects.all()
        return Appointment.objects.filter(user=user)
 
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def get_serializer_context(self):
        return {"request": self.request}
    
    def update(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("Only admin can approve/reject appointment")

        return super().update(request, *args, **kwargs)
  
class PrescriptionView(ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if self.request.user.is_staff:
            return Prescription.objects.all()
        else:
            return Prescription.objects.filter(appointment__user=user)
    
    def get_serializer_context(self):
        return {"request": self.request}
    
    def create(self, request, *args, **kwargs):
        
        if not request.user.is_staff:
            raise PermissionDenied("Only admin can create prescription")
        return super().create(request, *args, **kwargs)
    
class MedicineView(ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

def home(request):
    return HttpResponse("Welcome to HealthcareCenter")