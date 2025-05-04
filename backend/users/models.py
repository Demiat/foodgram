from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import MAX_LENGTH_EMAIL, LENGTH_USERNAME, USERNAME_REGEX_TEXT
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
        return self.username[:LENGTH_USERNAME]

    @property
    def is_subscribed(self):
        """
        Проверяет, подписан ли пользователь на другого пользователя.
        Предполагается наличие атрибута request.user
        в контексте запросов Django: obj._request_user = self.request.user
        """
        if hasattr(self, '_request_user'):
            user = getattr(self, '_request_user')
            return self.follows.filter(following=self, user=user).exists()
        else:
            return False


class Follow(models.Model):
    """Подписчики."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followed_by'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique_follow'
            ),
        )
        default_related_name = '%(model_name)ss'
