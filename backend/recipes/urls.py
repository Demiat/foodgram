from django.conf import settings
from django.urls import path

from .views import get_short_link_recipe

urlpatterns = [
    path(
        f'{settings.SHORT_URL_PREFIX}<int:recipe_id>/',
        get_short_link_recipe,
        name='recipe_short_link'
    ),
]
