import base64

from djoser.serializers import UserCreateSerializer, UserSerializer
from django.core.files.base import ContentFile
from rest_framework import serializers

from users.models import User
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
)
from users.validators import username_regex_validator


class UserSerializerDjoser(UserSerializer):
    """Обрабатывает модель пользователей."""

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
    """Обрабатывает создание модели пользователей."""

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
    """Переводит base64 данные во внутреннее представление Джанго."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format_img, imgstr = data.split(';base64,')
            ext = format_img.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='image.' + ext)
        return super().to_internal_value(data)


class AvatarSetSerializer(serializers.ModelSerializer):
    """Сериализирует картинку."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        """
        Предотвращает размножение картинок
        при множественных запросах POST.
        """
        if instance.avatar and instance.avatar.name:
            instance.avatar.delete(save=False)
        instance.avatar = validated_data['avatar']
        instance.save()
        return instance


class TagSerializer(serializers.ModelSerializer):
    """Тэги."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Ингредиенты."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Рецепты с ингредиентами и кол-вом."""

    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')


class RecipesSerializer(serializers.ModelSerializer):

    image = Base64ImageField(required=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipes_ingredients', read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'author',
            'name',
            'text',
            'cooking_time',
            'image',
        )
        extra_kwargs = {
            'author': {'read_only': True},
            'is_favorited': {'read_only': True},
            'is_in_shopping_cart': {'read_only': True},
            'cooking_time': {'min_value': 1, 'max_value': 240},
            'text': {'trim_whitespace': True},
        }

    def create(self, validated_data):
        # ingredients = validated_data.pop('ingredients')
        ingredients = self.initial_data.get('ingredients', [])
        # tags = validated_data.pop('tags')
        tags = self.initial_data.get('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(
                pk=ingredient['id']
            )
            RecipeIngredient.objects.create(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=ingredient['amount']
            )
        # recipe.ingredients.set(ingredients)
        recipe.tags.set(tags)
        return recipe
