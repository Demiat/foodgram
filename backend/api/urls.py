from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import (
    UserViewSet,
    EmailObtainAuthToken,
)

api_v1_router = DefaultRouter()
api_v1_router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(api_v1_router.urls)),
    path('auth/token/login/', EmailObtainAuthToken.as_view(), name='token'),
]
