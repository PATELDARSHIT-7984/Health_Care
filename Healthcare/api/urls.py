from django.urls import path, include
from .views import (ChangePasswordView, CurrentUserView, HealthcenterView, DoctorView, LoginView, RegisterView, AppointmentView, PrescriptionView, MedicineView, BillView, AdminDashboardView, PatientDashboardView, DoctorAppoitmentReportView, MedicineUsageReportView, PatientActivityReportView)
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.routers import DefaultRouter
from .views import ForgotPasswordView, ResetPasswordView

schema_view = get_schema_view(
    openapi.Info(
        title="Healthcare API",
        default_version='v1',
        description="API documentation for Healthcare project"
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'healthcenter', HealthcenterView)
router.register(r'register', RegisterView)
router.register(r'doctor', DoctorView)
router.register(r'appointment', AppointmentView)
router.register(r'prescription', PrescriptionView)
router.register(r'medicine', MedicineView)
router.register(r'bill', BillView)

urlpatterns = [
    path('login_T/', obtain_auth_token),
    path('dashboard/admin/',AdminDashboardView.as_view(), name='admin-dashboard'),
    path('dashboard/patient/',PatientDashboardView.as_view(), name='patient-dashboard'),
    path('login/',LoginView.as_view(), name='login'),
    path('current_user/', CurrentUserView.as_view(), name='current-user'),
    path('change_password/', ChangePasswordView.as_view(), name='change-password'),
    path('doctor_appointments/', DoctorAppoitmentReportView.as_view(), name='doctor-appointments'),
    path('medicine_usage/', MedicineUsageReportView.as_view(), name='medicine-usage'),
    path('patient_activity/', PatientActivityReportView.as_view(), name='patient-activity'),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),



    # JWT (if you use later)
    # path('login/', TokenObtainPairView.as_view(), name='login'),
    # path('refresh/', TokenRefreshView.as_view(), name='refresh'),

    path('', include(router.urls)),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
]