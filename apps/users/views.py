from django.db import transaction

from django.http import FileResponse, Http404
from rest_framework import status, generics, viewsets, filters, permissions, parsers
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.decorators import action

from apps.users.serializers import (
    StudentModelSerializer, StudentDetailModelSerializer,
    StudentAttachmentSerializer,
    TeacherSerializer,
    LoginSerializer,
    UserSerializer,
)
from apps.users.models import (
    User, Student, StudentAttachment,
    Teacher,
    Role, UserRole
)
from apps.users.permissions import AdminPermission
from core.views import YearFilteredQuerySetMixin, SerializerDetailMixin, CustomPagination


class StudentAttachmentViewSet(viewsets.ModelViewSet):
    queryset = StudentAttachment.objects.all()
    serializer_class = StudentAttachmentSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtrer les pièces jointes selon l'étudiant si besoin.
        """
        student_id = self.request.query_params.get("student_id")
        if student_id:
            return self.queryset.filter(student_id=student_id)
        return self.queryset
    

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, student_pk=None, pk=None):
        try:
            # attachment = StudentAttachment.objects.get(pk=pk, student_id=student_pk)
            attachment = StudentAttachment.objects.get(pk=pk)
        except StudentAttachment.DoesNotExist:
            raise Http404("Pièce jointe introuvable.")

        response = FileResponse(attachment.file.open('rb'), as_attachment=True, filename=attachment.file.name)
        return response

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

        if self.action == 'retrieve':
            queryset = queryset = Student.objects.filter()
        else:
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

    @action(methods=['DELETE'], detail=False, url_path='students-ids-delete')
    def student_delete_ids(self, request):
        ids = request.data.get("ids", [])
        
        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            return Response({"error": "Une liste d'IDs valide est requise."}, status=400)

        deleted = []
        not_found = []

        for student_id in ids:
            try:
                student = Student.objects.get(id=student_id)
                student.user.delete()
                deleted.append(student_id)
            except Student.DoesNotExist:
                not_found.append(student_id)

        return Response({
            "deleted": deleted,
            "not_found": not_found
        }, status=200 if deleted else 404)

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        current = request.data.get('current_password')
        new = request.data.get('new_password')

        if not user.check_password(current):
            return Response({'detail': 'current password is incorrect'}, status=400)

        user.set_password(new)
        user.save()
        return Response({'detail': 'success'})

class TeacherViewSet(YearFilteredQuerySetMixin, viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    pagination_class = CustomPagination
    # permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter]
    search_fields = [
        'user__code',
        'user__first_name',
        'user__last_name',
    ]

    def get_queryset(self):
        # GET /teachers/?year=2024/2025&level=1&speciality=1&department=1&classe=1 &search=charly

        queryset = queryset = Teacher.objects.filter()

        if not self.action == 'retrieve':
            queryset = Teacher.objects.filter(
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

    @action(methods=['DELETE'], detail=False, url_path='teachers-ids-delete')
    def teacher_delete_ids(self, request):
        ids = request.data.get("ids", [])
        
        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            return Response({"error": "Une liste d'IDs valide est requise."}, status=400)

        deleted = []
        not_found = []

        for teacher_id in ids:
            try:
                teacher = Teacher.objects.get(id=teacher_id)
                teacher.user.delete()
                deleted.append(teacher_id)
            except Teacher.DoesNotExist:
                not_found.append(teacher_id)

        return Response({
            "deleted": deleted,
            "not_found": not_found
        }, status=200 if deleted else 404)



class NoStudentUserListView(APIView):
    """ pour la liste de tous les potentiels admin d'un departement (admin et teacher)"""
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        student_role = Role.objects.filter(name="student").first()

        if not student_role:
            return Response({"error": "Rôle 'student' introuvable."}, status=status.HTTP_400_BAD_REQUEST)

        student_user_ids = UserRole.objects.filter(role=student_role).values_list("user_id", flat=True)

        users = User.objects.exclude(id__in=student_user_ids).distinct()

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)