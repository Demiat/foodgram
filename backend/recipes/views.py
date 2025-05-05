from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend

from .models import Recipe, Ingredient, Tag
from api.filters import IngredientFilter
from api.serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipesSerializer,
)


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
    serializer_class = RecipesSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination
    http_method_names = ('get', 'post', 'patch', 'delete')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
