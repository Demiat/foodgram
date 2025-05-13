from django_filters import rest_framework, ModelMultipleChoiceFilter, filters
from django.db.models import Exists, OuterRef, Case, When, Value, CharField

from recipes.models import Ingredient, Recipe, Tag, ShoppingCart, Favorite
from .constants import IS_FAVORITED_PARAM_NAME, IS_SHOPPING_CART_PARAM_NAME


class IngredientFilter(rest_framework.FilterSet):
    """Поиск по частичному вхождению в начале названия ингредиента."""

    name = filters.CharFilter(method='combined_search')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def combined_search(self, queryset, name, value):
        """
        Выводит ингредиенты в порядке приоритета сначала по совпадению
        в начале строки, потом в оставшейся части.
        C этой целью создает признак (временное поле в базе) приоритета
        со значением 1 для записей, в которых совпадение в начале строки.
        """
        return queryset.annotate(
            priority=Case(
                When(name__istartswith=value, then=Value(1)),
                default=Value(2),
                output_field=CharField()
            )
        ).filter(name__icontains=value).order_by('priority', 'name')


class RecipeFilter(rest_framework.FilterSet):
    """
    Фильтр для рецептов с возможностью выбора нескольких тегов и автора,
    а также флагов: в избранном, в списке покупок.
    """

    author = filters.CharFilter(field_name='author')
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_in_shopping_cart = filters.CharFilter(
        method='general_method')
    is_favorited = filters.CharFilter(
        method='general_method')

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def general_method(self, queryset, name, value):
        if not value or not self.request.user.is_authenticated:
            return queryset
        if name == IS_SHOPPING_CART_PARAM_NAME:
            manager = ShoppingCart.objects
        elif name == IS_FAVORITED_PARAM_NAME:
            manager = Favorite.objects
        # Создадим поле-признак существования записей с таким пользователем и
        # рецептом из модели флага, соответствующим общей модели рецептов.
        # Отфильтруем записи по этому полю-признаку.
        return queryset.annotate(
            in_shopping_cart=Exists(
                manager.filter(user=self.request.user, recipe=OuterRef('pk'))
            )
        ).filter(in_shopping_cart=value)
