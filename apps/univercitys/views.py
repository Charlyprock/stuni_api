from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets

from apps.users.models import User
from apps.users.permissions import IsAdminOrReadOnly
from apps.univercitys.serializers import TestSerializer


class TestViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = TestSerializer
    permission_classes = [IsAdminOrReadOnly]

    def list(self, request, *args, **kwargs):
        id = 11
        user = User.objects.get(pk=id) 
        print(self.request.user.is_authenticated)
        return Response({"data": "user"})
    
    def create(self, request, *args, **kwargs):
        return Response({"data": "create"}, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        return Response({"data": "retrieve"}, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        return Response({"data": "update"}, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        return Response({"data": "destroy"}, status=status.HTTP_204_NO_CONTENT)
    
    def partial_update(self, request, *args, **kwargs):
        return Response({"data": "partial_update"}, status=status.HTTP_200_OK)