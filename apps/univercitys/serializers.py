from rest_framework import serializers

from apps.users.models import User

class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"