import json
import os


class LoadDataBase:

    help = 'Загружает данные из JSON файла'

    def add_arguments(self, parser):
        """Добавляет аргументы для команды."""
        parser.add_argument(
            'path_to_file',
            type=str,
            help='Путь к файлу JSON'
        )

    def handle(self, *args, **options):
        """Загружает продукты из JSON-файла."""

        path_to_file = options['path_to_file']

        try:
            with open(path_to_file, mode='r', encoding='utf-8') as file:
                items = self.model_class.objects.bulk_create(
                    [self.model_class(**item) for item in json.load(file)],
                    ignore_conflicts=True
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Загружено объектов: {len(items)}')
                )
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f'Ошибка: {e} для файла {os.path.basename(path_to_file)}'
            ))
