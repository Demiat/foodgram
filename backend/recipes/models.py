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
        verbose_name='Slug-идентификатор',
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


class Recipe(models.Model):
    """Карточка рецепта."""

    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes_ingredients'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
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

    def __str__(self):
        return self.name

    @property
    def is_favorited(self):
        """
        Проверяет, содержится ли рецепт в избранном у текущего пользователя.
        Передать в контекстах обработки: obj._request_user = self.request.user
        """
        if hasattr(self, '_request_user'):
            user = getattr(self, '_request_user')
            return self.favorites.filter(recipe=self, user=user).exists()
        else:
            return False

    @property
    def is_in_shopping_cart(self):
        """
        Проверяет, содержится ли рецепт в списке покупок текущего пользователя.
        Передать в контекстах обработки: obj._request_user = self.request.user
        """
        if hasattr(self, '_request_user'):
            user = getattr(self, '_request_user')
            return self.shoppingcarts.filter(recipe=self, user=user).exists()
        else:
            return False


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
