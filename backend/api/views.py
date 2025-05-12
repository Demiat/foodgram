import csv

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch, Sum
from django.conf import settings
from djoser.serializers import SetPasswordSerializer
from django.http import HttpResponse

from users.models import User, Follow
from recipes.models import (
    Recipe, Ingredient, Tag, Favorite, ShoppingCart, RecipeIngredient
)
from .filters import IngredientFilter, RecipeFilter
from .serializers import (
    UserCreateSerializerDjoser,
    UserSerializerDjoser,
    AvatarSetSerializer,
    IngredientSerializer,
    TagSerializer,
    RecipesWriteSerializer,
    RecipesReadSerializer,
    ShortLinkSerializer,
    SubscriptionSerializer,
    LimitedRecipesReadSerializer,

)
from users.permissions import IsAuthorOrAdminOnly
from .constants import (
    FOLLOWING_ERROR,
    SELF_FOLLOWING,
    IS_FAVORITED_PARAM_NAME,
    IS_SHOPPING_CART_PARAM_NAME
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
            UserSerializerDjoser(
                request.user,
                context={"request": request}).data,
            status=status.HTTP_200_OK
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

    def _get_limit(self, request):
        """Получает limit рецептов или будем выводить все рецепты."""
        try:
            limit = int(request.query_params.get('recipes_limit'))
        except (ValueError, TypeError):
            limit = None
        return {'recipes_limit': limit}

    @action(
        detail=False,
        methods=['GET'],
        url_path=settings.SUBSCRIPTIONS_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Выводит список авторов (с рецептами), на которых подписан user."""
        context = {'request': request, **self._get_limit(request)}
        # Получаем список пользователей, на которых подписаны
        followed_users = self.request.user.followings.values_list(
            'author', flat=True)
        # Подготовим список рецептов с сортировкой
        recipe_prefetch = Prefetch(
            'recipes', queryset=Recipe.objects.order_by(
                *Recipe._meta.ordering)
        )
        # Соединяем рецепты с каждым пользователем, на которого подписаны
        queryset = User.objects.filter(
            id__in=followed_users).prefetch_related(
                recipe_prefetch).order_by(*User._meta.ordering)

        page = self.paginate_queryset(queryset) or []
        return self.get_paginated_response(
            SubscriptionSerializer(page, many=True, context=context).data
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path=settings.SUBSCRIBE_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, *args, **kwargs):
        author = get_object_or_404(User, pk=kwargs['pk'])
        if request.method == 'POST':
            if author == request.user:
                raise ValidationError(SELF_FOLLOWING)
            try:
                Follow.objects.create(
                    follower=request.user,
                    author=author
                )
            except IntegrityError:
                raise ValidationError(FOLLOWING_ERROR)
            context = {'request': request, **self._get_limit(request)}
            return Response(
                SubscriptionSerializer(
                    author,
                    context=context).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            try:
                Follow.objects.get(
                    follower=request.user, author=author).delete()
            except ObjectDoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)


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
    filter_backends = [DjangoFilterBackend]
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

    @action(
        detail=True,
        methods=['GET'],
        url_path=settings.GET_LINK_POINT,
        permission_classes=(AllowAny,)
    )
    def get_short_link(self, request, *args, **kwargs):
        return Response(
            ShortLinkSerializer(
                instance=get_object_or_404(Recipe, pk=kwargs['pk']),
                context={'request': request}
            ).data
        )

    def _general_methods(self, request, param_name, *args, **kwargs):
        """Добавляет рецепт в избранное или список покупок."""
        recipe = get_object_or_404(Recipe, pk=kwargs['pk'])
        if param_name == IS_SHOPPING_CART_PARAM_NAME:
            manager = ShoppingCart.objects
        elif param_name == IS_FAVORITED_PARAM_NAME:
            manager = Favorite.objects
        if request.method == 'POST':
            try:
                manager.create(
                    user=request.user,
                    recipe=recipe
                )
            except IntegrityError:
                raise ValidationError(FOLLOWING_ERROR)
            return Response(
                LimitedRecipesReadSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            try:
                manager.get(
                    user=request.user, recipe=recipe).delete()
            except ObjectDoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path=settings.FAVORITES_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, *args, **kwargs):
        """Добавляет рецепт в избранное."""
        return self._general_methods(
            request, *args, param_name=IS_FAVORITED_PARAM_NAME, **kwargs)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path=settings.SHOPPING_CART_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, *args, **kwargs):
        """Добавляет рецепт в список покупок."""
        return self._general_methods(
            request, *args, param_name=IS_SHOPPING_CART_PARAM_NAME, **kwargs)

    @action(
        detail=False,
        methods=['GET'],
        url_path=settings.DOWNLOAD_CART_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        """Отдаёт файл со списком игредиентов к покупке."""
        recipes_ids = ShoppingCart.objects.values_list(
            'recipe', flat=True).filter(user=request.user)
        ingredients_with_amount = RecipeIngredient.objects.filter(
            recipe__in=recipes_ids).values(
                'ingredient__name', 'ingredient__measurement_unit').annotate(
                total_amount=Sum('amount'))

        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="products.csv"'

        writer = csv.writer(response)  # передаём объект потока вывода
        writer.writerow(['Ingredients', 'Total Amount', 'Measurement_unit'])

        for ingredient in ingredients_with_amount:
            writer.writerow(
                [ingredient['ingredient__name'],
                 ingredient['total_amount'],
                 ingredient['ingredient__measurement_unit']]
            )

        return response
