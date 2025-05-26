from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse_lazy

from apps.users.models import User


class UserTest(APITestCase):

    def setUp(self):
        self.url_register = reverse_lazy('students')
        self.url_login = reverse_lazy('login')

        self.user_data = {
            "username": "sorel",
            "code": "moncode8",
            "password": "123456789sorel"
        }

    def format_datetime(self, dt):
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    def test_register_success(self):

        expected_output_data = self.user_data.copy()
        expected_output_data.pop('password')

        response = self.client.post(self.url_register, self.user_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), expected_output_data)

        self.assertTrue(User.objects.filter(code=self.user_data["code"]).exists())
        user = User.objects.get(code=self.user_data["code"])
        self.assertEqual(user.code, self.user_data["code"] )


    def test_register_error(self):

        data = self.user_data.copy()
        data.pop('code')
        
        response = self.client.post(self.url_register, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.json())


    def test_register_short_password(self):
        
        data = self.user_data.copy()
        data['password'] = 'short'
        
        response = self.client.post(self.url_register, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.json())

    def test_login(self):
        
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