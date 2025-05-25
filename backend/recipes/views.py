from django.core.exceptions import ValidationError
from django.shortcuts import redirect

from .constants import RECIPE_NOT_FOUND
from .models import Recipe


def get_short_link_recipe(request, recipe_id):
    """Выводит страницу по короткой ссылке."""
    if not Recipe.objects.filter(pk=recipe_id).exists():
        raise ValidationError(RECIPE_NOT_FOUND.format(recipe_id))
    return redirect(f'/recipes/{recipe_id}/')
