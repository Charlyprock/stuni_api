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
    StudentLevelSpecialityClass,
)

class EnrollmentSerializer(serializers.ModelSerializer):
    speciality = serializers.CharField(source="speciality.abbreviation")
    level = serializers.CharField(source="level.abbreviation")
    classe = serializers.CharField(source="classe.abbreviation")
    student = serializers.CharField(source="student.user.username")
    class Meta:
        model = StudentLevelSpecialityClass
        # fields = ["year", "is_delegate", "speciality", "level", "classe", "student"]
        fields = "__all__"

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

class DepartmentSerializer(serializers.ModelSerializer):
    admin_display = serializers.CharField(source='admin.username', read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'abbreviation', 'admin', 'admin_display']
        read_only_fields = ['id']
    

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
    class Meta:
        model = Classe
        fields = ['id', 'name', 'abbreviation']


# # -----------------------------
# Speciality Serializer
# # -----------------------------
class SpecialitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Speciality
        fields = ["id", "name", "abbreviation", "department"]

class SpecialityDetailSerializer(serializers.ModelSerializer):
    levels = LevelSerializer(many=True)
    class Meta:
        model = Speciality
        fields = SpecialitySerializer.Meta.fields + ["levels"]


# # -----------------------------
# LevelSpeciality Serializer
# # -----------------------------
class LevelSpecialitySerializer(serializers.ModelSerializer):
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
                raise serializers.ValidationError({"speciality": f"This Speciality pk ({speciality.pk}) already exists for this level."})
        return validated_data