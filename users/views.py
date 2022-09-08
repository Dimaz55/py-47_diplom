from rest_framework import viewsets, generics, views
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from users.models import User
from users.serializers import UserSerializer, LoginSerializer, PasswordResetSerializer
from users.tasks import send_password_reset_email, send_registration_email


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'patch']
    serializer_class = UserSerializer

    def get_permission_classes(self):
        if self.action == 'post':
            return [AllowAny]
        return [IsAuthenticated]

    def get_object(self):
        user = User.objects.filter(pk=self.request.user.pk)
        if user:
            return user.first()
        raise ValidationError({'error': 'token not provided'})

    def create(self, request, *args, **kwargs):
        if request.data['role'] not in ['seller', 'buyer']:
            return ValidationError(
                {'role': f'correct choices: {User.ROLES}'}
            )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = User.objects.create(**serializer.validated_data)
        user.set_password(password)
        user.save()
        send_registration_email.delay(email, password)
        return Response(self.serializer_class(user).data)


class UserLoginView(generics.CreateAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = User.objects.filter(email=email)
        if not user:
            raise ValidationError({'error': 'user not found'})
        if not user or not user.first().check_password(password):
            return Response(
                {'error': 'wrong credentials'},
                status=401
            )
        token, _ = Token.objects.get_or_create(user=user.first())
        return Response({'token': token.key})


class PasswordResetViewSet(views.APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if not user:
            raise ValidationError({'error': 'email not found'})
        password = User.objects.make_random_password()
        user.set_password(password)
        user.save(update_fields=['password'])

        print(f'Новый пароль: {password}')
        send_password_reset_email.delay(email, password)

        return Response({
            'success': f'new password was sent to {email}'
        })