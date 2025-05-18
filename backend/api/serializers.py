import base64

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import MIN_AMOUNT, MIN_COOKING_TIME
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag, User)

from .constants import (AMOUNT_INGREDIENTS, EMTY_INGREDIENTS, EMTY_TAGS,
                        INGREDIENTS_VALIDATE, IS_FAVORITED_PARAM_NAME,
                        IS_SHOPPING_CART_PARAM_NAME, REPETITIVE_INGREDIENTS,
                        REPETITIVE_TAGS, TAGS_VALIDATE)


class UserSerializerDjoser(UserSerializer):
    """Обрабатывает модель пользователей."""

    avatar = serializers.ImageField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ('avatar', 'is_subscribed')

    def get_is_subscribed(self, author):
        return (
            not self.context['request'].user.is_anonymous
            and self.context['request'].user.followings.filter(
                to_user=author).exists()
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
    amount = serializers.ReadOnlyField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipesReadSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True, source='recipeingredients'
    )
    author = UserSerializerDjoser(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

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
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return model.objects.filter(recipe=recipe, user=user).exists()

    def get_is_favorited(self, recipe):
        return self._favorite_shopping_methods(recipe, model=Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self._favorite_shopping_methods(
            recipe, model=ShoppingCart)


class RecipesWriteSerializer(serializers.ModelSerializer):

    image = Base64ImageField(required=True)
    ingredients = IngredientInRecipeCreateSerializer(many=True, required=True)

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
        instance.recipeingredients.all().delete()
        self._set_recipe_ingredient(
            recipe=instance, ingredients=ingredients
        )
        updated_recipe = super().update(instance, validated_data)
        return updated_recipe

    def to_representation(self, recipe):
        return RecipesReadSerializer(recipe, context=self.context).data


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
        try:
            recipes_limit = int(
                self.context['request'].GET.get('recipes_limit')
            )
        except (ValueError, TypeError):
            recipes_limit = None
        return LimitedRecipesReadSerializer(
            authors.recipes.all()[:recipes_limit], many=True).data

    def get_is_subscribed(self, author):
        if isinstance(author, User):
            return self.context['request'].user.followings.filter(
                to_user=author).exists()

    def get_recipes_count(self, author):
        return author.recipes.count()
