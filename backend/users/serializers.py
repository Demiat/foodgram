import base64

from djoser.serializers import UserCreateSerializer, UserSerializer
from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import User
from .validators import username_regex_validator


class UserSerializerDjoser(UserSerializer):

    avatar = serializers.ImageField(read_only=True)

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )
        read_only_fields = ('avatar', 'is_subscribed')


class UserCreateSerializerDjoser(UserCreateSerializer):
    """Обрабатывает создание модели User."""

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id',)

    def validate_username(self, username):
        username_regex_validator(username)
        return username


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format_img, imgstr = data.split(';base64,')
            ext = format_img.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class AvatarSetSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)
