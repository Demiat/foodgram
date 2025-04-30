import base64

from djoser.serializers import UserCreateSerializer
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

import users.models as mod
import users.validators as valid


class UserCreateSerializerForDjoser(UserCreateSerializer):
    """Обрабатывает модель пользователей User через Djoser."""

    class Meta(UserCreateSerializer.Meta):
        model = mod.User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'password'
        )

    def validate_username(self, username):
        valid.username_regex_validator(username)
        return username


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format_img, imgstr = data.split(';base64,')
            ext = format_img.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CatSerializer(ModelSerializer):

    image = Base64ImageField(required=True)
    image_url = serializers.SerializerMethodField(
        'get_image_url',
        read_only=True,
    )

    class Meta:
        model = mod.User
        fields = ('avatar',)
 
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None




    # def create(self, validated_data):
    #     passw = validated_data.pop('password')
    #     user = mod.User(**validated_data)
    #     # Шифруем пароль перед сохранением
    #     user.set_password(passw)
    #     user.save()
    #     return user
