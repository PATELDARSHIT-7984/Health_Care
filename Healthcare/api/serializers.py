from rest_framework import serializers
from .models import Appointment, Doctor, Health, Medicine, Prescription, User, Patient

class Healthserializer(serializers.ModelSerializer):

    class Meta:
        model = Health
        fields = '__all__'
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
    password = serializers.CharField(write_only=True)
    class Meta:
        model = Patient
        fields = ['username', 'password']

    def validate(self, attrs):
        if User.objects.filter(username = attrs['username']).exists():
            raise serializers.ValidationError(
                {"Username": "This username is already taken!"}
            )
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
        
    user_name = serializers.CharField(source='user.username', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)


    appointment_details = serializers.CharField(
        source='appointment.__str__',
        read_only=True
    )

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['user']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        def validate_date(self, attrs):
            from django.utils import timezone

            if attrs < timezone.now():
                raise serializers.ValidationError("Appointment date cannot be in the past!")
            return attrs

        if request:
            if request.user.is_staff:
                fields['doctor'].read_only = True
                fields['date'].read_only = True
            else:
                fields['status'].read_only = True

        return fields
            
class PrescriptionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Prescription
        fields = '__all__'
    
    user_name = serializers.CharField(source='appointment.user.username', read_only=True)
    doctor_name = serializers.CharField(source='appointment.doctor.name', read_only=True)

    def validate(self, attrs):
        appointment = attrs.get('appointment')
        if appointment and appointment.status != 'Approved':
            raise serializers.ValidationError("Cannot create prescription for unapproved appointment!")
        
        return attrs

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request and request.user.is_staff:
            fields['appointment'].queryset = Appointment.objects.filter(status='Approved')

        return fields

class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = '__all__'