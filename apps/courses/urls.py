from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from apps.courses.views import (
    SubjectViewSet,
    TeacherSubjectClassViewSet,
    SubjectLevelSpecialityViewSet
)

route = DefaultRouter()
route.register(r'subjects', SubjectViewSet, basename='subjects')
route.register(r'teacher-courses', TeacherSubjectClassViewSet, basename='teacher-courses')
route.register(r'subject-levels', SubjectLevelSpecialityViewSet, basename='subject-levels')

urlpatterns = [
    path('', include(route.urls)),
]