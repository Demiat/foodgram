from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet
from recipes.views import (
    RecipesViewSet,
)

api_router = DefaultRouter()
api_router.register('users', UserViewSet, basename='users')
api_router.register('recipes', RecipesViewSet, basename='recipes')


urlpatterns = [
    path('', include(api_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
