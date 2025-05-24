from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientsViewSet, RecipesViewSet, TagsViewSet, UserViewSet

app_name = 'api'

api_router = DefaultRouter()
api_router.register('users', UserViewSet, basename='users')
api_router.register('recipes', RecipesViewSet, basename='recipes')
api_router.register('tags', TagsViewSet, basename='tags')
api_router.register(
    'ingredients', IngredientsViewSet, basename='ingredients')

urlpatterns = [
    path('', include(api_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
