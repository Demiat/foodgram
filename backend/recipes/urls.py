from django.conf import settings
from django.urls import include, path

from .views import get_short_link_recipe

urlpatterns = [
    path(
        '<int:recipe_id>/',
        get_short_link_recipe,
        name='recipe_short_link'
    ),
]
