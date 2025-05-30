from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.timezone import now
from apps.univercitys.models import (
    Level, Speciality, Classe, LevelSpeciality, Department,
    StudentLevelSpecialityClass as Enrollment
)
from apps.users.models import User, Role, Student
import tempfile

class StudentAPITest(APITestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Dep14", abbreviation="Dep14")
        self.level = Level.objects.create(name="BTS-14", abbreviation="BTS-14")
        self.speciality = Speciality.objects.create(name="GL14", abbreviation="GL14", department=self.department)
        self.classe = Classe.objects.create(name="GL-C14", abbreviation="GL-C14")
        LevelSpeciality.objects.create(level=self.level, speciality=self.speciality)

        self.url = reverse("students-list")
        self.password = "StrongPass123!"

    def _get_payload(self, overrides=None):
        data = {
            "email": "test@student.com",
            "password": self.password,
            "first_name": "Jean Claude",
            "last_name": "Mbappe piere",
            "phone": "699112233",
            "address": "Yaoundé",
            "genre": "M",
            "nationnality": "Camerounaise",
            "birth_date": "2000-01-01",
            "birth_place": "Douala",
            "is_work": True,
            "level": self.level.id,
            "speciality": self.speciality.id,
            "classe": self.classe.id,
            "year": "2024/2025",
            "is_delegate": False
        }
        if overrides:
            data.update(overrides)
        return data

    def test_create_student_with_image(self):
        image = SimpleUploadedFile("avatar.jpg", b"fake-image-content", content_type="image/jpeg")
        payload = self._get_payload({"image": image})
        response = self.client.post(self.url, data=payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)

    def test_get_student_list_and_detail(self):
        # Création préalable
        response = self.client.post(self.url, data=self._get_payload(), format='json')
        student_id = response.data['id']
        # GET list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        # GET detail
        detail_url = reverse("students-detail", args=[student_id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_student_with_put(self):
        response = self.client.post(self.url, data=self._get_payload(), format='json')
        student_id = response.data['id']
        detail_url = reverse("students-detail", args=[student_id])
        updated = self._get_payload({"first_name": "Pierre Marie"})
        updated.pop("password")
        response = self.client.put(detail_url, updated, format='json')
        print("::::::::::::::::::::::::::",response.data, ":::::::::::::::::::::::::::")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['first_name'], "Pierre Marie")

    def test_partial_update_student_with_patch(self):
        response = self.client.post(self.url, data=self._get_payload(), format='json')
        student_id = response.data['id']
        detail_url = reverse("students-detail", args=[student_id])
        response = self.client.patch(detail_url, {"phone": "690000000"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['phone'], "690000000")

    def test_delete_student(self):
        response = self.client.post(self.url, data=self._get_payload(), format='json')
        student_id = response.data['id']
        detail_url = reverse("students-detail", args=[student_id])
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Student.objects.filter(pk=student_id).exists())

    # --------------------
    # TESTS D’ERREUR
    # --------------------
    def test_duplicate_code_should_fail(self):
        payload = self._get_payload({"code": "STU2024GL0001"})
        self.client.post(self.url, data=payload, format='json')
        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data)

    def test_invalid_birth_date(self):
        future_date = now().date().isoformat()
        payload = self._get_payload({"birth_date": future_date})
        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("birth_date", response.data)

    def test_invalid_level_speciality_pair(self):
        wrong_speciality = Speciality.objects.create(name="COM", department=self.department)
        payload = self._get_payload({"speciality": wrong_speciality.id})
        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("level", response.data)

    def test_delegate_already_exists(self):
        # 1er étudiant délégué
        self.client.post(self.url, data=self._get_payload({"is_delegate": True}), format='json')
        # 2e étudiant délégué pour la même classe/année
        payload = self._get_payload({"email": "new@student.com", "code": "STU2024X999", "is_delegate": True})
        response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_delegate", response.data)




# class UserTest(APITestCase):

    # def setUp(self):
    #     self.url_register = reverse_lazy('students')
    #     self.url_login = reverse_lazy('login')

    #     self.user_data = {
    #         "username": "sorel",
    #         "code": "moncode8",
    #         "password": "123456789sorel"
    #     }

    # def format_datetime(self, dt):
    #     return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    # def test_register_success(self):

    #     expected_output_data = self.user_data.copy()
    #     expected_output_data.pop('password')

    #     response = self.client.post(self.url_register, self.user_data, format='json')

    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(response.json(), expected_output_data)

    #     self.assertTrue(User.objects.filter(code=self.user_data["code"]).exists())
    #     user = User.objects.get(code=self.user_data["code"])
    #     self.assertEqual(user.code, self.user_data["code"] )


    # def test_register_error(self):

    #     data = self.user_data.copy()
    #     data.pop('code')
        
    #     response = self.client.post(self.url_register, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn('code', response.json())


    # def test_register_short_password(self):
        
    #     data = self.user_data.copy()
    #     data['password'] = 'short'
        
    #     response = self.client.post(self.url_register, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn('password', response.json())

    # def test_login(self):
        
        User.objects.create_user(**self.user_data)

        user_login_data = {
            "code": self.user_data['code'],
            "password": self.user_data['password']
        }

        response = self.client.post(self.url_login, data=user_login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())
        self.assertIn('user', response.json())