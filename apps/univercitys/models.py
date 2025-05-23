from django.db import models
from apps.users.models import User

# -----------------------------
# Department model
# -----------------------------
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='departments')

    def __str__(self):
        return self.name

# -----------------------------
# Level model
# -----------------------------
class Level(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

# -----------------------------
# Specialization model
# -----------------------------
class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

# -----------------------------
# LevelSpecialization model
# -----------------------------
class LevelSpecialization(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('level', 'specialization')

# -----------------------------
# Class model
# -----------------------------
class Class(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# -------------------------------------------
# StudentLevelClassSpecialization model
# -------------------------------------------

class StudentLevelClassSpecialization(models.Model):
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='enrollments')
    level = models.ForeignKey('univercitys.Level',on_delete=models.CASCADE,related_name='enrollments')
    class_obj = models.ForeignKey('univercitys.Class',on_delete=models.CASCADE,related_name='enrollments')
    specialization = models.ForeignKey('univercitys.Specialization',on_delete=models.CASCADE,related_name='enrollments')
    year = models.CharField(max_length=9) # example: 2024/2025 or 2024-2025
    is_delegate = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'level', 'class_obj', 'year')
        constraints = [
            models.UniqueConstraint(
                fields=['class_obj', 'year'],
                condition=models.Q(is_delegate=True),
                name='unique_delegate_per_class_year'
            )
        ]
        ordering = ['-year']

    def __str__(self):
        return f"{self.student.user.name} - {self.class_obj.name} ({self.year})"

    @classmethod
    def get_delegate(cls, class_id, year=None):
        """return delegate for a class and year"""
        if not year:
            year = cls.get_current_year()
        return cls.objects.filter(
            class_obj_id=class_id,
            year=year,
            is_delegate=True
        ).select_related('student__user').first()

    @classmethod
    def get_current_year(cls):
        """return current academic year"""
        from datetime import date
        today = date.today()
        if today.month >= 9:
            return f"{today.year}-{today.year + 1}"
        else:
            return f"{today.year - 1}-{today.year}"

    @classmethod
    def get_students_for_class(cls, class_id, year=None):
        """return students for a class and year(optional)"""
        queryset = cls.objects.filter(class_obj_id=class_id)
        if year:
            queryset = queryset.filter(year=year)
        return queryset.select_related('student__user')

