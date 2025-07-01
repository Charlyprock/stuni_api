from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets, generics, status, filters
from rest_framework.views import APIView

from core.views import SerializerDetailMixin

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
class ClassViewSet(SerializerDetailMixin, viewsets.ModelViewSet):
    queryset = Classe.objects.all()
    serializer_class = ClassSerializer
    serializer_detail_class = ClassDetailSerializer
    # permission_classes = [IsAdminOrReadOnly]


# # -----------------------------
# Speciality ViewSet
# # -----------------------------
class SpecialityViewSet(SerializerDetailMixin, viewsets.ModelViewSet):
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer
    serializer_detail_class = SpecialityDetailSerializer
    # permission_classes = [IsAdminOrReadOnly]

# # -----------------------------
# LevelSpeciality ViewSet
# # -----------------------------
class LevelSpecialityView(generics.CreateAPIView, generics.DestroyAPIView):
    queryset = LevelSpeciality.objects.all()
    serializer_class = LevelSpecialitySerializer
    # permission_classes = [IsAdminOrReadOnly]

    def delete(self, request, level_pk):
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

