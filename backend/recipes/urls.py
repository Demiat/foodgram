from django.urls import path

from .views import get_short_link_recipe

urlpatterns = [
    path(
        '<int:recipe_id>/',
        get_short_link_recipe,
        name='recipe_short_link'
    ),
]
