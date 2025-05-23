from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constants import MIN_AMOUNT, MIN_COOKING_TIME

MAX_LENGTH_NAME = 256
OUTPUT_LIMITATION_NAME = 50
MAX_LENGTH_TAG_SLUG = 32
MAX_LENGTH_TAG_NAME = 32
MAX_LENGTH_INGRED = 128
MAX_LENGTH_MEASUREMENT = 64
MAX_LENGTH_EMAIL = 254
LENGTH_USERNAME = 150
USERNAME_REGEX_TEXT = 'Имя может содержать только буквы, цифры и знаки .@+-_'
USERNAME_REGEX = r'^[\w.@+-]+$'


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


class Follow(models.Model):
    """
    Модель описывает связь между пользователями, где один пользователь
    подписан на другого.

    Поля:
    - from_user: Пользователь, который подписался (инициатор подписки).
    - author: Пользователь, на которого подписываются (получатель подписки).
    """

    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Кто подписался'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='На кого подписались'
    )

    def __str__(self):
        return f'{self.from_user} подписан на {self.author}'

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        constraints = (
            models.UniqueConstraint(
                fields=('from_user', 'author'),
                name='unique_followers'
            ),
        )


class Tag(models.Model):
    """Тэги рецептов."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_TAG_NAME
    )

    slug = models.SlugField(
        verbose_name='Идентификатор',
        max_length=MAX_LENGTH_TAG_SLUG,
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Продукты для рецептов."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_INGRED
    )

    measurement_unit = models.CharField(
        verbose_name='Ед.измерения',
        max_length=MAX_LENGTH_MEASUREMENT,
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient'
            ),
        )

    def __str__(self):
        return self.name[:OUTPUT_LIMITATION_NAME]


class Recipe(models.Model):
    """Карточка рецепта."""

    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME
    )
    tags = models.ManyToManyField(Tag)
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Продукт',
        through='RecipeIngredient',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (мин.)',
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
        ]
    )
    image = models.ImageField(
        'Изображение рецепта',
        upload_to='recipes/',
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        default_related_name = '%(model_name)ss'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:OUTPUT_LIMITATION_NAME]


class RecipeIngredient(models.Model):
    """Связующая модель рецептов и продуктов с мерой."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Продукт'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Мера',
        validators=[
            MinValueValidator(MIN_AMOUNT),
        ]
    )

    def __str__(self):
        return f'{self.recipe}: {self.ingredient}'

    class Meta:
        default_related_name = '%(model_name)ss'
        verbose_name = 'Продукт в рецепте с мерой'
        verbose_name_plural = 'Продукты в рецептах с мерой'


class AbstractUserRecipeRelation(models.Model):
    """Базовый абстрактный класс для избранного и списка покупок рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.user}: {self.recipe}'

    class Meta:
        abstract = True
        default_related_name = '%(model_name)ss'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique'
            )
        ]


class Favorite(AbstractUserRecipeRelation):
    """Избранные рецепты."""

    class Meta(AbstractUserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(AbstractUserRecipeRelation):
    """Список покупок для рецептов."""

    class Meta(AbstractUserRecipeRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
