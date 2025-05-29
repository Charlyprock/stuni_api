from django.contrib import admin

from apps.univercitys.models import (
    Department, Level, Speciality, 
    Classe, StudentLevelSpecialityClass,
    LevelSpeciality,
)

admin.site.register(Department)
admin.site.register(Level)
admin.site.register(Speciality)
admin.site.register(Classe)
admin.site.register(StudentLevelSpecialityClass)
admin.site.register(LevelSpeciality)