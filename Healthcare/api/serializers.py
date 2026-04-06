from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from .models import Appointment, Bill, Doctor, Health, Medicine, Prescription, User, Patient
from django.contrib.auth import authenticate

class Healthserializer(serializers.ModelSerializer):

    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Health
        fields = ['id', 'user', 'username', 'name', 'no', 'Email']
        read_only_fields = ['user']

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user
        email = attrs.get('Email')

        if request.method == 'POST':
            if Health.objects.filter(user=user,Email=email).exists():
                raise serializers.ValidationError(
                    {"Email": "You already have a record with this email!"}
                )
        return attrs

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True,style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True,style={'input_type': 'password'})
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        read_only_fields = ['id']

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if User.objects.filter(username = username).exists():
            raise serializers.ValidationError(
                {"Username": "This username is already taken!"}
            )
        
        if password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Password and confirm password do not match!"}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True,style ={'input_type': 'password'})

    def validate(self, attrs):
        
        username = attrs.get('username')
        password = attrs.get('password')
        
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError(
                {"detail": "Invalid username or password!"}
            )
        attrs['user'] = user
        return attrs

class CurrentUserSerializer(serializers.ModelSerializer):

    role = serializers.SerializerMethodField()
    has_health_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'is_staff']

    def get_role(self, obj):
        if obj.is_staff:
            return "Admin"
        return "Patient"
    
    def get_has_health_profile(self, obj):
        return Health.objects.filter(user=obj).exists()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        reqest = self.context.get('request')
        user = reqest.user

        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if not user.check_password(old_password):
            raise serializers.ValidationError({
                "old_password": "Incorrect old password!"
            })

        if new_password != confirm_password:
            raise serializers.ValidationError({
                "confirm_password": "New password and confirm password do not match!"
            })

        if old_password == new_password:
            raise serializers.ValidationError({
                "new_password": "New password must be different from old password!"
            })
        return attrs

class DoctorSerializer(serializers.ModelSerializer):
    can_leave = serializers.SerializerMethodField()
    doctor_status = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['id', 'name', 'specialization', 'experience', 'hospital', 'can_leave', 'doctor_status']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')   

        if request and not request.user.is_staff:
            fields.pop('can_leave', None)
            fields.pop('doctor_status', None)

        return fields

    def get_can_leave(self, obj):
        active_approved = Appointment.objects.filter(
            doctor=obj,
            status__in=['Approved', 'Pending']
        ).exists()

        finished_without_prescription = Appointment.objects.filter(
            doctor=obj,
            status='Finished',
            prescription__isnull=True
        ).exists()

        finished_with_prescription_but_no_bill = Prescription.objects.filter(
            appointment__doctor=obj,
            appointment__status='Finished',
            bill__isnull=True
        ).exists()

        return not (
            active_approved or
            finished_without_prescription or
            finished_with_prescription_but_no_bill
        )

    def get_doctor_status(self, obj):
        active_approved = Appointment.objects.filter(
            doctor=obj,
            status__in=['Approved', 'Pending']
        ).exists()

        finished_without_prescription = Appointment.objects.filter(
            doctor=obj,
            status='Finished',
            prescription__isnull=True
        ).exists()

        finished_with_prescription_but_no_bill = Prescription.objects.filter(
            appointment__doctor=obj,
            appointment__status='Finished',
            bill__isnull=True
        ).exists()

        if active_approved:
            return "Doctor still has approved appointments."

        if finished_without_prescription:
            return "Doctor has finished appointments but prescription is still pending."

        if finished_with_prescription_but_no_bill:
            return "Doctor has finished appointments and prescription is created, but bill is still pending."

        return "Doctor is free to leave."

