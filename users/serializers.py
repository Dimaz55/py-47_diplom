from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    role_value = serializers.CharField(
        source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'last_name', 'first_name', 'patronymic', 'company',
            'role', 'role_value', 'email', 'password',
        ]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    token = serializers.CharField(read_only=True)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ErrorDetailSerializer(serializers.Serializer):
    error = serializers.CharField()
