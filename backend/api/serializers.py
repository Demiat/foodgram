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
    Favorite,
    ShoppingCart,
)
from users.validators import username_regex_validator
from .constants import (
    REPETITIVE_INGREDIENTS,
    REPETITIVE_TAGS,
    EMTY_INGREDIENTS,
    AMOUNT_INGREDIENTS,
    EMTY_TAGS,
    IS_FAVORITED_PARAM_NAME,
    IS_SHOPPING_CART_PARAM_NAME,
    INGREDIENTS_VALIDATE,
    TAGS_VALIDATE
)


class UserSerializerDjoser(UserSerializer):
    """Обрабатывает модель пользователей."""

    avatar = serializers.ImageField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

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

    def get_is_subscribed(self, author):
        follower = self.context['request'].user
        if follower.is_anonymous:
            return False
        return follower.check_subscription(author)


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

    image = Base64ImageField()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipeingredient_set'
    )
    author = UserSerializerDjoser(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def _general_method(self, recipe, param_name):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        if param_name == IS_SHOPPING_CART_PARAM_NAME:
            manager = ShoppingCart.objects
        elif param_name == IS_FAVORITED_PARAM_NAME:
            manager = Favorite.objects
        return manager.filter(recipe=recipe, user=user).exists()

    def get_is_favorited(self, recipe):
        return self._general_method(recipe, param_name=IS_FAVORITED_PARAM_NAME)

    def get_is_in_shopping_cart(self, recipe):
        return self._general_method(
            recipe, param_name=IS_SHOPPING_CART_PARAM_NAME)


class RecipesWriteSerializer(serializers.ModelSerializer):

    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientSerializer(many=True, required=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'name',
            'text',
            'cooking_time',
            'image',
        )
        extra_kwargs = {
            'cooking_time': {'min_value': 1, 'max_value': 240},
            'text': {'trim_whitespace': True},
        }

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(EMTY_TAGS)
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(REPETITIVE_TAGS)
        return tags

    def validate_ingredients(self, ingredients):
        ing = []
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(AMOUNT_INGREDIENTS)
            ing.append(ingredient['ingredient'])
        if len(ing) != len(set(ing)):
            raise serializers.ValidationError(REPETITIVE_INGREDIENTS)
        if not ing:
            raise serializers.ValidationError(EMTY_INGREDIENTS)
        return ingredients

    def _set_recipe_ingredient(self, recipe, ingredients):
        """Заполним связанную таблицу RecipeIngredient."""
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                ingredient=ingredient['ingredient'],
                recipe=recipe,
                amount=ingredient['amount']
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self._set_recipe_ingredient(recipe=recipe, ingredients=ingredients)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' not in validated_data:
            raise serializers.ValidationError(INGREDIENTS_VALIDATE)
        if 'tags' not in validated_data:
            raise serializers.ValidationError(TAGS_VALIDATE)
        ingredients = validated_data.pop('ingredients')
        instance.recipeingredient_set.all().delete()
        self._set_recipe_ingredient(
            recipe=instance, ingredients=ingredients
        )
        updated_recipe = super().update(instance, validated_data)
        return updated_recipe

    def to_representation(self, recipe):
        return RecipesReadSerializer(recipe, context=self.context).data


class ShortLinkSerializer(serializers.ModelSerializer):
    """Выводит короткую уникальную ссылку для рецепта."""

    def to_representation(self, instance):
        request = self.context['request']
        base_url = request.build_absolute_uri('/')
        full_short_link = f'{base_url}s/{instance.short_code}'
        return {'short-link': full_short_link}

    class Meta:
        model = Recipe
        fields = ('short_code',)


class LimitedRecipesReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_recipes(self, authors):
        limit = self.context['recipes_limit']
        return LimitedRecipesReadSerializer(
            authors.recipes.all()[:limit], many=True).data

    def get_is_subscribed(self, author):
        follower = self.context['request'].user
        return follower.check_subscription(author)

    def get_recipes_count(self, author):
        return author.recipes.count()
