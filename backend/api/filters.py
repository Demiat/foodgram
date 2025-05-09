from django_filters import rest_framework, ModelMultipleChoiceFilter, filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(rest_framework.FilterSet):
    """Поиск по частичному вхождению в начале названия ингредиента."""

    name = rest_framework.CharFilter(
        field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(rest_framework.FilterSet):
    """Фильтр для рецептов с возможностью выбора нескольких тегов и автора."""

    author = filters.CharFilter(field_name="author")
    tags = ModelMultipleChoiceFilter(
        field_name='tags__name',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author')
