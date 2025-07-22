from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets, generics, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView

from core.views import SerializerDetailMixin, YearFilteredQuerySetMixin

from apps.users.models import User, Student

from apps.courses.models import (
    Subject, TeacherSubjectClass,
    SubjectLevelSpeciality,
)

from apps.courses.serializers import (
    SubjectSerializer, TeacherSubjectClassSerializer,
    SubjectLevelSpecialitySerializer
)

# # -----------------------------
# Subject ViewSet
# # -----------------------------
class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    # permission_classes = [permissions.IsAuthenticated]

# # -----------------------------
# SubjectLevelSpecializaty ViewSet
# # -----------------------------
class SubjectLevelSpecialityViewSet(viewsets.ModelViewSet):
    queryset = SubjectLevelSpeciality.objects.all()
    serializer_class = SubjectLevelSpecialitySerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        subject_id = self.request.query_params.get("subject")
        lspec_id = self.reques
        
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if lspec_id:
            qs = qs.filter(level_speciality_id=lspec_id)
        return qs


# # # -----------------------------
# TeacherSubjectClass ViewSet
# # # -----------------------------
class TeacherSubjectClassViewSet(YearFilteredQuerySetMixin, viewsets.ModelViewSet):
    queryset = TeacherSubjectClass.objects.all()
    serializer_class = TeacherSubjectClassSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        year = self.get_year()
        teacher = self.request.query_params.get("teacher")
        qs = self.queryset
        if year:
            qs = qs.filter(year=year)
        if teacher:
            qs = qs.filter(teacher_id=teacher)
        return qs
