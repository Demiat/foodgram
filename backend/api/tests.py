from http import HTTPStatus

from django.test import TestCase
from rest_framework.test import APIClient

from recipes.models import User


class FoodgramAPITestCase(TestCase):
    """Минимальные тесты для проекта."""

    def setUp(self):
        self.user = User.objects.create_user(username='auth_user')
        self.client = APIClient()
        # Что бы не генерировать токены, устанавливать заголовки - force auth
        self.client.force_authenticate(user=self.user)

    def test_recipes_list(self):
        """Проверяет эндпоинт списка рецептов."""
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
