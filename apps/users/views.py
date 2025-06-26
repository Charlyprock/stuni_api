from django.db import transaction

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets, filters
from rest_framework.views import APIView

from apps.users.serializers import (
    StudentModelSerializer, StudentDetailModelSerializer,
    TeacherSerializer,
    LoginSerializer,
)
from apps.users.models import (
    User, Student, Teacher,
    Role, UserRole
)
from apps.users.permissions import AdminPermission
from core.views import YearFilteredQuerySetMixin, SerializerDetailMixin, CustomPagination


class StudentViewSet(SerializerDetailMixin, YearFilteredQuerySetMixin, viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentModelSerializer
    serializer_detail_class = StudentDetailModelSerializer
    pagination_class = CustomPagination
    # permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter]
    search_fields = [
        'user__code',
        'user__first_name',
        'user__last_name',
    ]

    def get_queryset(self):
        # GET /students/?year=2024/2025&level=1&speciality=1&department=1&classe=1 &search=charly

        queryset = Student.objects.filter(
            enrollments__year=self.get_year()
        )

        level_id = self.request.query_params.get("level")
        department_id = self.request.query_params.get("department")
        speciality_id = self.request.query_params.get("speciality")
        classe_id = self.request.query_params.get("classe")

        if level_id:
            queryset = queryset.filter(enrollments__level_id=level_id)

        if speciality_id:
            queryset = queryset.filter(enrollments__speciality_id=speciality_id)

        if department_id:
            queryset = queryset.filter(enrollments__speciality__department_id=department_id)

        if classe_id:
            queryset = queryset.filter(enrollments__classe_id=classe_id)

        return queryset.distinct()

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

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    # permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        instance.user.delete()
