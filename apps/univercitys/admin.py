from django.contrib import admin

from apps.univercitys.models import (Department, Level, Specialization, 
                                     Class, StudentLevelClassSpecialization)

admin.site.register(Department)
admin.site.register(Level)
admin.site.register(Specialization)
admin.site.register(Class)
admin.site.register(StudentLevelClassSpecialization)