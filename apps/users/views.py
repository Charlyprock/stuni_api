from django.db import transaction

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets
from rest_framework.views import APIView

from apps.users.serializers import (
    StudentSerializer, StudentModelSerializer,
    LoginSerializer,
)
from apps.users.models import User, Student, Role, UserRole

from apps.users.permissions import AdminPermission


class StudentView(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentModelSerializer
    # permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        instance.user.delete()
    

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current = request.data.get('current_password')
        new = request.data.get('new_password')

        if not user.check_password(current):
            return Response({'detail': 'current password is incorrect'}, status=400)

        user.set_password(new)
        user.save()
        return Response({'detail': 'success'})


