from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch
from django.conf import settings
from djoser.serializers import SetPasswordSerializer

from users.models import User
from api.serializers import (
    UserCreateSerializerDjoser,
    UserSerializerDjoser,
    AvatarSetSerializer,
)
from recipes.models import Recipe, Ingredient, Tag
from .filters import IngredientFilter, RecipeFilter
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipesWriteSerializer,
    RecipesReadSerializer,
    ShortLinkSerializer,
    SubscriptionSerializer,

)
from users.permissions import IsAuthorOrAdminOnly


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

    def _get_queryset_users(self, request, *args, **kwargs):
        """Формирует кверисет подписчиков с рецептами."""
        # Получаем список пользователей, на которых подписаны
        followed_users = self.request.user.followings.values_list(
            'author', flat=True)
        # Получаем limit рецептов или будем выводить все рецепты
        try:
            limit = int(request.query_params.get('recipes_limit'))
        except (ValueError, TypeError):
            limit = None
        context = {'recipes_limit': limit}
        # Формируем список рецептов
        recipe_prefetch = Prefetch(
            'recipes', queryset=Recipe.objects.order_by(
                *Recipe._meta.ordering)
        )
        # Соединяем рецепты с каждым пользователем, на которого подписаны
        queryset = User.objects.filter(
            id__in=followed_users).prefetch_related(recipe_prefetch)
        return queryset, context

    @action(
        detail=False,
        methods=['GET'],
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request, *args, **kwargs):
        queryset, context = self._get_queryset_users(request, *args, **kwargs)
        page = self.paginate_queryset(queryset)
        if page:
            return self.get_paginated_response(
                SubscriptionSerializer(page, many=True, context=context).data
            )
        # serializer = SubscriptionSerializer(queryset, many=True, context=context)
        # return Response(serializer.data)


class TagsViewSet(ModelViewSet):
    """Контроллер Тэгов, GET."""

    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer
    pagination_class = None
    http_method_names = ('get',)


class IngredientsViewSet(ModelViewSet):
    """Контроллер ингредиентов, GET."""

    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None
    http_method_names = ('get',)


class RecipesViewSet(ModelViewSet):
    """Контроллер рецептов."""

    queryset = Recipe.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        elif self.action == 'create':
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['partial_update', 'destroy']:
            self.permission_classes = [IsAuthorOrAdminOnly]
        return [permission() for permission in self.permission_classes]

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipesReadSerializer
        return RecipesWriteSerializer
