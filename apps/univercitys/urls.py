from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from apps.univercitys.views import (
    TestViewSet,
    DepartmentViewSet,
    LevelViewSet,
    ClassViewSet,
    SpecialityViewSet,
    LevelSpecialityView,
    EnrollmentViewSet,
    UnivercityYearsListView,
)

# route.register(r"admin/wholesalers", WholesalerAdminViewset, basename="admin-wholesalers")
# wholesaler_router_admin = routers.NestedDefaultRouter(route, r'admin/wholesalers', lookup='wholesaler')
# wholesaler_router_admin.register(r'products', WholesalerProductAdminViewSert, basename='admin-wholesaler-products')

route = DefaultRouter()
route.register(r'test', TestViewSet, basename='test')
route.register(r'departments', DepartmentViewSet, basename='departments')
route.register(r'levels', LevelViewSet, basename='levels')
route.register(r'classes', ClassViewSet, basename='classes')
route.register(r'specialitys', SpecialityViewSet, basename='specialitys')
route.register(r'enrollments', EnrollmentViewSet, basename='enrollments')

# level_router = routers.NestedDefaultRouter(route, r'levels', lookup='level')
# level_router.register(r'specialitys', LevelSpecialityViewSet, basename='level-specialitys')

urlpatterns = [
    path('', include(route.urls)),
    path('levels/<int:level_pk>/specialitys/', LevelSpecialityView.as_view()),
    path("years-list/", UnivercityYearsListView.as_view(), name="years-list"),
]