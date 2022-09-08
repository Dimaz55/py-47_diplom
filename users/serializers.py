from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role_value = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'last_name', 'first_name', 'patronymic', 'company',
            'role', 'role_value',
            'email', 'password',
        ]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
