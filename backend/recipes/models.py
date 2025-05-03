from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .constants import (
    MAX_LENGTH_NAME,
    MAX_LENGTH_SLUG,
    MAX_LENGTH_INGRED,
    MAX_LENGTH_TEXT,
    MAX_COOKING_TIME
)
from users.models import User


class Tag(models.Model):
    """Тэги рецептов."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Идентификатор',
        max_length=MAX_LENGTH_SLUG,
        unique=True
    )


class Ingredient(models.Model):
    """Ингредиенты для рецептов."""

    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=MAX_LENGTH_NAME,
        unique=True
    )
    measurement_unit = models.CharField(
        verbose_name='Ед. измерения',
        max_length=MAX_LENGTH_INGRED,
    )
    # amount = models.PositiveSmallIntegerField()


class Recipe(models.Model):
    """Карточка рецепта."""

    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    is_favorited = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)
    name = models.CharField(
        verbose_name='Рецепт',
        max_length=MAX_LENGTH_NAME,
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
        upload_to='recipes/images/',
    )


class RecipeIngredient(models.Model):
    """Связующая модель рецептов и ингредиентов с количеством."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(verbose_name="Количество")


class FavoriteShoppingCartAbstractModel(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        default_related_name = '%(model_name)ss'


class Favorite(FavoriteShoppingCartAbstractModel):

    class Meta(FavoriteShoppingCartAbstractModel.Meta):
        verbose_name = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            ),
        )


class ShoppingCart(FavoriteShoppingCartAbstractModel):

    class Meta(FavoriteShoppingCartAbstractModel.Meta):
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart'
            ),
        )
        verbose_name = 'Список покупок'
