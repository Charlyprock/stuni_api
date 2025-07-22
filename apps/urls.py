from django.urls import path, include

from apps.users.urls import urlpatterns as user_urls
from apps.univercitys.urls import urlpatterns as univercity_urls
from apps.courses.urls import urlpatterns as course_urls


urlpatterns = [
    path('', include(user_urls)),
    path('', include(univercity_urls)),
    path('', include(course_urls)),
]