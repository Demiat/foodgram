from collections import Counter

from djoser.serializers import UserSerializer as UserSerializerDjoser
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import MIN_AMOUNT, MIN_COOKING_TIME
from recipes.models import (
    Favorite, Follow, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
    User
)

REPETITIVE_ERROR = 'Повторения в запросе! Объекты: {}'
EMPTY_INGREDIENTS = 'Пустой список продуктов недопустим'
NOT_IMAGE = 'Изображение обязательно!'
EMPTY_TAGS = 'Пустой список тэгов недопустим'
INGREDIENTS_VALIDATE = {
    'error': 'Поле ingredients отсутствует или не прошло валидацию'
}
TAGS_VALIDATE = {
    'error': 'Поле tags отсутствует или не прошло валидацию'
}


class UserSerializer(UserSerializerDjoser):
    """Обрабатывает модель пользователей."""

    avatar = serializers.ImageField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializerDjoser.Meta):
        model = User
        fields = ['avatar', 'is_subscribed', *UserSerializerDjoser.Meta.fields]

    def get_is_subscribed(self, author):
        return (
            not self.context['request'].user.is_anonymous
            and Follow.objects.filter(
                from_user=self.context['request'].user,
                author=author).exists()
        )


class AvatarSetSerializer(serializers.ModelSerializer):
    """Сериализирует картинку."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Тэги."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Продукты."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    """Рецепты с продуктами и мерой."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """Читаемый сериализатор для вывода рецептов с продуктами и мерой."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipesReadSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True, source='recipeingredients'
    )
    author = UserSerializer(read_only=True)
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
        read_only_fields = fields

    def _favorite_shopping_methods(self, recipe, model):
        return (
            not self.context['request'].user.is_anonymous
            and model.objects.filter(
                recipe=recipe,
                user=self.context['request'].user
            ).exists()
        )

    def get_is_favorited(self, recipe):
        return self._favorite_shopping_methods(recipe, model=Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self._favorite_shopping_methods(
            recipe, model=ShoppingCart)


class RecipesWriteSerializer(serializers.ModelSerializer):

    image = Base64ImageField()
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'ingredients',
            'name',
            'text',
            'cooking_time',
            'image',
        )

    def _repetitive_validate(self, items):
        duplicates = [
            item for item, count in Counter(items).items() if count > 1
        ]
        if duplicates:
            raise serializers.ValidationError(
                REPETITIVE_ERROR.format(duplicates)
            )

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError(NOT_IMAGE)
        return image

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(EMPTY_TAGS)
        self._repetitive_validate(tags)
        return tags

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(EMPTY_INGREDIENTS)
        self._repetitive_validate([item['ingredient'] for item in ingredients])
        return ingredients

    def validate(self, attrs):
        if 'ingredients' not in attrs:
            raise serializers.ValidationError(INGREDIENTS_VALIDATE)
        if 'tags' not in attrs:
            raise serializers.ValidationError(TAGS_VALIDATE)
        return super().validate(attrs)

    def _set_recipe_ingredient(self, recipe, ingredients):
        """Заполним связанную таблицу RecipeIngredient."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                **ingredient_data
            ) for ingredient_data in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self._set_recipe_ingredient(recipe=recipe, ingredients=ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance.recipeingredients.all().delete()
        self._set_recipe_ingredient(
            recipe=instance, ingredients=ingredients
        )
        return super().update(instance, validated_data)

    def to_representation(self, recipe):
        return RecipesReadSerializer(recipe, context=self.context).data


class ShortRecipesReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class RecipesOfUserSerializer(UserSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta(UserSerializer.Meta):
        model = User
        fields = [
            'recipes',
            'recipes_count', *UserSerializer.Meta.fields
        ]

    def get_recipes(self, authors):
        return ShortRecipesReadSerializer(
            authors.recipes.all()[
                :int(self.context['request'].GET.get('recipes_limit', 10**10))
            ],
            many=True
        ).data
