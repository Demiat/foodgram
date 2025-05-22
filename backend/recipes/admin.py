import numpy
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe

from .models import (
    Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
    ShoppingCart, Tag, User
)

admin.site.empty_value_display = '-пусто-'


class RecipesCountMixin:
    """Показывает кол-во рецептов для того или иного связанного объекта."""

    list_display = ['recipes_count']

    @admin.display(description='Рецептов')
    def recipes_count(self, obj):
        """Считает рецепты для связанного объекта"""
        return obj.recipes.count()


class GetImageMixin:

    @mark_safe
    @admin.display(description='Изображение')
    def image_miniature(self, obj):
        """Выводит изображение в миниатюре для Пользователей и Рецептов."""
        if hasattr(obj, 'image'):
            image_obj = obj.image
            obj_name = obj.name
        else:
            image_obj = obj.avatar
            obj_name = obj.username
        if image_obj:
            return f'<img src="{image_obj.url}" alt="{obj_name}" width="50">'
        return 'not image'


class HasRecipesFilter(admin.SimpleListFilter):
    """Фильтрует по признаку наличия рецептов."""

    title = 'Наличие рецептов'
    parameter_name = 'has_recipes'
    OPTIONS = (
        ('yes', 'С рецептами'),
        ('no', 'Без рецептов'),
    )

    def lookups(self, request, model_admin):
        return self.OPTIONS

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        elif self.value() == 'no':
            return queryset.filter(recipes=None)
        return queryset


class HasSubscriptionFilter(admin.SimpleListFilter):
    """Выводит авторов, на которых есть подписки."""

    title = 'Подписки'
    parameter_name = 'subscriptions'
    OPTIONS = (
        ('yes', 'Есть подписки?'),
        ('no', 'Нет подписок'),
    )

    def lookups(self, request, model_admin):
        return self.OPTIONS

    def queryset(self, request, users):
        if self.value() == 'yes':
            return users.filter(authors__isnull=False).distinct()
        elif self.value() == 'no':
            return users.filter(authors=None)
        return users


class HasFollowersFilter(admin.SimpleListFilter):
    """Выводит пользователей, которые подписаны на авторов."""

    title = 'Подписавшиеся'
    parameter_name = 'followers'
    OPTIONS = (
        ('yes', 'Подписан на кого-то?'),
        ('no', 'Нет подписок'),
    )

    def lookups(self, request, model_admin):
        return self.OPTIONS

    def queryset(self, request, users):
        if self.value() == 'yes':
            return users.filter(followers__isnull=False).distinct()
        elif self.value() == 'no':
            return users.filter(followers=None)
        return users


class CookingTimeFilter(admin.SimpleListFilter):
    """
    Делит время приготовления на 3 категории, считает кол-во
    рецептов в каждой такой категории.
    """

    title = 'Время приготовления'
    parameter_name = 'cooking_time__range'

    def filter_by_range(self, value_range, queryset=None):
        base_queryset = queryset or Recipe.objects.all()
        value_range = tuple(map(int, value_range.split()))
        return base_queryset.filter(cooking_time__range=value_range)

    def lookups(self, request, model_admin):
        cooking_times = sorted(
            Recipe.objects.values_list('cooking_time', flat=True)
        )
        number_recipes, time_levels = numpy.histogram(
            cooking_times, bins=3)
        time_levels = list(map(int, time_levels))

        # Первый параметр в возврате есть строковое
        # представление диапазона времени готовки
        return [
            (
                f'0 {time_levels[1]}',  # Быстрые
                'Быстрее {} мин. Рецептов ({})'.format(
                    time_levels[1], number_recipes[0]
                )
            ),
            (
                f'{time_levels[1]} {time_levels[2]}',  # Средние
                'Быстрее {} мин. Рецептов ({})'.format(
                    time_levels[2], number_recipes[1]
                )
            ),
            (
                f'{time_levels[2]} {time_levels[3]}',  # Долгие
                'Дольше {} мин. Рецептов ({})'.format(
                    time_levels[2], number_recipes[2]
                )
            ),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return self.filter_by_range(self.value(), queryset)
        return queryset


@admin.register(User)
class UserAdmin(BaseUserAdmin, RecipesCountMixin, GetImageMixin):
    search_fields = ('email', 'username')
    list_display = [
        'id', 'username', 'full_name', 'email', 'image_miniature',
        'subscription_count', 'follower_count'
    ] + RecipesCountMixin.list_display
    list_filter = (
        'is_active', 'is_staff', 'is_superuser',
        HasSubscriptionFilter, HasFollowersFilter, HasRecipesFilter
    )

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'.strip()

    @admin.display(description='Подписчиков')
    def subscription_count(self, user):
        return user.authors.count()

    @admin.display(description='Подписан на')
    def follower_count(self, user):
        return user.followers.count()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    search_fields = ('from_user__username', 'from_user__email',
                     'author__username', 'author__email')
    list_filter = ('from_user', 'author')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin, RecipesCountMixin):
    list_display = ['name', 'slug', *RecipesCountMixin.list_display]
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin, RecipesCountMixin):
    list_display = [
        'name', 'measurement_unit', *RecipesCountMixin.list_display]
    search_fields = ('name', 'measurement_unit')
    list_filter = (HasRecipesFilter,)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin, GetImageMixin):
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'favorite_count',
        'product_list',
        'image_miniature',
    )
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = (
        'tags',
        ('author', admin.RelatedOnlyFieldListFilter),
        CookingTimeFilter
    )

    @admin.display(description='В Избранном')
    def favorite_count(self, recipe):
        """Показывает сколько рецептов в избранном."""
        return recipe.favorites.count()

    @admin.display(description='Продукты')
    @mark_safe
    def product_list(self, recipe):
        """Выводит список продуктов в рецептах."""
        products = '<br>'.join(
            f'- {ingredient.name}' for ingredient in recipe.ingredients.all()
        )
        return f'<div style="white-space: nowrap;">{products}</div>'


@admin.register(ShoppingCart, Favorite)
class FavoriteShoppingCartAdmin(admin.ModelAdmin):
    pass
