import json

from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):

    help = 'Загружает Тэги из JSON файла в модель Tag'

    def add_arguments(self, parser):
        """Добавляет аргументы для команды."""
        parser.add_argument(
            'path_to_file',
            type=str,
            help='Путь к файлу JSON'
        )

    def handle(self, *args, **options):
        """Загружает Тэги из из JSON-файла."""

        path_to_file = options['path_to_file']

        try:
            with open(path_to_file, mode='r', encoding='utf-8') as file:
                raw_data = json.load(file)
                tags_list = [
                    Tag(name=item['name'],
                        slug=item['slug']
                        ) for item in raw_data
                ]

                Tag.objects.bulk_create(tags_list)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ошибка: {e}'))
        else:
            self.stdout.write(self.style.SUCCESS('Тэги загружены!'))
