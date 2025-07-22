from django.db import transaction
from collections import defaultdict

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

from apps.univercitys.models import (
    LevelSpeciality
)
from apps.courses.models import (
    SubjectLevelSpeciality,
    Subject, TeacherSubjectClass,
)

from apps.courses.serializers import (
    TeacherClassInfoSerializer
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
    queryset = Teacher.objects.select_related('user').all()
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
        """
        Si les paramètres year, level, speciality et classe sont fournis,
        renvoyer uniquement les enseignants de cette classe.
        Sinon, renvoyer tous les enseignants.
        """
        year = self.request.query_params.get("year")
        level = self.request.query_params.get("level")
        speciality = self.request.query_params.get("speciality")
        classe_id = self.request.query_params.get("classe")

        if all([year, level, speciality, classe_id]):
            try:
                level_speciality = LevelSpeciality.objects.get(level_id=level, speciality_id=speciality)
            except LevelSpeciality.DoesNotExist:
                return Teacher.objects.none()

            subject_ids = SubjectLevelSpeciality.objects.filter(
                level_speciality=level_speciality,
            ).values_list("subject_id", flat=True)

            teacher_ids = TeacherSubjectClass.objects.filter(
                year=year,
                subject_id__in=subject_ids,
                classe_id=classe_id
            ).values_list("teacher_id", flat=True).distinct()

            return Teacher.objects.filter(id__in=teacher_ids).select_related("user")

        return self.queryset

    @action(detail=False, methods=["get"], url_path="no-courses")
    def without_courses(self, request):
        """
        GET /api/teachers/without-courses/?year=2024-2025
        Renvoie les enseignants qui ne donnent aucun cours (optionnellement pour une année).
        """
        year = request.query_params.get("year")

        if year:
            teachers_with_courses = TeacherSubjectClass.objects.filter(
                year=year
            ).values_list("teacher_id", flat=True)
        else:
            teachers_with_courses = TeacherSubjectClass.objects.values_list("teacher_id", flat=True)
            
        teachers = Teacher.objects.exclude(id__in=teachers_with_courses).select_related("user")

        return Response(self.serializer_class(teachers, many=True).data)

    @action(methods=['DELETE'], detail=False, url_path='teachers-ids-delete')
    def teacher_delete_ids(self, request):
        """
        Supprime les enseignants par IDs fournis dans le corps de la requête.
        """
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

    @action(detail=True, methods=["get"], url_path="classes")
    def classes_taught(self, request, pk=None):
        """
            GET /api/teachers/{pk}/classes/?year=2024-2025&group_by=year|classe|subject 
            Récupère les classes enseignées par un enseignant, avec option de regroupement.
        """

        teacher = self.get_object()
        group_by = request.query_params.get("group_by")  # year, classe, subject
        year_filter = request.query_params.get("year")

        queryset = TeacherSubjectClass.objects.filter(teacher=teacher).select_related("classe", "subject")

        if year_filter:
            queryset = queryset.filter(year=year_filter)

        serializer = TeacherClassInfoSerializer(queryset, many=True)
        raw_data = serializer.data

        # GROUPING LOGIC
        if group_by in ['year', 'classe', 'subject']:
            grouped = defaultdict(list)

            for item in raw_data:
                if group_by == "year":
                    key = item["year"]
                    entry = {k: v for k, v in item.items() if k != "year"}
                elif group_by == "classe":
                    key = f"{item['classe']['id']}-{item['classe']['name']}"
                    entry = {k: v for k, v in item.items() if k != "classe"}
                elif group_by == "subject":
                    key = f"{item['subject']['id']}-{item['subject']['name']}"
                    entry = {k: v for k, v in item.items() if k != "subject"}
                grouped[key].append(entry)

            return Response(grouped)

        # Default flat response
        return Response(raw_data)

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