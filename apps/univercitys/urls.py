from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from apps.univercitys.views import TestViewSet

route = DefaultRouter()
route.register(r'test', TestViewSet, basename='test')


urlpatterns = [
    path('', include(route.urls)),
]