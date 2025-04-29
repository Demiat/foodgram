from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import (
    UserViewSet,
)

api_v1_router = DefaultRouter()
api_v1_router.register('users', UserViewSet, basename='users')

# auth_urls = [
#     path('auth/signup/', user_signup, name='signup'),
#     path('auth/token/', issue_token, name='token'),
# ]

urlpatterns = [
    path('', include(api_v1_router.urls)),
    # path('v1/', include(auth_urls)),
]
