from django.contrib import admin

from apps.courses.models import (
    Subject,
    SubjectLevelSpeciality,
    TeacherSubjectClass,
)

admin.site.register(Subject)
admin.site.register(SubjectLevelSpeciality)
admin.site.register(TeacherSubjectClass)