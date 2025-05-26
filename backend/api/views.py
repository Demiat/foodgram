from datetime import datetime

from django.conf import settings
from django.db.models import Prefetch, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as UserViewSetDjoser
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    SAFE_METHODS, AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import IsAuthorOrReadOnly
from recipes.constants import RECIPE_NOT_FOUND
from recipes.models import (
    Favorite, Follow, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
    User
)

from .filters import IngredientFilter, RecipeFilter
from .serializers import (
    AvatarSetSerializer, IngredientSerializer, RecipesOfUserSerializer,
    RecipesReadSerializer, RecipesWriteSerializer, ShortRecipesReadSerializer,
    TagSerializer, UserSerializer
)

FOLLOWING_ERROR = 'Подписка на {} уже есть!'
RECORD_ERROR = 'Запись рецепта с id {} в модели {} уже есть в базе!'
SELF_FOLLOWING = 'Нельзя подписаться на самого себя!'


class UserViewSet(UserViewSetDjoser):
    """Работает с моделью пользователей."""

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    http_method_names = ('get', 'post', 'put', 'delete')

    @action(
        detail=False,
        methods=['GET'],
        url_path=settings.SELF_PROFILE_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def get_me_data(self, request):
        """Получение своей учетной записи."""
        return Response(
            UserSerializer(
                request.user,
                context={'request': request}).data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['PUT', 'DELETE'],
        url_path=f'{settings.SELF_PROFILE_POINT}/{settings.AVATAR_POINT}',
        permission_classes=(IsAuthenticated,)
    )
    def set_or_delete_avatar(self, request):
        """Установка или удаление аватарки пользователя."""
        if request.method != 'PUT':
            request.user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSetSerializer(
            instance=request.user,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['GET'],
        url_path=settings.SUBSCRIPTIONS_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Выводит список авторов (с рецептами), на которых подписан user."""
        # Получаем список пользователей, на которых подписаны
        followed_users = self.request.user.followers.values_list(
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
            RecipesOfUserSerializer(
                page, many=True, context={'request': request}).data
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path=settings.SUBSCRIBE_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        if request.method != 'POST':
            get_object_or_404(
                Follow, from_user=request.user, author_id=id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        author = get_object_or_404(User, pk=id)
        if author == request.user:
            raise ValidationError(SELF_FOLLOWING)
        follow_obj, created = Follow.objects.get_or_create(
            from_user=request.user,
            author=author
        )
        if not created:
            raise ValidationError(FOLLOWING_ERROR.format(author))
        return Response(
            RecipesOfUserSerializer(
                author,
                context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class TagsViewSet(ReadOnlyModelViewSet):
    """Контроллер Тэгов, GET."""

    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer
    pagination_class = None


class IngredientsViewSet(ReadOnlyModelViewSet):
    """Контроллер продуктов, GET."""

    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class CustomPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'


class RecipesViewSet(ModelViewSet):
    """Контроллер рецептов."""

    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete')
    # pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

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
    def get_short_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise ValidationError(RECIPE_NOT_FOUND.format(pk))
        return Response({
            'short-link': request.build_absolute_uri(
                reverse('recipes:recipe_short_link', args=[pk])
            )
        })

    def _favorite_and_shopping_methods(self, request, recipe_id, model):
        """Добавляет рецепт в избранное или список покупок."""
        if request.method != 'POST':
            get_object_or_404(
                model, user=request.user, recipe_id=recipe_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        model_obj, created = model.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if not created:
            raise ValidationError(
                RECORD_ERROR.format(recipe_id, model._meta.verbose_name)
            )
        return Response(
            ShortRecipesReadSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path=settings.FAVORITES_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Добавляет рецепт в избранное."""
        return self._favorite_and_shopping_methods(
            request, recipe_id=pk, model=Favorite)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path=settings.SHOPPING_CART_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Добавляет рецепт в список покупок."""
        return self._favorite_and_shopping_methods(
            request, recipe_id=pk, model=ShoppingCart)

    @action(
        detail=False,
        methods=['GET'],
        url_path=settings.DOWNLOAD_CART_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Отдаёт файл со списком продуктов к покупке."""
        recipes = [rec.recipe for rec in request.user.shoppingcarts.all()]
        ingredients_with_amount = RecipeIngredient.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by(
            'ingredient__name'
        )

        content = render_to_string(
            'shop_template.txt', {
                'current_date': datetime.now(),
                'ingredients': ingredients_with_amount,
                'recipes': recipes,
            }
        )

        return FileResponse(
            content,
            as_attachment=True,
            filename=f'shopping_list_{datetime.now().strftime("%d.%m.%Y")}.txt'
        )
