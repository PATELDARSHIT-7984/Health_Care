from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from .models import Appointment, Bill, Doctor, Health, Medicine, Prescription, User
from .serializers import AppointmentSerializer, BillSerializer, DoctorSerializer, Healthserializer, MedicineSerializer, PrescriptionSerializer, RegisterSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permission import IsOwnerOrReadOnly, IsAdminOrReadOnly, IsOwnerOrAdmin
from django.db.models import Q, Sum
from rest_framework.exceptions import PermissionDenied


class HealthcenterView(ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = Health.objects.all()
    serializer_class = Healthserializer

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
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    filterset_fields = ['specialization']
    search_fields = ['name', 'specialization']
    ordering_fields = ['name', 'experience']

    def get_serializer_context(self):
        return {"request": self.request}

    def destroy(self, request, *args, **kwargs):
        doctor = self.get_object()

        # 1) Block delete if doctor has Pending or Approved appointments
        active_appointments = Appointment.objects.filter(
            doctor=doctor,
            status__in=['Pending', 'Approved']
        ).exists()

        if active_appointments:
            raise PermissionDenied(
                "Doctor cannot be deleted because they still have pending or approved appointments."
            )

        # 2) Block delete if doctor has Finished appointments but prescription not created
        finished_without_prescription = Appointment.objects.filter(
            doctor=doctor,
            status='Finished',
            prescription__isnull=True
        ).exists()

        if finished_without_prescription:
            raise PermissionDenied(
                "Doctor cannot be deleted because some finished appointments still do not have prescriptions."
            )

        # 3) Block delete if doctor has Finished appointments with prescription but bill not created
        finished_with_prescription_but_no_bill = Prescription.objects.filter(
            appointment__doctor=doctor,
            appointment__status='Finished',
            bill__isnull=True
        ).exists()

        if finished_with_prescription_but_no_bill:
            raise PermissionDenied(
                "Doctor cannot be deleted because some finished appointments still do not have bills."
            )

        return super().destroy(request, *args, **kwargs)


class RegisterView(ModelViewSet):
    permission_classes = [AllowAny, IsAdminOrReadOnly]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    filterset_fields = ['username']
    search_fields = ['username']
    ordering_fields = ['username']


class AppointmentView(ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    filterset_fields = ['status', 'doctor', 'date']
    search_fields = ['doctor__name', 'user__username', 'status']
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
        appointment = self.get_object()

        # Patient can only edit their own pending appointment
        if not request.user.is_staff:
            if appointment.user != request.user:
                raise PermissionDenied("You can only update your own appointment.")

            if appointment.status != 'Pending':
                raise PermissionDenied("You can only update pending appointments.")

        # Admin cannot edit finished appointment if prescription exists
        if request.user.is_staff:
            if appointment.status == 'Finished' and Prescription.objects.filter(appointment=appointment).exists():
                raise PermissionDenied(
                    "Finished appointment with prescription should not be edited because it is part of patient history."
                )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        appointment = self.get_object()

        # Do not allow deleting if prescription already exists
        if Prescription.objects.filter(appointment=appointment).exists():
            raise PermissionDenied(
                "Cannot delete appointment because prescription already exists."
            )

        return super().destroy(request, *args, **kwargs)

class PrescriptionView(ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    filterset_fields = ['appointment', 'medication']
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

    def update(self, request, *args, **kwargs):
        prescription = self.get_object()

        # If bill already exists, don't allow changing prescription history
        if Bill.objects.filter(prescription=prescription).exists():
            raise PermissionDenied(
                "Cannot update prescription because bill already exists and it is part of patient history."
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        prescription = self.get_object()

        # Do not allow deleting if bill already exists
        if Bill.objects.filter(prescription=prescription).exists():
            raise PermissionDenied(
                "Cannot delete prescription because bill already exists."
            )

        return super().destroy(request, *args, **kwargs)

class MedicineView(ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    filterset_fields = ['price']
    search_fields = ['name']
    ordering_fields = ['name', 'price']

    def destroy(self, request, *args, **kwargs):
        medicine = self.get_object()

        # Block delete if medicine is used in any prescription
        if Prescription.objects.filter(medication=medicine).exists():
            raise PermissionDenied(
                "Cannot delete medicine because it is already used in prescriptions."
            )

        return super().destroy(request, *args, **kwargs)

class BillView(ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    filterset_fields = ['billing_date', 'prescription']
    search_fields = ['prescription__appointment__user__username', 'prescription__appointment__doctor__name', 'prescription__medication__name']
    ordering_fields = ['billing_date', 'total_price', 'quantity']

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

    def update(self, request, *args, **kwargs):
        bill = self.get_object()

        # Prevent changing bill history too much
        if bill.prescription is None:
            raise PermissionDenied(
                "This bill is already archived and cannot be edited."
            )

        return super().update(request, *args, **kwargs)

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
        finished_appointments = Appointment.objects.filter(status='Finished').count()

        total_bills = Bill.objects.count()
        total_prescriptions = Prescription.objects.count()

        total_revenue = Bill.objects.aggregate(total=Sum('total_price'))['total'] or 0

        data = {
            "total_users": total_users,
            "total_doctors": total_doctors,
            "total_appointments": total_appointments,
            "total_medicines": total_medicines,
            "total_profiles": total_profiles,
            "approved_appointments": approved_appointments,
            "pending_appointments": pending_appointments,
            "rejected_appointments": rejected_appointments,
            "finished_appointments": finished_appointments,
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
        my_finished_appointments = Appointment.objects.filter(user=user, status='Finished').count()

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
            "my_finished_appointments": my_finished_appointments,
            "my_prescriptions": my_prescriptions,
            "my_bills": my_bills,
            "my_total_bill_amount": my_total_bill_amount,
        }

        return Response(data)

def home(request):
    return HttpResponse("Welcome to HealthcareCenter")