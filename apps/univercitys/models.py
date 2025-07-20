from datetime import date
from django.db import models
from apps.users.models import User

# -----------------------------
# Department model
# -----------------------------
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    abbreviation = models.SlugField(max_length=15, unique=True)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='departments')

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

# -----------------------------
# Level model
# -----------------------------
class Level(models.Model):
    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.SlugField(max_length=15, unique=True)
    specialitys = models.ManyToManyField('Speciality', through="LevelSpeciality", related_name='levels')

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

# -----------------------------
# Speciality model
# -----------------------------
class Speciality(models.Model):
    name = models.CharField(max_length=100, unique=True)
    abbreviation = models.SlugField(max_length=15, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='specialitys')

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

# -----------------------------
# LevelSpeciality model
# -----------------------------
class LevelSpeciality(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.level.name}-{self.speciality.name}"

    class Meta:
        unique_together = ('level', 'speciality')

    @classmethod
    def validate_level_speciality(cls, level_id, speciality_id):
        return cls.objects.filter(
                level_id=level_id,
                speciality_id=speciality_id
            ).exists()

# -----------------------------
# Classe model
# -----------------------------
class Classe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    abbreviation = models.SlugField(max_length=15, unique=True)
    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE, related_name='classes')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

# -------------------------------------------
# StudentLevelClassSpeciality model
# -------------------------------------------

class StudentLevelSpecialityClass(models.Model):
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='enrollments')
    level = models.ForeignKey('univercitys.Level',on_delete=models.CASCADE,related_name='enrollments')
    classe = models.ForeignKey('univercitys.Classe',on_delete=models.CASCADE,related_name='enrollments')
    speciality = models.ForeignKey('univercitys.Speciality',on_delete=models.CASCADE,related_name='enrollments')
    year = models.CharField(max_length=9) # example: 2024/2025
    is_delegate = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['classe', 'year'],
                condition=models.Q(is_delegate=True),
                name='unique_delegate_per_class_year'
            ),
            models.UniqueConstraint(
                fields=['student', 'year'],
                name='unique_student_per_year'
            )
        ]
        ordering = ['-year']

    def __str__(self):
        return f"{self.student.user.username}::{self.student.user.code} - {self.classe.name} ({self.year})"

    @classmethod
    def get_delegate(cls, class_id, year=None):
        """return delegate for a class and year"""
        if not year:
            year = cls.get_current_year()
        return cls.objects.filter(
            classe_id=class_id,
            year=year,
            is_delegate=True
        ).select_related('student__user').first()
    
    @classmethod
    def validate_year_format(cls, year):
        year_now = date.today().year
        years = year.split('/')
        
        if(len(years) == 2 and years[1] <= str(year_now)):
            try:
                if (int(years[0]) == int(years[1]) - 1):
                    return True
            except:
                return False
        
        return False

    @classmethod
    def get_current_year(cls):
        """return current academic year"""
        today = date.today()
        if today.month >= 9:
            return f"{today.year}/{today.year + 1}"
        else:
            return f"{today.year - 1}/{today.year}"

    @classmethod
    def get_students_for_class(cls, class_id, year=None):
        """return students for a class and year(optional)"""
        queryset = cls.objects.filter(classe_id=class_id)
        if year:
            queryset = queryset.filter(year=year)
        return queryset.select_related('student__user')

