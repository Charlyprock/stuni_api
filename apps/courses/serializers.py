from django.db import transaction
from rest_framework.generics import get_object_or_404
from rest_framework import serializers

from apps.univercitys.models import (
    Level, Speciality, LevelSpeciality,
)
from apps.courses.models import (
    Subject, TeacherSubjectClass,
    SubjectLevelSpeciality,
)
from apps.univercitys.models import (
    StudentLevelSpecialityClass as Enrollment,
)

# # -----------------------------
# Subject Serializer
# # -----------------------------
class SubjectSerializer(serializers.ModelSerializer):
    level = serializers.PrimaryKeyRelatedField(queryset=Level.objects.all(), write_only=True, required=False)
    speciality = serializers.PrimaryKeyRelatedField(queryset=Speciality.objects.all(), write_only=True, required=False)

    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'credit', 'volume_horaire', 'level', 'speciality']

    @transaction.atomic
    def create(self, validated_data):
       
        level = validated_data.pop('level', None)
        speciality = validated_data.pop('speciality', None)

        subject = super().create(validated_data)

        if level and speciality:
            # Trouver ou créer LevelSpecialization
            level_spec, _ = LevelSpeciality.objects.get_or_create(
                level=level,
                speciality=speciality
            )

            # Vérifier doublon SubjectLevelSpecialization
            exists = SubjectLevelSpeciality.objects.filter(
                subject=subject,
                level_speciality=level_spec,
            ).exists()

            if not exists:
                SubjectLevelSpeciality.objects.create(
                    subject=subject,
                    level_speciality=level_spec,
                )

        return subject


class SubjectLevelSpecialitySerializer(serializers.ModelSerializer):
    level = serializers.PrimaryKeyRelatedField(queryset=Level.objects.all(), write_only=True)
    speciality = serializers.PrimaryKeyRelatedField(queryset=Speciality.objects.all(), write_only=True)

    class Meta:
        model = SubjectLevelSpeciality
        fields = ['id', 'subject', 'level', 'speciality']

    def validate(self, data):
        level = data.get("level")
        speciality = data.get("speciality")

        try:
            lspec = LevelSpeciality.objects.get(level=level, speciality=speciality)
        except LevelSpeciality.DoesNotExist:
            raise serializers.ValidationError("La spécialité sélectionnée n'appartient pas au niveau donné.")

        subject = data.get("subject")

        # Ne pas créer de doublon (exclure instance si update)
        qs = SubjectLevelSpeciality.objects.filter(
            subject=subject,
            level_speciality=lspec,
        )
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError("Cette matière est déjà assignée à ce parcours.")

        data['level_speciality'] = lspec
        return data

    def create(self, validated_data):
        validated_data.pop('level')
        validated_data.pop('speciality')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('level', None)
        validated_data.pop('speciality', None)
        return super().update(instance, validated_data)

# # -----------------------------
# TeacherSubjectClass Serializer
# # -----------------------------
class TeacherSubjectClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherSubjectClass
        fields = ['id', 'year', 'teacher', 'subject', 'classe']

    def validate_year(self, year):
        if not Enrollment.validate_year_format(year):
            raise serializers.ValidationError("Format of field year is invalid.")
        return year

    def validate(self, data):
        if self.instance:
            # Update : exclure l'objet actuel
            exists = TeacherSubjectClass.objects.exclude(id=self.instance.id).filter(
                year=data['year'],
                teacher=data['teacher'],
                subject=data['subject'],
                classe=data['classe']
            ).exists()
        else:
            exists = TeacherSubjectClass.objects.filter(
                year=data['year'],
                teacher=data['teacher'],
                subject=data['subject'],
                classe=data['classe']
            ).exists()

        if exists:
            raise serializers.ValidationError("Ce cours est déjà assigné à cette classe, matière et année.")

        return data


class TeacherClassInfoSerializer(serializers.ModelSerializer):
    subject = serializers.SerializerMethodField()
    classe = serializers.SerializerMethodField()

    class Meta:
        model = TeacherSubjectClass
        fields = ['year', 'classe', 'subject']

    def get_subject(self, obj):
        return {
            "id": obj.subject.id,
            "code": obj.subject.code,
            "name": obj.subject.name
        }

    def get_classe(self, obj):
        return {
            "id": obj.classe.id,
            "name": obj.classe.name
        }
