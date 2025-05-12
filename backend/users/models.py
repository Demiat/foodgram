from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import (
    MAX_LENGTH_EMAIL,
    LENGTH_USERNAME,
    USERNAME_REGEX_TEXT,
)
from .validators import username_regex_validator


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
        validators=(username_regex_validator,),
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
    REQUIRED_FIELDS = ('username',)

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
        related_name="followings",
        verbose_name="Подписчик"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name="Автор"
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
