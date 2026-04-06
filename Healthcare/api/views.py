from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .models import Appointment, Bill, Doctor, Health, Medicine, Prescription, User
from .serializers import AppointmentSerializer, BillSerializer, DoctorSerializer, Healthserializer, MedicineSerializer, PrescriptionSerializer, RegisterSerializer, LoginSerializer, CurrentUserSerializer, ChangePasswordSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permission import IsOwnerOrReadOnly, IsAdminOrReadOnly
from django.db.models import Q, Sum, Count, Avg, Max
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


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

    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    filterset_fields = ['username']
    search_fields = ['username']
    ordering_fields = ['username']

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrReadOnly()]
    
class LoginView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def get(self, request):
        serializer = self.get_serializer()
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                "message": "Login successful!",
                "token": token.key,
                "username": user.username,
                "is_staff": user.is_staff
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        Token.objects.filter(user=user).delete()
        return Response({"message": "Logout successful!"}, status=status.HTTP_200_OK)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data)

class ChangePasswordView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def get(self, request):
        serializer = self.get_serializer()
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer = self.get_serializer(data=request.data, context={'request': request})

            user = request.user
            new_password = serializer.validated_data['new_password']

            user.set_password(new_password)
            user.save()

            Token.objects.filter(user=user).delete()
            new_token = Token.objects.create(user=user)

            return Response({"message": "Password changed successfully!", "new_token": new_token.key}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only admin can access admin dashboard.")

        total_users = User.objects.count()
        total_doctors = Doctor.objects.count()
        total_appointments = Appointment.objects.count()
        total_medicines = Medicine.objects.count()
        total_profiles = Health.objects.count()
        total_prescriptions = Prescription.objects.count()
        total_bills = Bill.objects.count()

        approved_appointments = Appointment.objects.filter(status='Approved').count()
        pending_appointments = Appointment.objects.filter(status='Pending').count()
        rejected_appointments = Appointment.objects.filter(status='Rejected').count()
        finished_appointments = Appointment.objects.filter(status='Finished').count()

        total_revenue = Bill.objects.aggregate(total=Sum('total_price'))['total'] or 0

        # Appointments that are approved but still waiting for prescription
        appointments_waiting_for_prescription = Appointment.objects.filter(
            status='Approved',
            prescription__isnull=True
        ).count()

        # Prescriptions that exist but bill is not created yet
        prescriptions_waiting_for_bill = Prescription.objects.filter(
            bill__isnull=True
        ).count()

        # Doctors still busy (Pending or Approved appointment exists)
        doctors_still_busy = Doctor.objects.filter(
            appointment__status__in=['Pending', 'Approved']
        ).distinct().count()

        # Doctors free to leave
        doctors_free_to_leave = total_doctors - doctors_still_busy

        # Recent records
        recent_appointments = Appointment.objects.order_by('-id')[:5]
        recent_prescriptions = Prescription.objects.order_by('-id')[:5]
        recent_bills = Bill.objects.order_by('-id')[:5]

        data = {
            "dashboard_type": "Admin Dashboard",

            "totals": {
                "total_users": total_users,
                "total_doctors": total_doctors,
                "total_appointments": total_appointments,
                "total_medicines": total_medicines,
                "total_profiles": total_profiles,
                "total_prescriptions": total_prescriptions,
                "total_bills": total_bills,
                "total_revenue": total_revenue,
            },

            "appointment_status_summary": {
                "approved_appointments": approved_appointments,
                "pending_appointments": pending_appointments,
                "rejected_appointments": rejected_appointments,
                "finished_appointments": finished_appointments,
            },

            "workflow_summary": {
                "appointments_waiting_for_prescription": appointments_waiting_for_prescription,
                "prescriptions_waiting_for_bill": prescriptions_waiting_for_bill,
                "doctors_still_busy": doctors_still_busy,
                "doctors_free_to_leave": doctors_free_to_leave,
            },

            "recent_activity": {
                "recent_appointments": [str(a) for a in recent_appointments],
                "recent_prescriptions": [str(p) for p in recent_prescriptions],
                "recent_bills": [str(b) for b in recent_bills],
            }
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

        my_latest_appointment = Appointment.objects.filter(user=user).order_by('-date').first()
        my_latest_prescription = Prescription.objects.filter(appointment__user=user).order_by('-id').first()
        my_latest_bill = Bill.objects.filter(prescription__appointment__user=user).order_by('-billing_date').first()

        # Appointments that are approved but still waiting for prescription
        my_waiting_prescription = Appointment.objects.filter(
            user=user,
            status='Approved',
            prescription__isnull=True
        ).count()

        # Prescriptions that are created but bill not yet generated
        my_waiting_bill = Prescription.objects.filter(
            appointment__user=user,
            bill__isnull=True
        ).count()

        data = {
            "dashboard_type": "Patient Dashboard",
            "username": user.username,

            "appointment_summary": {
                "my_appointments": my_appointments,
                "my_approved_appointments": my_approved_appointments,
                "my_pending_appointments": my_pending_appointments,
                "my_rejected_appointments": my_rejected_appointments,
                "my_finished_appointments": my_finished_appointments,
            },

            "medical_summary": {
                "my_prescriptions": my_prescriptions,
                "my_bills": my_bills,
                "my_total_bill_amount": my_total_bill_amount,
                "my_waiting_prescription": my_waiting_prescription,
                "my_waiting_bill": my_waiting_bill,
            },

            "latest_activity": {
                "my_latest_appointment": str(my_latest_appointment) if my_latest_appointment else "No appointment yet",
                "my_latest_prescription": str(my_latest_prescription) if my_latest_prescription else "No prescription yet",
                "my_latest_bill": str(my_latest_bill) if my_latest_bill else "No bill yet",
            }
        }

        return Response(data)

class DoctorAppoitmentReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only admin can access doctor appointment report.")

        doctor = Doctor.objects.annotate(
            total_appointments=Count('appointment'),
            pending_appointments=Count('appointment', filter=Q(appointment__status='Pending')),
            approved_appointments=Count('appointment', filter=Q(appointment__status='Approved')),
            rejected_appointments=Count('appointment', filter=Q(appointment__status='Rejected')),
            finished_appointments=Count('appointment', filter=Q(appointment__status='Finished')),
        ).order_by('name')

        data = []

        for doc in doctor:
            data.append({
                "doctor_id": doc.id,
                "doctor_name": doc.name,
                "specialization": doc.specialization,
                "hospital": doc.hospital,
                "total_appointments": doc.total_appointments,
                "pending_appointments": doc.pending_appointments,
                "approved_appointments": doc.approved_appointments,
                "rejected_appointments": doc.rejected_appointments,
                "finished_appointments": doc.finished_appointments,
            })

        return Response({
            "report name": "Doctor Appointment Report",
            "total_doctors": doctor.count(),
            "doctors_report": data
        })
    
class RevenueReportView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only admin can access revenue report.")

        total_bills = Bill.objects.count()
        revenue = Bill.objects.aggregate(
            total_revenue = Sum('total_price'),
            average_bill = Avg('total_price'),
            max_bill = Max('total_price'),
        )

        recent_bills = Bill.objects.order_by('-billing_date')[:5]

        bills_data = []

        for bill in recent_bills:
            bills_data.append({
                "bill_id": bill.id,
                "patient_name": bill.patient_name,
                "doctor_name": bill.doctor_name,
                "medicine_name": bill.medicine_name,
                "quantity": bill.quantity,
                "total_price": bill.total_price,
                "billing_date": bill.billing_date
            })

        return Response({
            "report_name": "Revenue Report",
            "summary": {
                "total_bills": total_bills,
                "total_revenue": revenue['total_revenue'] or 0,
                "average_bill_amount": revenue['average_bill'] or 0,
                "highest_bill_amount": revenue['max_bill'] or 0,
            },
            "recent_bills": bills_data
        })

class MedicineUsageReportView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request):

        if not request.user.is_staff:
            raise PermissionDenied("Only admin can access medicine usage report.")
        
        medicines = Medicine.objects.annotate(
            total_prescriptions=Count('prescription')
            ).order_by('-total_prescriptions', 'name')
        
        data = []

        for medicine in medicines:
            data.append({
                "medicine_id": medicine.id,
                "medicine_name": medicine.name,
                "price": medicine.price,
                "times_prescribed": medicine.total_prescriptions,
            })
        
        return Response({
            "report_name": "Medicine Usage Report",
            "total_medicines": medicines.count(),
            "medicine_report": data
        })

class PatientActivityReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only admin can access patient activity reports.")

        patients = User.objects.filter(is_staff=False).annotate(
            total_appointments=Count('appointment'),
            approved_appointments=Count('appointment', filter=Q(appointment__status='Approved')),
            pending_appointments=Count('appointment', filter=Q(appointment__status='Pending')),
            rejected_appointments=Count('appointment', filter=Q(appointment__status='Rejected')),
            finished_appointments=Count('appointment', filter=Q(appointment__status='Finished')),
            total_prescriptions=Count('appointment__prescription'),
            total_bills=Count('appointment__prescription__bill')
        ).order_by('-total_appointments', 'username')

        data = []

        for patient in patients:
            total_bill_amount = Bill.objects.filter(
                prescription__appointment__user=patient
            ).aggregate(total=Sum('total_price'))['total'] or 0

            data.append({
                "patient_id": patient.id,
                "username": patient.username,
                "total_appointments": patient.total_appointments,
                "approved_appointments": patient.approved_appointments,
                "pending_appointments": patient.pending_appointments,
                "rejected_appointments": patient.rejected_appointments,
                "finished_appointments": patient.finished_appointments,
                "total_prescriptions": patient.total_prescriptions,
                "total_bills": patient.total_bills,
                "total_bill_amount": total_bill_amount,
            })

        return Response({
            "report_name": "Patient Activity Report",
            "total_patients": patients.count(),
            "patient_report": data
        })

def home(request):
    return HttpResponse("Welcome to HealthcareCenter")