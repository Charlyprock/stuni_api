from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets, generics

from core.views import MultipleViewMixin

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
    DepartmentSerializer,
    LevelSerializer, LevelDetailSerializer,
    ClassSerializer,
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
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    # permission_classes = [IsAdminOrReadOnly]


# # -----------------------------
# Level ViewSet
# # -----------------------------
class LevelViewSet(MultipleViewMixin, viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    serializer_detail_class = LevelDetailSerializer
    # permission_classes = [IsAdminOrReadOnly]


# # -----------------------------
# Class ViewSet
# # -----------------------------
class ClassViewSet(viewsets.ModelViewSet):
    queryset = Classe.objects.all()
    serializer_class = ClassSerializer
    # permission_classes = [IsAdminOrReadOnly]


# # -----------------------------
# Speciality ViewSet
# # -----------------------------
class SpecialityViewSet(MultipleViewMixin, viewsets.ModelViewSet):
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer
    serializer_detail_class = SpecialityDetailSerializer
    # permission_classes = [IsAdminOrReadOnly]

# # -----------------------------
# LevelSpeciality ViewSet
# # -----------------------------
class LevelSpecialityView(generics.CreateAPIView):
    queryset = LevelSpeciality.objects.all()
    serializer_class = LevelSpecialitySerializer
    # permission_classes = [IsAdminOrReadOnly]
