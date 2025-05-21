from django.core.management.base import BaseCommand

from recipes.models import Ingredient
from ._base_load import LoadDataBase


class Command(LoadDataBase, BaseCommand):
    """
    Предоставляет модель продуктов родительскому классу
    для загрузки продуктов в базу данных.
    """

    help = 'Комманда для импорта продуктов из JSON'
    model_class = Ingredient
