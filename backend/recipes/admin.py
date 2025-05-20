import numpy
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import (Case, CharField, Count, Exists, Max, OuterRef,
                              Value, When)
from django.utils.safestring import mark_safe

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, User)

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
    parameter_name = 'Subscriptions'
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

    title = 'Подписчики'
    parameter_name = 'Followers'
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
    parameter_name = 'cooking_time'

    def recipes_and_cooking_times_calculate(self):
        self.cooking_times = sorted(
            Recipe.objects.values_list('cooking_time', flat=True)
        )
        # Создаем гистограмму с тремя бинами
        self.number_recipes, self.time_levels = numpy.histogram(
            self.cooking_times, bins=3)
        # self.fast = self.time_levels[1]
        # self.medium = self.time_levels[2]

    def lookups(self, request, model_admin):
        # Раннее завершение, если нет данных
        # if not getattr(self, 'is_valid', False):
        #     return []
        

        # Разделим все рецепты на 3 категории по времени готовки
        # Для этого создадим поле-признак category и заполним его по условиям
        # results = Recipe.objects.annotate(
        #     category=Case(
        #         When(cooking_time__lt=self.fast, then=Value('fast')),
        #         When(
        #             cooking_time__gte=self.fast,
        #             cooking_time__lte=self.medium,
        #             then=Value('medium')),
        #         default=Value('slow'),
        #         output_field=CharField(),
        #     ),
        #     # Сгруппируем записи по полю category и посчитаем кол-во этих полей
        # ).values('category').annotate(
        #     recipes_count=Count('id')).order_by('category')

        # result_data = {}
        # for item in results:
        #     if item['category'] == 'fast':
        #         result_data['fast'] = item['recipes_count']
        #     elif item['category'] == 'medium':
        #         result_data['medium'] = item['recipes_count']
        #     elif item['category'] == 'slow':
        #         result_data['slow'] = item['recipes_count']

        return [
            ('fast', 'Быстрее {} мин. Рецептов ({})'.format(
                self.fast, result_data.get('fast', 0))),
            ('medium', 'Быстрее {} мин. Рецептов ({})'.format(
                self.medium, result_data.get('medium', 0))),
            ('slow', 'Дольше {} мин. Рецептов ({})'.format(
                self.medium, result_data.get('slow', 0))),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'fast':
            return queryset.filter(cooking_time__lt=self.fast)
        elif value == 'medium':
            return queryset.filter(cooking_time__range=(
                self.fast, self.medium))
        elif value == 'slow':
            return queryset.filter(cooking_time__gt=self.medium)
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

    @admin.display(description='Подписки')
    def subscription_count(self, user):
        return user.authors.count()

    @admin.display(description='Подписчики')
    def follower_count(self, user):
        return user.followers.count()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    search_fields = ('from_user__username', 'from_user__email',
                     'author__username', 'author__email')
    list_filter = ('from_user', 'author')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin, RecipesCountMixin):
    list_display = ['name', 'slug'] + RecipesCountMixin.list_display
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin, RecipesCountMixin):
    list_display = [
        'name', 'measurement_unit'] + RecipesCountMixin.list_display
    search_fields = ('name', 'measurement_unit')
    list_filter = (HasRecipesFilter,)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


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
    list_filter = ('tags', 'author', CookingTimeFilter)

    @admin.display(description='В Избранном')
    def favorite_count(self, obj):
        """Показывает сколько рецептов в избранном."""
        return obj.favorites.count()

    @mark_safe
    def product_list(self, obj):
        """Выводит список продуктов в рецептах."""
        return '<br>'.join(f'- {item}' for item in obj.ingredients.all())
    product_list.short_description = 'Продукты'


@admin.register(ShoppingCart, Favorite)
class FavoriteShoppingCartAdmin(admin.ModelAdmin):
    pass
