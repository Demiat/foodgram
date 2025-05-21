from django.shortcuts import redirect
from django.core.exceptions import ValidationError

from .models import Recipe

RECIPE_NOT_FOUND = 'Рецепта c id {} нет в базе!'


def get_short_link_recipe(request, recipe_id):
    """Выводит страницу по короткой ссылке."""
    if not Recipe.objects.filter(pk=recipe_id).exists():
        raise ValidationError(RECIPE_NOT_FOUND.format(recipe_id))
    return redirect('recipes-detail', pk=recipe_id)
