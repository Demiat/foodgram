from django_filters import rest_framework, ModelMultipleChoiceFilter, filters
from rest_framework.filters import BaseFilterBackend
from django.db.models import Exists, OuterRef

from recipes.models import Ingredient, Recipe, Tag, ShoppingCart


class IngredientFilter(rest_framework.FilterSet):
    """Поиск по частичному вхождению в начале названия ингредиента."""

    name = rest_framework.CharFilter(
        field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(rest_framework.FilterSet):
    """Фильтр для рецептов с возможностью выбора нескольких тегов и автора."""

    author = filters.CharFilter(field_name='author')
    tags = ModelMultipleChoiceFilter(
        field_name='tags__name',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    # is_in_shopping_cart = filters.BooleanFilter(
    #     field_name='is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    # def filter_is_in_shopping_cart(self, queryset, name, value):
    #     if value and self.request.user.is_authenticated:
    #         return queryset.annotate(
    #             in_shopping_cart=Exists(
    #                 ShoppingCart.objects.filter(
    #                     user=self.request.user, recipe=OuterRef('pk')
    #                 )
    #             )
    #         ).filter(in_shopping_cart=value)
    #     return queryset


class ShoppingCartFilter(BaseFilterBackend):
    """Фильтрует рецепты по признаку присутствия в списке покупок."""

    def filter_queryset(self, request, queryset, view):
        if not request.user.is_authenticated:
            return queryset.none()

        return queryset.annotate(
            in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=request.user, recipe=OuterRef('pk')
                )
            )
        ).filter(in_shopping_cart=True)
