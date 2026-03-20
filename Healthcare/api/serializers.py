from rest_framework import serializers
from .models import Appointment, Doctor, Health, User, Patient

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

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user
    
    def validate(self, attrs):
        if User.objects.filter(username = attrs['username']).exists():
            raise serializers.ValidationError(
                {"Username": "This username is already taken!"}
            )
        return attrs


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['user', 'status']

        