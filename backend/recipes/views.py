from django.shortcuts import redirect
from django.http import Http404

from .models import Recipe
from .constants import RECIPE_NOT_FOUND


def get_short_link_recipe(request, recipe_id):
    """Выводит страницу по короткой ссылке."""
    if Recipe.objects.filter(pk=recipe_id).exists():
        return redirect(f'/api/recipes/{recipe_id}/')
    raise Http404(RECIPE_NOT_FOUND)
