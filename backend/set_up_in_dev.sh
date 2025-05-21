# ВНИМАНИЕ! Скрипт запускать только во время разработки приложения,
# для пересоздания базы данных, на свой страх и риск! (шутка)
# TODO: Добавить в .gitignore в продакш-версии кода

# Удаляем все файлы миграций
rm -f recipes/migrations/[!_]*.py
# Удаляем базу данных
rm -f db.sqlite3

# Создаем базу данных
python manage.py makemigrations
python manage.py migrate

# Загружаем продукты и тэги в базу
python manage.py load_products data/ingredients.json
python manage.py load_tags data/tags.json

# Создаем тестового суперюзера
export DJANGO_SUPERUSER_EMAIL=admin@admin.ru
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=123
python manage.py createsuperuser --first_name Dima --last_name Tarasov --noinput

echo "Setup complete!"