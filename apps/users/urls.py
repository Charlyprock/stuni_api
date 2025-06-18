from django.urls import path, include

from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from apps.users.views import (
    StudentViewSet, TeacherViewSet,
    LoginView, ChangePasswordView
)

route = DefaultRouter()
route.register(r"students", StudentViewSet, basename="students")
route.register(r"teachers", TeacherViewSet, basename="teachers")


urlpatterns = [
    path('', include(route.urls)),
    path('change_password/', ChangePasswordView.as_view(), name='change_password'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]