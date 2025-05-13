import uuid
from typing import List

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User

from .constants import (MAX_COOKING_TIME, MAX_LENGTH_INGRED, MAX_LENGTH_LINK,
                        MAX_LENGTH_NAME, MAX_LENGTH_SLUG, MAX_LENGTH_TEXT)


class RecipesBaseModel(models.Model):

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME
    )

    def __str__(self):
        return self.name[:50]

    class Meta:
        abstract = True


class Tag(RecipesBaseModel):
    """Тэги рецептов."""

    slug = models.SlugField(
        verbose_name='Slug-идентификатор',
        max_length=MAX_LENGTH_SLUG,
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)


class Ingredient(RecipesBaseModel):
    """Ингредиенты для рецептов."""

    measurement_unit = models.CharField(
        verbose_name='Ед. измерения',
        max_length=MAX_LENGTH_INGRED,
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name',)


class Recipe(RecipesBaseModel):
    """Карточка рецепта."""

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes_tags',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes_ingredients'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        max_length=MAX_LENGTH_TEXT
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (мин.)',
        validators=[
            MinValueValidator(1),
            MaxValueValidator(MAX_COOKING_TIME)
        ]
    )
    image = models.ImageField(
        'Изображение рецепта',
        upload_to='recipes/',
    )
    short_code = models.CharField(
        'short-link рецепта',
        max_length=MAX_LENGTH_LINK,
        default=None,
        null=True,
        unique=True
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    def save(self, *args, **kwargs):
        """Создает и сохраняет уникальный код для короткой ссылки на рецепт."""
        if not self.short_code:
            self.short_code = uuid.uuid4().hex[:MAX_LENGTH_LINK]
            while Recipe.objects.filter(short_code=self.short_code).exists():
                self.short_code = uuid.uuid4().hex[:MAX_LENGTH_LINK]
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)


class RecipeIngredient(models.Model):
    """Связующая модель рецептов и ингредиентов с количеством."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(verbose_name="Количество")

    def __str__(self):
        return f'{self.recipe}: {self.ingredient}'

    class Meta:
        verbose_name = 'Рецепт с количеством ингредиента'
        verbose_name_plural = 'Рецепты с количеством ингредиентов'


class FavoriteShoppingBaseModel(models.Model):
    """Базовый абстрактный класс для избранного и списка покупок рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.user}: {self.recipe}'

    @staticmethod
    def _get_unique_constraint(constraint_name):
        return models.UniqueConstraint(
            fields=('user', 'recipe'), name=constraint_name)

    class Meta:
        abstract = True
        constraints: List[models.UniqueConstraint] = []


class Favorite(FavoriteShoppingBaseModel):
    """Избранные рецепты."""

    class Meta(FavoriteShoppingBaseModel.Meta):
        constraints = [
            FavoriteShoppingBaseModel._get_unique_constraint('favorite_unique')
        ]
        verbose_name_plural = 'Избранное'


class ShoppingCart(FavoriteShoppingBaseModel):
    """Список покупок для рецептов."""

    class Meta(FavoriteShoppingBaseModel.Meta):
        constraints = [
            FavoriteShoppingBaseModel._get_unique_constraint('shopping_unique')
        ]
        verbose_name_plural = 'Список покупок'
