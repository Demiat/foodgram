from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    RecipesViewSet,
    IngredientsViewSet,
    TagsViewSet,
    UserViewSet,
    # RecipeDetailView
)

api_v1_router = DefaultRouter()
api_v1_router.register('users', UserViewSet, basename='users')
api_v1_router.register('recipes', RecipesViewSet, basename='recipes')
api_v1_router.register('tags', TagsViewSet, basename='tags')
api_v1_router.register(
    'ingredients', IngredientsViewSet, basename='ingredients')


urlpatterns = [
    # path(
    #     's/<uuid:short_code>/',
    #     RecipeDetailView.as_view(),
    #     name='recipe_short_link'
    # ),
    path('', include(api_v1_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
