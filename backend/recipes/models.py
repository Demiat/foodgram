import uuid
from typing import List

from django.contrib.auth.models import AbstractUser
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from .constants import (LENGTH_USERNAME, MAX_COOKING_TIME, MAX_LENGTH_EMAIL,
                        MAX_LENGTH_INGRED, MAX_LENGTH_LINK, MAX_LENGTH_NAME,
                        MAX_LENGTH_SLUG, MAX_LENGTH_TEXT, USERNAME_REGEX,
                        USERNAME_REGEX_TEXT)


class User(AbstractUser):
    """Кастомная модель пользователя с логином по email."""

    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        verbose_name='Электронная почта',
        unique=True
    )
    username = models.CharField(
        max_length=LENGTH_USERNAME,
        verbose_name='Ник',
        unique=True,
        validators=[
            RegexValidator(regex=USERNAME_REGEX, message=USERNAME_REGEX_TEXT)
        ],
        help_text=USERNAME_REGEX_TEXT
    )
    first_name = models.CharField(
        max_length=LENGTH_USERNAME,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=LENGTH_USERNAME,
        verbose_name='Фамилия',
    )
    avatar = models.ImageField(
        'Изображение',
        upload_to='users/',
        blank=True,
        null=True
    )

    # Устанавливаем авторизацию по полю email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username

    def check_subscription(self, author):
        """Подписан ли текущий пользователь на указанного автора."""
        if isinstance(author, User):
            return self.followings.filter(author=author).exists()


class Follow(models.Model):
    """
    Поле follower обозначает пользователя, подписанного на автора.
    Поле author обозначает пользователя, на которого
    подписаны другие пользователи.

    ivan.followings.all() - вернёт всех авторов, на которых подписан Иван
    maria.followers.all() - вернёт всех пользов., которые подписались на Марию
    """

    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followings',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Автор'
    )

    def __str__(self):
        return f'{self.follower}: {self.author}'

    class Meta:
        verbose_name_plural = 'Подписчики'
        constraints = (
            models.UniqueConstraint(
                fields=('follower', 'author'),
                name='unique_follow'
            ),
        )


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
        verbose_name='Идентификатор',
        max_length=MAX_LENGTH_SLUG,
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)


class Ingredient(RecipesBaseModel):
    """Продукты для рецептов."""

    measurement_unit = models.CharField(
        verbose_name='Мера',
        max_length=MAX_LENGTH_INGRED,
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
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
    """Связующая модель рецептов и продуктов с количеством."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(verbose_name='Количество')

    def __str__(self):
        return f'{self.recipe}: {self.ingredient}'

    class Meta:
        verbose_name = 'Рецепт с количеством продукта'
        verbose_name_plural = 'Рецепты с количеством продуктов'


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
