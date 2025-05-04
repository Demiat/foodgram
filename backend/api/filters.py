from django_filters import rest_framework

from recipes.models import Ingredient


class IngredientFilter(rest_framework.FilterSet):
    """Поиск по частичному вхождению в начале названия ингредиента."""

    name = rest_framework.CharFilter(
        field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
