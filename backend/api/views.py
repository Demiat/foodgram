from datetime import datetime

from django.conf import settings
from django.db.models import Prefetch, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as UserViewSetDjoser
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import IsAuthOrAuthorOrAdminOrReadOnly
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag, User)

from .constants import FOLLOWING_ERROR, SELF_FOLLOWING
from .filters import IngredientFilter, RecipeFilter
from .serializers import (AvatarSetSerializer, FollowSerializer,
                          IngredientSerializer, LimitedRecipesReadSerializer,
                          RecipesReadSerializer, RecipesWriteSerializer,
                          TagSerializer, UserSerializerDjoser)


class UserViewSet(UserViewSetDjoser):
    """Работает с моделью пользователей."""

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializerDjoser
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
            UserSerializerDjoser(
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
        if request.method == 'PUT':
            serializer = AvatarSetSerializer(
                instance=request.user,
                data=request.data
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        url_path=settings.SUBSCRIPTIONS_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Выводит список авторов (с рецептами), на которых подписан user."""
        # Получаем список пользователей, на которых подписаны
        followed_users = self.request.user.followings.values_list(
            'to_user', flat=True)
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
            FollowSerializer(
                page, many=True, context={'request': request}).data
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path=settings.SUBSCRIBE_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            if author == request.user:
                raise ValidationError(SELF_FOLLOWING)
            if Follow.objects.filter(
                    from_user=request.user, to_user=author).exists():
                raise ValidationError(FOLLOWING_ERROR)
            Follow.objects.create(from_user=request.user, to_user=author)
            return Response(
                FollowSerializer(
                    author,
                    context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        get_object_or_404(
            Follow, from_user=request.user, to_user=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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


class RecipesViewSet(ModelViewSet):
    """Контроллер рецептов."""

    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = (IsAuthOrAuthorOrAdminOrReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete')

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
        return Response({
            'short-link': (
                f'{request.build_absolute_uri("/")}{settings.SHORT_URL_PREFIX}'
                f'{get_object_or_404(Recipe, pk=pk).id}'
            )
        })

    def _favorite_and_shopping_methods(self, request, recipe_id, model):
        """Добавляет рецепт в избранное или список покупок."""
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if request.method == 'POST':
            if model.objects.filter(
                    user=request.user, recipe=recipe).exists():
                raise ValidationError(FOLLOWING_ERROR)
            model.objects.create(user=request.user, recipe=recipe)
            return Response(
                LimitedRecipesReadSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            get_object_or_404(model, user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path=settings.FAVORITES_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        """Добавляет рецепт в избранное."""
        return self._favorite_and_shopping_methods(
            request, recipe_id=pk, Model=Favorite)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        url_path=settings.SHOPPING_CART_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        """Добавляет рецепт в список покупок."""
        return self._favorite_and_shopping_methods(
            request, recipe_id=pk, Model=ShoppingCart)

    @action(
        detail=False,
        methods=['GET'],
        url_path=settings.DOWNLOAD_CART_POINT,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Отдаёт файл со списком игредиентов к покупке."""
        recipes = [rec.recipe for rec in request.user.shoppingcarts.all()]
        ingredients_with_amount = RecipeIngredient.objects.filter(
            recipe__in=recipes).values(
                'ingredient__name', 'ingredient__measurement_unit').annotate(
                total_amount=Sum('amount')).order_by('ingredient__name')

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
