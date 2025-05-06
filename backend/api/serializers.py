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

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def to_representation(self, instance):
        ingredient_serialized = IngredientSerializer(instance.ingredient).data
        # Добавляем количество на один уровень с полями ингредиента
        representation = {**ingredient_serialized, 'amount': instance.amount}
        return representation


class RecipesReadSerializer(serializers.ModelSerializer):

    image = Base64ImageField(required=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipeingredient_set'
    )
    author = UserSerializerDjoser(read_only=True)

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
        read_only_fields = fields


class RecipesWriteSerializer(serializers.ModelSerializer):

    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'text',
            'cooking_time',
            'image',
        )
        extra_kwargs = {
            'is_favorited': {'read_only': True},
            'is_in_shopping_cart': {'read_only': True},
            'cooking_time': {'min_value': 1, 'max_value': 240},
            'text': {'trim_whitespace': True},
        }

    def validate_tags(self, value):
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        # tags = validated_data.pop('tags')
        # recipe = Recipe.objects.create(**validated_data)
        recipe = super().create(validated_data)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                ingredient=ingredient['ingredient'],
                recipe=recipe,
                amount=ingredient['amount']
            )
        # recipe.tags.set(tags)
        return recipe

    def to_representation(self, recipe):
        super().to_representation(self)
        return RecipesReadSerializer(recipe, context=self.context).data
