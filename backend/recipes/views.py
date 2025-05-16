from django.shortcuts import redirect

from .models import Recipe

def get_short_link_recipe(request, recipe_id):
    """Выводит страницу по короткой ссылке."""
    if Recipe.objects.filter(pk=recipe_id).exists():
        return redirect(f'/api/recipes/{recipe_id}/')
