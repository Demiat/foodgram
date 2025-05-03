import csv
import os
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    help = 'Загружает ингредиенты из CSV файла в модель Ingredient'

    def handle(self, *args, **options):
        create_count = 0
        update_count = 0
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
        FILE_PATH = os.path.join(BASE_DIR, 'data', 'ingredients.csv')
        with open(FILE_PATH, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)

            for row in reader:
                # Разделяем каждый ряд на ингредиенты и единицы измерения
                name = row[0].strip()   # Название ингредиента
                unit = row[1].strip()   # Единица измерения

                # Проверка наличия данных перед добавлением
                if not name or not unit:
                    continue

                ingredient, created = Ingredient.objects.update_or_create(
                    name=name,
                    defaults={'measurement_unit': unit}
                )
                if created:
                    create_count += 1
                else:
                    update_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Создано: {create_count} ингредиентов, '
                f'обновлено: {update_count}'
            )
        )
