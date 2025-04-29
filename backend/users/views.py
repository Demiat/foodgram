from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny

import users.models as mod
import users.serializers as serial


class UserViewSet(ModelViewSet):
    """Регистрирует и выводит пользователей."""

    queryset = mod.User.objects.all()
    serializer_class = serial.UserSerializer
    permission_classes = (AllowAny,)
    http_method_names = ('get', 'post')
