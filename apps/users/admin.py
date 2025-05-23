from django.contrib import admin

from apps.users.models import User, Student, Role, UserRole, Teacher

# class UserAdmin(admin.ModelAdmin):
#     list_display = ('pk', 'username', 'email', 'is_staff', 'is_active')

admin.site.register(User)
admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Role)
admin.site.register(UserRole)