class AppointmentSerializer(serializers.ModelSerializer):
        
    user_name = serializers.CharField(source='user.username', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    appointment_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['user']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request:
            if not request.user.is_staff:
                fields['status'].read_only = True

        return fields

    def validate(self, attrs):
        from django.utils import timezone

        request = self.context.get('request')
        doctor = attrs.get('doctor', getattr(self.instance, 'doctor', None))
        date = attrs.get('date', getattr(self.instance, 'date', None))
        new_status = attrs.get('status', getattr(self.instance, 'status', None))

        # 1. Prevent past appointment booking
        if date and date < timezone.now():
            raise serializers.ValidationError({
                "date": "Appointment date cannot be in the past!"
            })

        # 2. Prevent duplicate same-slot booking for same doctor
        if doctor and date:
            existing_appointment = Appointment.objects.filter(doctor=doctor, date=date)

            if self.instance:
                existing_appointment = existing_appointment.exclude(id=self.instance.id)

            if existing_appointment.exists():
                raise serializers.ValidationError({
                    "date": "This doctor already has an appointment at this date and time!"
                })

        # 3. Only admin can change status
        if self.instance and request and not request.user.is_staff:
            if 'status' in attrs:
                raise serializers.ValidationError({
                    "status": "Only admin can update appointment status!"
                })

        # 4. Finished allowed only if prescription and bill exist
        if self.instance and request and request.user.is_staff:
            if new_status == 'Finished':
                prescription = Prescription.objects.filter(appointment=self.instance).first()

                if not prescription:
                    raise serializers.ValidationError({
                        "status": "Cannot mark appointment as finished until prescription is created!"
                    })

                if not Bill.objects.filter(prescription=prescription).exists():
                    raise serializers.ValidationError({
                        "status": "Cannot mark appointment as finished until bill is generated!"
                    })

        return attrs

    def get_appointment_details(self, obj):
        return f"Appointment for {obj.user.username} with Dr. {obj.doctor.name} on {obj.date.strftime('%Y-%m-%d %H:%M')} - Status: {obj.status}"

class PrescriptionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='appointment.user.username', read_only=True)
    doctor_name = serializers.CharField(source='appointment.doctor.name', read_only=True)
    medicine_name = serializers.CharField(source='medication.name', read_only=True)
    medicine_price = serializers.FloatField(source='medication.price', read_only=True)
    appointment_details = serializers.CharField(source='appointment.__str__', read_only=True)

    class Meta:
        model = Prescription
        fields = '__all__'

    def validate(self, attrs):
        appointment = attrs.get('appointment', getattr(self.instance, 'appointment', None))

        if appointment and appointment.status != 'Approved':
            raise serializers.ValidationError({
                "appointment": "Cannot create prescription for unapproved appointment!"
            })

        return attrs

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request and request.user.is_staff:

            if isinstance(self.instance, Prescription):
                fields['appointment'].queryset = Appointment.objects.filter(
                    Q(prescription__isnull=True) | Q(id=self.instance.appointment.id),
                    status='Approved'
                )
            else:
                fields['appointment'].queryset = Appointment.objects.filter(
                    prescription__isnull=True,
                    status='Approved'
                )

        return fields

class MedicineSerializer(serializers.ModelSerializer):

    class Meta:
        model = Medicine
        fields = '__all__'
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Medicine price must be greater than zero!")
        return value

class BillSerializer(serializers.ModelSerializer):
    
    user_name = serializers.CharField(source='patient_name', read_only=True)
    class Meta:
        model = Bill
        fields = '__all__'
        read_only_fields = ['total_price', 'billing_date']

    def validate(self, attrs):
        prescription = attrs.get('prescription', getattr(self.instance, 'prescription', None))
        quantity = attrs.get('quantity', getattr(self.instance, 'quantity', None))

        if not prescription:
            raise serializers.ValidationError({
                "prescription": "Prescription is required to create a bill!"
            })

        # 1. Only one bill per prescription
        existing_bill = Bill.objects.filter(prescription=prescription)

        if self.instance:
            existing_bill = existing_bill.exclude(id=self.instance.id)

        if existing_bill.exists():
            raise serializers.ValidationError({
                "prescription": "Bill already exists for this prescription!"
            })

        # 2. Prescription must belong to Approved or Finished appointment
        if prescription.appointment.status not in ['Approved', 'Finished']:
            raise serializers.ValidationError({
                "prescription": "Bill can only be created for approved or finished appointments!"
            })

        # 3. Medicine price must be valid
        if prescription.medication.price <= 0:
            raise serializers.ValidationError({
                "prescription": "Medicine price must be greater than zero!"
            })

        # 4. Quantity must be valid
        if quantity is None or quantity <= 0:
            raise serializers.ValidationError({
                "quantity": "Quantity must be greater than zero!"
            })

        return attrs

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request:
            if request.user.is_staff:
                if isinstance(self.instance, Bill):
                    fields['prescription'].queryset = Prescription.objects.filter(
                        Q(bill__isnull=True) | Q(id=self.instance.prescription.id)
                    )
                else:
                    fields['prescription'].queryset = Prescription.objects.filter(
                        bill__isnull=True
                    )
            else:
                fields['prescription'].read_only = True
                fields['quantity'].read_only = True
                fields['total_price'].read_only = True
                fields['billing_date'].read_only = True

        return fields