from django.contrib.auth import authenticate
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.utils.timezone import now
import os

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.models import (
    User, Student, Teacher,
    Role, UserRole,
)
from apps.univercitys.models import (
    Level, Speciality, Classe,
    StudentLevelSpecialityClass as Enrollment, LevelSpeciality
)
from apps.univercitys.serializers import EnrollmentSerializer

class UserSerializerMixin:
    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'first_name', 'last_name', 'code', 
            'phone', 'address', 'genre', 'nationnality', 'image',
        ]
    
    def validate_genre(self, genre):
        if not User.validate_genre(genre):
            raise serializers.ValidationError({"genre": "the genre field must contain M or F."})
        return genre

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request:
            if request.method in ['PATCH', 'PUT']:
                fields['password'].required = False
                fields['code'].required = False
            elif request.method == 'GET':
                fields['password'].required = True  
                fields['password'].required = fields['password'].required
        return fields


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'username', 'first_name', 'last_name', 'code', 
            'phone', 'address', 'genre', 'nationnality', 'image',
        ]

        read_only_fields = ['id', 'username']

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

class StudentModelSerializer(UserSerializerMixin, serializers.ModelSerializer):
    
    email = serializers.EmailField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    code = serializers.CharField(write_only=True, required=False, min_length=10, max_length=25)  # si l'api doit générer le code
    first_name = serializers.CharField(write_only=True, min_length=10)
    last_name = serializers.CharField(write_only=True, min_length=10)
    phone = serializers.CharField(write_only=True, required=False, min_length=9)
    address = serializers.CharField(write_only=True, required=False)
    genre = serializers.CharField(write_only=True, required=False)
    nationnality = serializers.CharField(write_only=True, required=False)
    image = serializers.ImageField(write_only=True, required=False)

    level = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Level.objects.all())
    speciality = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Speciality.objects.all())
    classe = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Classe.objects.all())
    year = serializers.CharField(write_only=True, required=False)
    is_delegate = serializers.BooleanField(write_only=True, default=False)

    enrollments = serializers.SerializerMethodField(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = [
            'email', 'password', 'first_name', 'last_name', 'code', 'phone', 'address',
            'genre', 'nationnality', 'image',
            'id', 'birth_date', 'birth_place', 'is_work',
            'level', 'speciality', 'classe', 'year', 'is_delegate',
            'user', 'enrollments'
        ]
        read_only_fields = ['id']

    def get_enrollments(self, student):
        request = self.context.get('request')
        year = request.query_params.get('year') or Enrollment.get_current_year()

        try:
            enrollment = student.enrollments.get(year=year)
        except Enrollment.DoesNotExist:
            return None

        return EnrollmentSerializer(enrollment).data

    
    def validate(self, data):
        is_partial_update = self.context.get('view').action == 'partial_update'

        if data.get('level') and data.get("speciality") and not is_partial_update:
            if not LevelSpeciality.validate_level_speciality(data['level'].id, data['speciality'].id):
                raise serializers.ValidationError(
                    {"level": "this speciality is not disponible for the level."}
                )
        
        if data.get('year') and not Enrollment.validate_year_format(data['year']):
            raise serializers.ValidationError({"year": "Format of field year is invalid."})
        elif not data.get('year') and not is_partial_update:
            data['year'] = Enrollment.get_current_year()
        
        if not data.get("code") and not is_partial_update:
            data["code"] = Student.generate_matricule(data.get('speciality'))
        else:
            if User.objects.filter(code=data.get('code')).exists():
                raise serializers.ValidationError({"code": "This code already exists."})

        if data.get("email") and data.get("email") != '' and data.get("email") != None:
            if User.objects.filter(email=data.get('email')).exists():
                raise serializers.ValidationError({"email": "This email already exists."})

        if data.get("genre") and not User.validate_genre(data["genre"]):
            raise serializers.ValidationError({"genre": "the genre field must contain M or F."})
        
        if data.get("birth_date") and data["birth_date"] >= now().date():
            raise serializers.ValidationError({"birth_date": "this date is invalide."})

        if data.get("is_delegate"):
            if Enrollment.get_delegate(data['classe'], data.get('year')):
                raise serializers.ValidationError({"is_delegate": "A delegate already exists for this class."})

        return data
    
    @transaction.atomic
    def create(self, validated_data):
       
        user = User.objects.create_user(
            email=validated_data.get('email'),
            password=validated_data['password'],
            username=f"{validated_data['first_name'].split(' ')[0]} {validated_data['last_name'].split(' ')[0]}",
            code=validated_data['code'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data.get('phone'),
            address=validated_data.get('address'),
            genre=validated_data.get('genre'),
            nationnality=validated_data.get('nationnality'),
            image=validated_data.get('image')
        )

        student = Student.objects.create(
            user=user,
            birth_date=validated_data.get('birth_date'),
            birth_place=validated_data.get('birth_place'),
            is_work = validated_data.get('is_work', False)
        )

        Enrollment.objects.create(
            student=student,
            level=validated_data['level'],
            speciality=validated_data['speciality'],
            classe=validated_data['classe'],
            year=validated_data['year'],
            is_delegate=validated_data.get('is_delegate', False)
        )

        role, _ = Role.create_student_role()
        UserRole.objects.get_or_create(user=user, role=role)

        return student

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = {
            "first_name": validated_data.get("first_name", instance.user.first_name),
            "last_name": validated_data.get("last_name", instance.user.last_name),
            "username": f"{validated_data['first_name'].split(' ')[0]} {validated_data['last_name'].split(' ')[0]}",
            "code": validated_data.get("code", instance.user.code),
            "email": validated_data.get("email", instance.user.email),
            "phone": validated_data.get("phone", instance.user.phone),
            "address": validated_data.get("address", instance.user.address),
            "genre": validated_data.get("genre", instance.user.genre),
            "nationnality": validated_data.get("nationnality", instance.user.nationnality),
        }

        if 'password' in validated_data:
            raise serializers.ValidationError(
                {"password": "The password is not update via this route."}
            )

        latest_enrollment = instance.enrollments.order_by('-year').first()

        level = validated_data.get('level', latest_enrollment.level)
        speciality = validated_data.get('speciality', latest_enrollment.speciality)

        if level and speciality:
            if not LevelSpeciality.validate_level_speciality(level.id, speciality.id):
                raise serializers.ValidationError(
                    {"level": "this speciality is not disponible for the level."}
                )

        for attr, value in user_data.items():
            setattr(instance.user, attr, value)

        if 'image' in validated_data:
            image_path = instance.user.image.path
            
            if os.path.isfile(image_path):
                os.remove(image_path)

            instance.user.image = validated_data['image']

        instance.user.save()

        instance.birth_date = validated_data.get('birth_date', instance.birth_date)
        instance.birth_place = validated_data.get('birth_place', instance.birth_place)
        instance.is_work = validated_data.get('is_work', instance.is_work)
        instance.save()

        if latest_enrollment:
            latest_enrollment.level = validated_data.get('level', latest_enrollment.level)
            latest_enrollment.speciality = validated_data.get('speciality', latest_enrollment.speciality)
            latest_enrollment.classe = validated_data.get('classe', latest_enrollment.classe)
            latest_enrollment.year = validated_data.get('year', latest_enrollment.year)
            latest_enrollment.is_delegate = validated_data.get('is_delegate', latest_enrollment.is_delegate)
            latest_enrollment.save()
        else:
            Enrollment.objects.create(
                student=instance,
                level=validated_data['level'],
                speciality=validated_data['speciality'],
                classe=validated_data['classe'],
                year=validated_data['year'],
                is_delegate=validated_data.get('is_delegate', False)
            )

        return instance

class StudentDetailModelSerializer(serializers.ModelSerializer):
    enrollments = serializers.SerializerMethodField(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'birth_date', 'birth_place', 'is_work',
            'user', 'enrollments'
        ]

    def get_enrollments(self, student):
        return EnrollmentSerializer(student.enrollments.all(), many=True).data

class TeacherSerializer(UserSerializerMixin, serializers.ModelSerializer):

    email = serializers.EmailField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    code = serializers.CharField(write_only=True, required=True, min_length=10, max_length=25)  # si l'api doit générer le code
    first_name = serializers.CharField(write_only=True, min_length=10)
    last_name = serializers.CharField(write_only=True, min_length=10)
    phone = serializers.CharField(write_only=True, required=False, min_length=9)
    address = serializers.CharField(write_only=True, required=False)
    genre = serializers.CharField(write_only=True, required=False)
    nationnality = serializers.CharField(write_only=True, required=False)
    image = serializers.ImageField(write_only=True, required=False)

    user = UserSerializer(read_only=True)
    teacher_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = Teacher
        fields = UserSerializerMixin.Meta.fields + ['grade', 'teacher_id', 'user']
        read_only_fields = ['teacher_id', 'user']

    def validate_code(self, code):
        if User.objects.filter(code=code).exists():
            raise serializers.ValidationError("This code already exists.")
        return code

    @transaction.atomic
    def create(self, validated_data):
        grade = validated_data.pop('grade', None)

        user = User.objects.create_user(
            username=f"{validated_data['first_name'].split(' ')[0]} {validated_data['last_name'].split(' ')[0]}",
            **validated_data
        )
        teacher = Teacher.objects.create(
            user=user,
            grade=grade
        )
        user.save()

        role, _ = Role.create_teacher_role()
        UserRole.objects.create(user=user, role=role)

        return teacher
    
    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = {
            "first_name": validated_data.get("first_name", instance.user.first_name),
            "last_name": validated_data.get("last_name", instance.user.last_name),
            "username": f"{validated_data['first_name'].split(' ')[0]} {validated_data['last_name'].split(' ')[0]}",
            "code": validated_data.get("code", instance.user.code),
            "email": validated_data.get("email", instance.user.email),
            "phone": validated_data.get("phone", instance.user.phone),
            "address": validated_data.get("address", instance.user.address),
            "genre": validated_data.get("genre", instance.user.genre),
            "nationnality": validated_data.get("nationnality", instance.user.nationnality),
        }

        if 'password' in validated_data:
            raise serializers.ValidationError(
                {"password": ["The password is not update via this route."]}
            )

        for attr, value in user_data.items():
            setattr(instance.user, attr, value)

        if 'image' in validated_data:
            image_path = instance.user.image.path
            
            if os.path.isfile(image_path):
                os.remove(image_path)

            instance.user.image = validated_data['image']

        instance.user.save()

        instance.grade = validated_data.get('grade', instance.grade)
        instance.save()

        return instance
