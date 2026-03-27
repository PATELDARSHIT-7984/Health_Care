from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from .models import Appointment, Bill, Doctor, Health, Medicine, Prescription, User
from .serializers import AppointmentSerializer, BillSerializer, DoctorSerializer, Healthserializer, MedicineSerializer, PrescriptionSerializer, RegisterSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permission import IsOwnerOrReadOnly,IsAdminOrReadOnly, IsOwnerOrAdmin
from django.db.models import Q, Sum
from rest_framework.exceptions import PermissionDenied

# we use this when we use JWTAuthentication
# from rest_framework import status
# from drf_yasg.utils import swagger_auto_s`chema


class HealthcenterView(ModelViewSet):
    permission_classes = [IsAuthenticated,IsOwnerOrReadOnly]
    queryset = Health.objects.all()
    serializer_class = Healthserializer
    # for Session or JWT this code remains a same for both Authenticatoin

    filterset_fields = ['Email']
    search_fields = ['name', 'Email']
    ordering_fields = ['name', 'Email']

    def get_queryset(self):
        return Health.objects.filter(Q(user=self.request.user))
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DoctorView(ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated,IsAdminOrReadOnly]  

    filterset_fields = ['specialization']
    search_fields = ['name', 'specialization']
    ordering_fields = ['name', 'experience']

class RegisterView(ModelViewSet):
    permission_classes = [AllowAny,IsAdminOrReadOnly]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    filterset_fields = ['username']
    search_fields = ['username']
    ordering_fields = ['username']

class AppointmentView(ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    filterset_fields = ['status', 'doctor','date']
    search_fields = ['doctor__name', 'user__username','status']
    ordering_fields = ['date', 'doctor__name']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
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

    filterset_fields = ['appointment','medication']
    search_fields = ['appointment__user__username', 'appointment__doctor__name', 'medication__name']
    ordering_fields = ['appointment']

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

    filterset_fields = ['price']
    search_fields = ['name']
    ordering_fields = ['name', 'price']

class BillView(ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    filterset_fields = ['billing_date','prescription']
    search_fields = ['prescription__appointment__user__username', 'prescription__appointment__doctor__name', 'prescription__medication__name']
    ordering_fields = ['billing_date', 'total_price','quantity']

    def get_queryset(self):
        user = self.request.user
        if self.request.user.is_staff:
            return Bill.objects.all()
        else:
            return Bill.objects.filter(prescription__appointment__user=user)
    
    def get_serializer_context(self):
        return {"request": self.request}
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("Only admin can create bill")
        return super().create(request, *args, **kwargs)

class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get(self, request):
        total_users = User.objects.count()
        total_doctors = Doctor.objects.count()
        total_appointments = Appointment.objects.count()
        total_medicines = Medicine.objects.count()
        total_profiles = Health.objects.count()

        approved_appointments = Appointment.objects.filter(status='Approved').count()
        pending_appointments = Appointment.objects.filter(status='Pending').count()
        rejected_appointments = Appointment.objects.filter(status='Rejected').count()

        total_bills = Bill.objects.count()
        total_prescriptions = Prescription.objects.count()

        total_revenue = Bill.objects.aggregate(total = Sum('total_price'))['total'] or 0

        data = {
            "total_users": total_users,
            "total_doctors": total_doctors,
            "total_appointments": total_appointments,
            "total_medicines": total_medicines,
            "total_profiles": total_profiles,
            "approved_appointments": approved_appointments,
            "pending_appointments": pending_appointments,
            "rejected_appointments": rejected_appointments,
            "total_bills": total_bills,
            "total_prescriptions": total_prescriptions,
            "total_revenue": total_revenue,
        }
        return Response(data)

class PatientDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        my_appointments = Appointment.objects.filter(user=user).count()
        my_approved_appointments = Appointment.objects.filter(user=user, status='Approved').count()
        my_pending_appointments = Appointment.objects.filter(user=user, status='Pending').count()
        my_rejected_appointments = Appointment.objects.filter(user=user, status='Rejected').count()

        my_prescriptions = Prescription.objects.filter(appointment__user=user).count()
        my_bills = Bill.objects.filter(prescription__appointment__user=user).count()

        my_total_bill_amount = Bill.objects.filter(
            prescription__appointment__user=user
        ).aggregate(total=Sum('total_price'))['total'] or 0

        data = {
            "username": user.username,
            "my_appointments": my_appointments,
            "my_approved_appointments": my_approved_appointments,
            "my_pending_appointments": my_pending_appointments,
            "my_rejected_appointments": my_rejected_appointments,
            "my_prescriptions": my_prescriptions,
            "my_bills": my_bills,
            "my_total_bill_amount": my_total_bill_amount,
        }

        return Response(data)
      
def home(request):
    return HttpResponse("Welcome to HealthcareCenter")