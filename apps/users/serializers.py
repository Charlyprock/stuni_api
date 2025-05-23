from django.contrib.auth import authenticate
from django.db import transaction
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.models import User, Student, Role, UserRole

class StudentSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    class Meta:
        model = User
        fields = ['username', 'code', 'password']

    @transaction.atomic
    def create(self, validated_data):

        user = User.objects.create_user(**validated_data)
        Student.objects.create(user=user)
        user.save()

        role, _ = Role.objects.get_or_create(name="student")
        UserRole.objects.create(user=user, role=role)

        return user
    
class LoginSerializer(TokenObtainPairSerializer):
    username_field = 'code'

    def validate(self, attrs):
        code = attrs.get('code')
        password = attrs.get('password')

        if code and password:
            user = authenticate(request=self.context.get('request'), code=code, password=password)

            if not user:
                raise serializers.ValidationError({"login_error": "Code or password incorrect."})

        else:
            raise serializers.ValidationError({"login_error": 'Code and passwors is required.'})

        data = super().validate(attrs)

        data['user'] = {
            'id': user.pk,
            'username': user.username,
            'code': user.code,
        }
        return data
