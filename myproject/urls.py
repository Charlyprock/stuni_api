from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include

from myproject import config

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="API Documentation",
        default_version="v1",
        description="Description de votre API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="votre_email@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [

    # documentation routes
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),


    path('admin/', admin.site.urls),
    path('api/', include('apps.urls')),
] + static(config.MEDIA_URL, document_root=config.MEDIA_ROOT)
