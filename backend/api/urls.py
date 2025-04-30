from django.urls import include, path
from rest_framework.routers import DefaultRouter
from djoser.views import TokenCreateView, TokenDestroyView

# from users.views import (
#     UserViewSet,
#     EmailObtainAuthToken,
# )

# api_v1_router = DefaultRouter()
# api_v1_router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include('djoser.urls')),
    path('auth/token/login/', TokenCreateView.as_view(), name='login'),
    path('auth/token/logout/', TokenDestroyView.as_view(), name='logout'),
    # path('', include(api_v1_router.urls)),
    # path('auth/token/login/', EmailObtainAuthToken.as_view(), name='token'),
]
