import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import Permission

# -----------------------------
# User model
# -----------------------------
class User(AbstractUser):
    email = models.EmailField(null=True, blank=True)
    username = models.CharField(max_length=150, validators=[UnicodeUsernameValidator()],)
    code = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    genre = models.CharField(max_length=15, blank=True, default=True)
    nationnality = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to="users/", null=True, blank=True)

    USERNAME_FIELD = 'code'
    REQUIRED_FIELDS = ['username']


    def __str__(self):
        return f"email: {self.email}, code: {self.code}"

    @property
    def is_admin(self):
        return self.is_staff
    
    @property
    def is_student(self):
        try:
            self.student
        except:
            return False
        else:
            return True
        
    @property
    def is_teacher(self):
        try:
            self.teacher
        except:
            return False
        else:
            return True

# -----------------------------
# Student model
# -----------------------------
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student")
    birth_date = models.DateField(null=True, blank=True)
    birth_place = models.CharField(max_length=100, null=True, blank=True)
    is_work = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}-{self.user.code}"

    @classmethod
    def create_matricule(clt, speciality):
        year = datetime.datetime.now().year
        student = Student.objects.filter(user__code__startswith=f"STU{year}")
        count = student.count() + 1
        return f"STU{year}{speciality.abbreviation}{str(count).zfill(4)}"

# -----------------------------
# Teacher model
# -----------------------------
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher")
    grade = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}-{self.user.code}"

# -----------------------------
# Admin model 
# -----------------------------
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin")

    def __str__(self):
        return f"{self.user.username}-{self.user.code}"

# -----------------------------
# Role model
# -----------------------------
class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    
    @classmethod
    def create_student_role(cls):
        return cls.objects.get_or_create(name="student")

# -----------------------------
# UserRole association
# -----------------------------
class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'role')

# -----------------------------
# RolePermission association
# -----------------------------
class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')