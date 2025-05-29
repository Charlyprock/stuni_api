from django.contrib.auth import authenticate
from django.db import transaction
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.models import User, Student, Role, UserRole
from apps.univercitys.models import StudentLevelSpecialityClass
from apps.univercitys.serializers import EnrollmentSerializer


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    class Meta:
        model = User
        fields = ['username', 'code', 'password']
     

class StudentSerializer(serializers.ModelSerializer):
    enrollments = serializers.SerializerMethodField()
    user = UserSerializer()
    class Meta:
        model = Student
        fields = ['birth_date', 'birth_place', 'is_work', 'user', 'enrollments']

    def get_enrollments(self, student):
        return EnrollmentSerializer(student.enrollments.all(), many=True).data

    @transaction.atomic
    def create(self, validated_data):
        print(Student.create_matricule())

        user = User.objects.create_user(**validated_data)
        student = Student.objects.create(user=user)
        user.save()

        role, _ = Role.create_student_role()
        UserRole.objects.create(user=user, role=role)

        return user


class StudentModelSerializer(serializers.ModelSerializer):
    # champs supplémentaires (pas dans le modèle Student)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    level_id = serializers.IntegerField(write_only=True)
    specialization_id = serializers.IntegerField(write_only=True)
    class_id = serializers.IntegerField(write_only=True)
    year = serializers.CharField(write_only=True)

    class Meta:
        model = Student
        fields = [
            'email', 'password', 'birth_date', 'birth_place',
            'level_id', 'specialization_id', 'class_id', 'year'
        ]

    def validate(self, data):
        
        if not LevelSpecialization.objects.filter(
            level_id=data['level_id'],
            specialization_id=data['specialization_id']
        ).exists():
            raise serializers.ValidationError(
                "Cette spécialité n'est pas disponible pour ce niveau."
            )
        return data

    def create(self, validated_data):
        # Créer le User
        user = User.objects.create_user(
            username=f"{validated_data['email'].split('@')[0]}",
            email=validated_data['email'],
            password=validated_data['password']
        )

        # Créer l'étudiant
        student = Student.objects.create(
            user=user,
            birth_date=validated_data['birth_date'],
            birth_place=validated_data['birth_place']
        )
        
        if not validated_data['birth_place']:
            user.code = Student
        user.save()

        StudentLevelSpecialityClass.objects.create(
            student=student,
            level_id=validated_data['level_id'],
            specialization_id=validated_data['specialization_id'],
            class_obj_id=validated_data['class_id'],
            year=validated_data['year']
        )

        # Ajouter le rôle student
        role, _ = Role.create_student_role()
        UserRole.objects.get_or_create(user=user, role=role)

        return student



class LoginSerializer(TokenObtainPairSerializer):
    username_field = 'code'

    def validate(self, attrs):
        code = attrs.get('code')
        password = attrs.get('password')

        if code and password:
            user = authenticate(request=self.context.get('request'), code=code, password=password)

            if not user:
                raise serializers.ValidationError({"login_error": "Code or password incorrect."})

        else:
            raise serializers.ValidationError({"login_error": 'Code and passwors is required.'})

        data = super().validate(attrs)

        data['user'] = {
            'id': user.pk,
            'username': user.username,
            'code': user.code,
        }
        return data
