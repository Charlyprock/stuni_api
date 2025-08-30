from django.db import models
from apps.users.models import User


# -------------------------------------------
# Subject model
# -------------------------------------------
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    credit = models.PositiveIntegerField()
    volume_horaire = models.CharField(max_length=50, blank=True, null=True)
    level_specializations = models.ManyToManyField(
        'univercitys.LevelSpeciality',
        through="SubjectLevelSpeciality",
        related_name="subjects"
    )

    def __str__(self):
        return f"{self.code} - {self.name}"
    
# -------------------------------------------
# SubjectLevelSpeciality model
# -------------------------------------------
class SubjectLevelSpeciality(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    level_speciality = models.ForeignKey('univercitys.LevelSpeciality', on_delete=models.CASCADE)

    class Meta:
        unique_together = ("subject", "level_speciality")

    def __str__(self):
        return f"{self.subject}-{self.level_speciality}"

    
# -------------------------------------------
# TeacherSubjectClass model
# -------------------------------------------
class TeacherSubjectClass(models.Model):
    year = models.CharField(max_length=9)

    teacher = models.ForeignKey(
        "users.Teacher", on_delete=models.CASCADE, related_name="teacher_assignments"
    )
    subject = models.ForeignKey(
        "courses.Subject", on_delete=models.CASCADE, related_name="teacher_assignments"
    )
    classe = models.ForeignKey(
        "univercitys.Classe", on_delete=models.CASCADE, related_name="teacher_assignments"
    )
    level = models.ForeignKey(
        "univercitys.Level", on_delete=models.CASCADE, related_name="teacher_subjects"
    )
    speciality = models.ForeignKey(
        "univercitys.Speciality", on_delete=models.CASCADE, related_name="teacher_subjects"
    )

    class Meta:
        unique_together = ['year', 'teacher', 'subject', 'classe']


    def __str__(self):
        return f"{self.year} - {self.teacher} - {self.subject}-{self.level}-{self.speciality} ({self.classe})"
