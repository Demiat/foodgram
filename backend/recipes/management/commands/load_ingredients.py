import csv
import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    help = 'Загружает продукты из CSV или JSON файла в модель Ingredient'

    def add_arguments(self, parser):
        """Добавляет аргументы для команды."""
        parser.add_argument(
            'path_to_file',
            type=str,
            help='Путь к файлу (CSV или JSON)'
        )
        parser.add_argument(
            '--f',
            choices=['csv', 'json'],
            required=True,
            help='Формат файла: csv или json'
        )

    def handle(self, *args, **options):
        """Загружает продукты из CSV-файла."""

        path_to_file = options['path_to_file']
        format_type = options['f']

        try:
            with open(path_to_file, mode='r', encoding='utf-8') as file:
                if format_type == 'csv':
                    raw_data = csv.reader(file)
                    # row[0] название продукта
                    # row[1] единица измерения
                    products_list = [
                        Ingredient(name=row[0], measurement_unit=row[1])
                        for row in raw_data
                        if row[0].strip() and row[1].strip()
                    ]
                else:
                    raw_data = json.load(file)
                    products_list = [
                        Ingredient(name=item['name'],
                                   measurement_unit=item['measurement_unit']
                                   ) for item in raw_data
                    ]

                Ingredient.objects.bulk_create(products_list)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ошибка: {e}'))
        else:
            self.stdout.write(
                self.style.SUCCESS('Продукты загружены!')
            )
