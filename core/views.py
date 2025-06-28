import math
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from apps.univercitys.models import StudentLevelSpecialityClass as Enrollment

class SerializerDetailMixin:

    serializer_detail_class = None

    def get_serializer_class(self):
        if self.action == 'retrieve' and self.serializer_detail_class is not None:
            return self.serializer_detail_class
        return super().get_serializer_class()


class YearFilteredQuerySetMixin:
    year_param_name = 'year'

    def get_current_year(self):
        return Enrollment.get_current_year()

    def get_year(self):
        return self.request.query_params.get(self.year_param_name, self.get_current_year())


class CustomPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        total_pages = math.ceil(self.page.paginator.count / self.page_size)
        return Response({
            'count': self.page.paginator.count,
            'total_pages': total_pages,
            'current_page': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })