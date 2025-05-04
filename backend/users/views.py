from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from djoser.serializers import SetPasswordSerializer
from django.conf import settings

from .models import User
from api.serializers import (
    UserCreateSerializerDjoser,
    UserSerializerDjoser,
    AvatarSetSerializer,
)


class UserViewSet(ModelViewSet):
    """Работает с моделью пользователей."""

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    http_method_names = ('get', 'post', 'put', 'delete')

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializerDjoser
        return UserSerializerDjoser

    @action(
        detail=False,
        methods=['GET'],
        url_path=settings.SELF_PROFILE_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def get_me_data(self, request):
        """Получение своей учетной записи."""
        return Response(
            UserSerializerDjoser(request.user).data, status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['POST'],
        url_path='set_password',
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        """Изменение своего пароля."""
        serializer = SetPasswordSerializer(
            data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['PUT', 'DELETE'],
        url_path=f'{settings.SELF_PROFILE_POINT}/{settings.AVATAR_POINT}',
        permission_classes=(IsAuthenticated,)
    )
    def set_or_delete_avatar(self, request):
        """Установка или удаление аватарки пользователя."""
        if request.method == 'PUT':
            serializer = AvatarSetSerializer(
                instance=request.user,
                data=request.data
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            request.user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
