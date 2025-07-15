from django.db import transaction
from rest_framework.generics import get_object_or_404
from rest_framework import serializers

from apps.users.models import User, Student
from apps.univercitys.models import (
    Department,
    Level,
    Classe,
    Speciality,
    LevelSpeciality,
    StudentLevelSpecialityClass as Enrollment
)

class EnrollmentSerializer(serializers.ModelSerializer):
    # speciality = serializers.CharField(source="speciality.abbreviation", read_only=True)
    # level = serializers.CharField(source="level.abbreviation", read_only=True)
    # classe = serializers.CharField(source="classe.abbreviation", read_only=True)
    # student = serializers.CharField(source="student.user.username", read_only=True)
    class Meta:
        model = Enrollment
        # fields = ["year", "is_delegate", "speciality", "level", "classe", "student"]
        fields = "__all__"

    def validate_year(self, year):
        if not Enrollment.validate_year_format(year):
            raise serializers.ValidationError("Format of field year is invalid.")
        return year
            
    def validate(self, data):
        is_partial_update = self.context.get('view').action == 'partial_update'

        if data.get('level') and data.get("speciality") and not is_partial_update:
            if not LevelSpeciality.validate_level_speciality(data.get('level').id, data['speciality'].id):
                raise serializers.ValidationError(
                    {"level": "this speciality is not disponible for the level."}
                )

        if data.get("is_delegate") and data.get('year'):
            if Enrollment.get_delegate(data.get('classe'), data.get("year")):
                raise serializers.ValidationError({"is_delegate": "A delegate already exists for this class."})
        return data

class EnrollmentDetailSerializer(serializers.ModelSerializer):
    speciality = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    classe = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        # fields = ["year", "is_delegate", "speciality", "level", "classe", "student"]
        fields = "__all__"

    def get_level(self, enrollment):
        return {
            "id": enrollment.level.id,
            "name": enrollment.level.name,
            "abbreviation": enrollment.level.abbreviation
        }
    
    def get_speciality(self, enrollment):
        return {
            "id": enrollment.speciality.id,
            "name": enrollment.speciality.name,
            "abbreviation": enrollment.speciality.abbreviation
        }
    
    def get_classe(self, enrollment):
        return {
            "id": enrollment.classe.id,
            "name": enrollment.classe.name,
            "abbreviation": enrollment.classe.abbreviation
        }


class TestSerializer(serializers.ModelSerializer):
    # enrollments = serializers.SerializerMethodField()
    enrollments = EnrollmentSerializer(many=True)
    class Meta:
        model = Student
        fields = ["is_work", "enrollments"]

    def get_enrollments(self, student):
        return [{
            "year": enrollment.year,
            "is_delegate": enrollment.is_delegate
        } for enrollment in student.enrollments.all()]

# # -----------------------------
# Department Serializer
# # -----------------------------

class DepartmentSerializerMixin:

    def get_specialitys(self, depart):
        return [
            {
                "id": speciality.id,
                "name": speciality.name,
                "abbreviation": speciality.abbreviation,
            }
            for speciality in depart.specialitys.all()
        ]
        
    def get_admin_display(self, depart):
        return {
            "id": depart.admin.id,
            "username": depart.admin.username,
            "code": depart.admin.code,
        } if depart.admin  else None

class DepartmentSerializer(DepartmentSerializerMixin, serializers.ModelSerializer):
    admin_display = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'abbreviation', 'admin', 'admin_display']
        read_only_fields = ['id']

class DepartmentDetailSerializer(DepartmentSerializerMixin, serializers.ModelSerializer):
    specialitys = serializers.SerializerMethodField()
    admin_display = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = DepartmentSerializer.Meta.fields + ["specialitys"]


# # -----------------------------
# Level Serializer
# # -----------------------------
class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['id', 'name', 'abbreviation']

class LevelDetailSerializer(serializers.ModelSerializer):
    specialitys = serializers.SerializerMethodField()
    class Meta:
        model = Level
        fields = LevelSerializer.Meta.fields + ["specialitys"]

    def get_specialitys(self, level):
        return [
            {
                "id": speciality.id,
                "name": speciality.name,
                "abbreviation": speciality.abbreviation,
            }
            for speciality in level.specialitys.all()
        ]

# # -----------------------------
# Class Serializer
# # -----------------------------
class ClassSerializer(serializers.ModelSerializer):
    speciality_display = serializers.SerializerMethodField()
    delegate = serializers.SerializerMethodField()
    class Meta:
        model = Classe
        fields = ['id', 'name', 'abbreviation', 'speciality', 'speciality_display', 'delegate']

    def get_speciality_display(self, classe):
        return {
            "id": classe.speciality.id,
            "name": classe.speciality.name,
            "abbreviation": classe.speciality.abbreviation,
        }
    
    def get_delegate(self, classe):
        request = self.context.get("request")
        year = request.query_params.get("year")
        if not year:
            return None

        enrollment = Enrollment.objects.filter(classe=classe, year=year, is_delegate=True).first()
        return {
            "id": enrollment.student.id,
            "first_name": enrollment.student.user.first_name,
            "last_name": enrollment.student.user.last_name,
            "username": enrollment.student.user.username,
            "code": enrollment.student.user.code,
        } if enrollment else None

class ClassDetailSerializer(serializers.ModelSerializer):
    speciality = serializers.PrimaryKeyRelatedField(source='speciality.id', read_only=True)
    class Meta:
        model = Classe
        fields = ClassSerializer.Meta.fields + ['speciality']


# # -----------------------------
# Speciality Serializer
# # -----------------------------
class SpecialitySerializerMixin(serializers.ModelSerializer):
    levels = LevelSerializer(many=True)
    classes = ClassSerializer(many=True)
    department_display = serializers.SerializerMethodField()

    def get_department_display(self, speciality):
        return DepartmentSerializer(speciality.department).data

class SpecialitySerializer(SpecialitySerializerMixin, serializers.ModelSerializer):
    
    class Meta:
        model = Speciality
        fields = ["id", "name", "abbreviation", "department", "department_display"]

class SpecialityDetailSerializer(SpecialitySerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = Speciality
        fields = SpecialitySerializer.Meta.fields + ["levels", 'classes']


# # -----------------------------
# LevelSpeciality Serializer
# # -----------------------------
class LevelSpecialitySerializer(serializers.ModelSerializer):
    """ pour assigner plusieur spécialité a la fois a un niveau."""
    specialitys = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Speciality.objects.all()),
    )
    class Meta:
        model = LevelSpeciality
        fields = ["id", "specialitys"]

    @transaction.atomic()
    def create(self, validated_data):  # save many speciality for level
        level = get_object_or_404(Level, pk=self.context.get("view").kwargs["level_pk"])

        for speciality in validated_data["specialitys"]:
            try:
                LevelSpeciality.objects.create(level=level, speciality=speciality)
            except:
                raise serializers.ValidationError({"specialitys": [f"This Speciality pk ({speciality.pk}-{speciality.name}) already exists for this level."]})
        return validated_data

    