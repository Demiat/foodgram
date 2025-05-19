from django.contrib import admin
from django.utils.safestring import mark_safe
from django.db.models import Case, When, CharField, Value, Count, Max, Exists, OuterRef

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, User)

admin.site.empty_value_display = '-пусто-'


class RecipesCountMixin(admin.ModelAdmin):
    list_display: list[str] = ['recipes_count']

    def recipes_count(self, obj):
        """Рецептов"""
        return obj.recipes.count()
    recipes_count.short_description = 'Рецептов'


class HasRecipesFilter(admin.SimpleListFilter):
    title = 'Продукты, использованные в рецептах'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Используются в рецептах'),
            ('no', 'Не используются в рецептах'),
        )

    def queryset(self, request, queryset):
        exists_query = Recipe.objects.filter(ingredients=OuterRef('pk'))
        if self.value() == 'yes':
            return queryset.annotate(has_recipe=Exists(
                exists_query)).filter(has_recipe=True)
        elif self.value() == 'no':
            return queryset.annotate(has_recipe=Exists(
                exists_query)).filter(has_recipe=False)
        return queryset


class CookingTimeFilter(admin.SimpleListFilter):
    """
    Делит время приготовления на 3 категории, считает кол-во
    рецептов в каждой такой категории.
    """

    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def __init__(self, request, params, model, model_admin):
        # Рассчитаем пороговые значения для фильтрации
        # исходя из самих данных времени приготовления в рецептах
        self.max_cooking_time = model.objects.aggregate(
            Max('cooking_time'))['cooking_time__max']
        if self.max_cooking_time is None or self.max_cooking_time == 0:
            # Если нет записей или 0, устанавливаем флаг выхода
            self.is_valid = False
        else:
            self.fast = self.max_cooking_time // 3
            self.medium = self.fast * 2
            self.is_valid = True
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        # Раннее завершение, если нет данных
        if not getattr(self, 'is_valid', True):
            return []

        # Разделим все рецепты на 3 категории по времени готовки
        # Для этого создадим поле-признак category и заполним его по условиям
        results = Recipe.objects.annotate(
            category=Case(
                When(cooking_time__lt=self.fast, then=Value('fast')),
                When(
                    cooking_time__gte=self.fast,
                    cooking_time__lte=self.medium,
                    then=Value('medium')),
                default=Value('slow'),
                output_field=CharField(),
            ),
            # Сгруппируем записи по полю category и посчитаем кол-во этих полей
        ).values('category').annotate(
            recipes_count=Count('id')).order_by('category')

        result_data = {}
        for item in results:
            if item['category'] == 'fast':
                result_data['fast'] = item['recipes_count']
            elif item['category'] == 'medium':
                result_data['medium'] = item['recipes_count']
            elif item['category'] == 'slow':
                result_data['slow'] = item['recipes_count']

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
class UserAdmin(admin.ModelAdmin):
    search_fields = ('email', 'username')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    pass


@admin.register(Tag)
class TagAdmin(RecipesCountMixin):
    list_display = RecipesCountMixin.list_display + ['name', 'slug']
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(RecipesCountMixin):
    list_display = RecipesCountMixin.list_display + [
        'name', 'measurement_unit']
    search_fields = ('name', 'measurement_unit')
    list_filter = (HasRecipesFilter,)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
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

    # Количество избранных рецептов
    def favorite_count(self, obj):
        """В Избранном"""
        return obj.favorites.count()
    favorite_count.short_description = 'В Избранном'

    # Формирование списка продуктов
    @mark_safe
    def product_list(self, obj):
        items = '<br>'.join(f'- {item}' for item in obj.ingredients.all())
        return f'<div>{items}</div>'
    product_list.short_description = 'Продукты'

    # Просмотр миниатюр изображения
    @mark_safe
    def image_miniature(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" alt="{obj.name}" width="50">'
        return '-'
    image_miniature.short_description = 'Изображение'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    pass


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    pass
