from django.contrib.auth.models import AbstractUser
from django.db import models

import constants as const
import validators as valid


class CustomUser(AbstractUser):
    """Абстрактная модель пользователя с логином по email."""

    email = models.EmailField(
        max_length=const.MAX_LENGTH_EMAIL,
        verbose_name='Электронная почта',
        unique=True
    )
    username = models.CharField(
        max_length=const.LENGTH_USERNAME,
        verbose_name='Ник',
        unique=True,
        validators=(valid.username_regex_validator,),
        help_text=const.USERNAME_REGEX_TEXT
    )

    first_name = models.CharField(
        max_length=const.LENGTH_USERNAME,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=const.LENGTH_USERNAME,
        verbose_name='Фамилия',
    )
    is_subscribed = models.BooleanField(default=False)
    avatar = models.ImageField(
        'Изображение',
        upload_to='users/',
        blank=True
    )

    # Устанавливаем авторизацию по полю email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username[:const.LENGTH_USERNAME]
