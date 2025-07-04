from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.views import APIView

from core.views import SerializerDetailMixin, YearFilteredQuerySetMixin

from apps.users.models import User, Student
from apps.users.permissions import IsAdminOrReadOnly

from apps.univercitys.models import (
    Department,
    Level,
    Classe,
    Speciality,
    LevelSpeciality,
    StudentLevelSpecialityClass as Enrollment,
)

from apps.univercitys.serializers import (
    TestSerializer,
    DepartmentSerializer, DepartmentDetailSerializer,
    LevelSerializer, LevelDetailSerializer,
    ClassSerializer, ClassDetailSerializer,
    SpecialitySerializer, SpecialityDetailSerializer,
    LevelSpecialitySerializer,
    EnrollmentSerializer,
)

from apps.users.serializers import StudentModelSerializer


class TestViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = TestSerializer
    # permission_classes = [IsAdminOrReadOnly]

    # def list(self, request, *args, **kwargs):
    #     id = 11
    #     user = User.objects.get(pk=id) 
    #     print(self.request.user.is_authenticated)
    #     return Response({"data": "user"})

    def list(self, request, *args, **kwargs):
        sp = Speciality.objects.get(id=1)
        return Response({"data": f"create {Student.create_matricule(sp)}"})
        return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        super().create(self, *args, **kwargs)
        print(Student.create_matricule())
        return Response({"data": f"create {Student.create_matricule()}"}, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        return Response({"data": "retrieve"}, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        return Response({"data": "update"}, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        return Response({"data": "destroy"}, status=status.HTTP_204_NO_CONTENT)
    
    def partial_update(self, request, *args, **kwargs):
        return Response({"data": "partial_update"}, status=status.HTTP_200_OK)
    
class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.GET

        if params.get('student_id', None):
            queryset = queryset.filter(student=params.get('student_id'))
        return queryset
        

# # -----------------------------
# Department ViewSet
# # -----------------------------
class DepartmentViewSet(SerializerDetailMixin, viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    serializer_detail_class = DepartmentDetailSerializer
    # permission_classes = [IsAdminOrReadOnly]

    filter_backends = [filters.SearchFilter]
    search_fields = [
        'name',
        'abbreviation'
    ]


# # -----------------------------
# Level ViewSet
# # -----------------------------
class LevelViewSet(SerializerDetailMixin, viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    serializer_detail_class = LevelDetailSerializer
    # permission_classes = [IsAdminOrReadOnly]

    filter_backends = [filters.SearchFilter]
    search_fields = [
        'name',
        'abbreviation'
    ]


# # -----------------------------
# Class ViewSet
# # -----------------------------
class ClasseViewSet(viewsets.ModelViewSet):
    queryset = Classe.objects.all()
    serializer_class = ClassSerializer
    # serializer_detail_class = ClassDetailSerializer
    # permission_classes = [IsAdminOrReadOnly]

    filter_backends = [filters.SearchFilter]
    search_fields = [
        'name',
        'abbreviation'
    ]

    def get_queryset(self):
        department_id = self.request.query_params.get("department")
        queryset = Classe.objects.all()

        if department_id:
            queryset = queryset.filter(speciality__department_id=department_id)

        return queryset

    @action(detail=True, methods=["post"], url_path="delegate")
    def set_delegate(self, request, pk=None):
        classe = self.get_object()
        student_id = request.data.get("student")

        if not student_id:
            return Response({"student": "student is required."}, status=400)

        year = Enrollment.get_current_year()

        # Supprime le délégué actuel
        Enrollment.objects.filter(classe=classe, year=year, is_delegate=True).update(is_delegate=False)

        # Active le nouveau délégué
        enrollment = generics.get_object_or_404(Enrollment, student_id=student_id, classe=classe, year=year)
        enrollment.is_delegate = True
        enrollment.save()

        return Response({
            "id": enrollment.student.id,
            "first_name": enrollment.student.user.first_name,
            "last_name": enrollment.student.user.last_name,
            "username": enrollment.student.user.username,
            "code": enrollment.student.user.code,
        })

    
    @action(detail=True, methods=["get"], url_path="students")
    def get_students(self, request, pk=None):
        classe = self.get_object()
        year = request.query_params.get("year") or Enrollment.get_current_year()

        # Filtrer les inscriptions dans la classe et pour l'année
        enrollments = classe.enrollments.filter(year=year).select_related("student__user")

        data = [
            {
                "id": enrollment.student.id,
                "first_name": enrollment.student.user.first_name,
                "last_name": enrollment.student.user.last_name,
                "username": enrollment.student.user.username,
                "code": enrollment.student.user.code,
            }
            for enrollment in enrollments
        ]

        return Response(data, status=status.HTTP_200_OK)


# # -----------------------------
# Speciality ViewSet
# # -----------------------------
class SpecialityViewSet(SerializerDetailMixin, viewsets.ModelViewSet):
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer
    serializer_detail_class = SpecialityDetailSerializer
    # permission_classes = [IsAdminOrReadOnly]

    filter_backends = [filters.SearchFilter]
    search_fields = [
        'name',
        'abbreviation'
    ]

    
    def get_queryset(self):
        queryset = Speciality.objects.all()

        department_id = self.request.query_params.get("department")
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        return queryset


# # -----------------------------
# LevelSpeciality ViewSet
# # -----------------------------
class LevelSpecialityView(generics.CreateAPIView, generics.DestroyAPIView):
    queryset = LevelSpeciality.objects.all()
    serializer_class = LevelSpecialitySerializer
    # permission_classes = [IsAdminOrReadOnly]

    def delete(self, request, level_pk):
        """
            la suppretion remove des spécialité dans un level
        """
        ids = request.data.get("ids", [])

        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            return Response({"error": "Liste d'IDs invalide."}, status=400)

        level = generics.get_object_or_404(Level, pk=level_pk)

        deleted = []
        not_found = []

        for sid in ids:
            try:
                link = LevelSpeciality.objects.get(level=level, speciality_id=sid)
                link.delete()
                deleted.append(sid)
            except LevelSpeciality.DoesNotExist:
                not_found.append(sid)

        return Response({
            "deleted": deleted,
            "not_found": not_found
        }, status=200 if deleted else 404)


class UnivercityYearsListView(APIView):
    """
        pour recupérer la liste de année acardemic ou il ya eu des inscriptions.
    """
    def get(self, request):
        years = Enrollment.objects.values_list('year', flat=True).distinct().order_by('-year')
        return Response(years, status=status.HTTP_200_OK)

