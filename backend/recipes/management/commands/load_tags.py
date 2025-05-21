from django.core.management.base import BaseCommand

from recipes.models import Tag
from ._base_load import LoadDataBase


class Command(LoadDataBase, BaseCommand):
    """
    Предоставляет модель тегов родительскому классу
    для загрузки тегов в базу данных.
    """

    help = 'Комманда для импорта тегов из JSON'
    model_class = Tag
