import datetime
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import Permission

# -----------------------------
# User model
# -----------------------------
class User(AbstractUser):
    email = models.EmailField(null=True, blank=True)
    username = models.CharField(max_length=150, validators=[UnicodeUsernameValidator()],)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    genre = models.CharField(max_length=15, blank=True, null=True)
    nationnality = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to="users/", null=True, blank=True)

    USERNAME_FIELD = 'code'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['email'],
                name='email_unique',
                condition=~Q(email__isnull=True) & ~Q(email='')
            )
        ]


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
    
    @classmethod
    def validate_genre(cls, genre):
        if genre.lower() in ("m", "f"):
            return True
        return False

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
    def generate_matricule(cls, speciality):  # STU2025RT0001
        year = datetime.datetime.now().year
        student = cls.objects.filter(user__code__startswith=f"STU{year}")
        count = student.count() + 1
        return f"STU{year}{speciality.abbreviation}{str(count).zfill(4)}"
    
class StudentAttachment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attachments")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="student_attachments/")
    mime_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.file:
            self.mime_type = self.file.file.content_type
        super().save(*args, **kwargs)

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
    
    @classmethod
    def create_teacher_role(cls):
        return cls.objects.get_or_create(name="teacher")

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