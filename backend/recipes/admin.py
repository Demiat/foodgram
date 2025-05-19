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

    list_display: list[str] = ['recipes_count']

    def recipes_count(self, obj):
        """Считает рецепты для связанного объекта"""
        return obj.recipes.count()
    recipes_count.short_description = 'Рецептов'


class GetImageMixin:

    @mark_safe
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
    image_miniature.short_description = 'Изображение'


class HasRecipesFilter(admin.SimpleListFilter):
    """Фильтрует по признаку наличия рецептов."""

    title = 'Наличие рецептов'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'С рецептами'),
            ('no', 'Без рецептов'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        elif self.value() == 'no':
            return queryset.filter(recipes=None)
        return queryset


class UserRelationshipFilter(admin.SimpleListFilter):
    """Выводит пользователей по наличию подписок и подписчиков."""

    title = 'Подписки и подписчики'
    parameter_name = 'relationship_status'

    def lookups(self, request, model_admin):
        return (
            ('subscribed', 'Подписан на кого-то'),
            ('followed', 'Есть подписчики'),
            ('both', 'И подписан, и есть подписчики'),
            ('none', 'Ни подписок, ни подписчиков'),
        )

    def queryset(self, request, queryset):
        subscribed_users = Follow.objects.filter(
            from_user=OuterRef('pk'))  # Подписки
        followed_by_users = Follow.objects.filter(
            to_user=OuterRef('pk'))  # Подписчики

        if self.value() == 'subscribed':
            return queryset.annotate(
                has_subscription=Exists(subscribed_users)
            ).filter(has_subscription=True)

        elif self.value() == 'followed':
            return queryset.annotate(
                has_follower=Exists(followed_by_users)
            ).filter(has_follower=True)

        elif self.value() == 'both':  # И подписан и есть подписчики
            return queryset.annotate(
                has_subscription=Exists(subscribed_users),
                has_follower=Exists(followed_by_users)
            ).filter(has_subscription=True, has_follower=True)

        elif self.value() == 'none':  # Ни подписок, ни подписчиков
            return queryset.annotate(
                has_subscription=Exists(subscribed_users),
                has_follower=Exists(followed_by_users)
            ).filter(has_subscription=False, has_follower=False)

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
        if not getattr(self, 'is_valid', False):
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
class UserAdmin(BaseUserAdmin, RecipesCountMixin, GetImageMixin):
    search_fields = ('email', 'username')
    list_display = [
        'id', 'username', 'full_name', 'email', 'image_miniature',
        'subscription_count', 'follower_count'
    ] + RecipesCountMixin.list_display
    list_filter = (
        'is_active', 'is_staff', 'is_superuser',
        UserRelationshipFilter, HasRecipesFilter
    )

    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'.strip()

    def subscription_count(self, user):
        return user.followings.count()

    def follower_count(self, user):
        return user.followers.count()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    pass


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

    # Количество избранных рецептов
    def favorite_count(self, obj):
        """Показывает сколько рецептов в избранном."""
        return obj.favorites.count()
    favorite_count.short_description = 'В Избранном'

    @mark_safe
    def product_list(self, obj):
        """Выводит список продуктов в рецептах."""
        return '<br>'.join(f'- {item}' for item in obj.ingredients.all())
    product_list.short_description = 'Продукты'


@admin.register(ShoppingCart, Favorite)
class FavoriteShoppingCartAdmin(admin.ModelAdmin):
    pass
