from rest_framework import serializers
from .models import Health

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



        