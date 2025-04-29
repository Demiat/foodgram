from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate

import users.models as mod
import users.serializers as serial


class UserViewSet(ModelViewSet):
    """Регистрирует и выводит пользователей."""

    queryset = mod.User.objects.all()
    serializer_class = serial.UserSerializer
    permission_classes = (AllowAny,)
    http_method_names = ('get', 'post')


class EmailObtainAuthToken(ObtainAuthToken):
    """Переопределяет ObtainAuthToken для выдачи токена по email."""

    serializer_class = None

    def post(self, request, *args, **kwargs):
        data = request.data
        user = authenticate(
            request=request,
            username=data.get('email'),
            password=data.get('password')
        )
        if not user:
            return Response(
                {'detail': 'Неверные учетные данные'},
                status=status.HTTP_400_BAD_REQUEST
            )
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})
