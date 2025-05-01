from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from djoser.serializers import SetPasswordSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from .models import User
from .serializers import (
    UserCreateSerializerDjoser,
    UserSerializerDjoser,
    AvatarSetSerializer,
)


class UserViewSet(ModelViewSet):
    """Работает с моделью пользователей."""

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = LimitOffsetPagination
    http_method_names = ('get', 'post', 'put', 'delete')

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializerDjoser
        return UserSerializerDjoser

    @action(
        detail=False,
        methods=['GET'],
        url_path='me',
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
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def set_or_delete_avatar(self, request):
        """Обновление аватарки пользователя."""
        if request.method == 'PUT':
            serializer = AvatarSetSerializer(
                instance=request.user,
                data=request.data
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            user = request.user
            # if user.avatar:
            #     os.remove(user.avatar.path)
            user.avatar.delete(save=True)  # удаляем ссылку на файл в БД
            return Response(status=status.HTTP_204_NO_CONTENT)
