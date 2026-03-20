from django.http import HttpResponse
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from .models import Appointment, Doctor, Health
from .serializers import AppointmentSerializer, DoctorSerializer, Healthserializer, RegisterSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permission import IsOwnerOrReadOnly,IsAdminOrReadOnly
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
    queryset = Health.objects.all()
    serializer_class = RegisterSerializer

class AppointmentView(ModelViewSet):

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        if self.request.user.is_staff:
            return Appointment.objects.all()
        return Appointment.objects.filter(user=user)
 
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admin can update the appointment status.")
        serializer.save()

    
def home(request):
    return HttpResponse("Welcome to HealthcareCenter")