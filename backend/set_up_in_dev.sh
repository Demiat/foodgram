python manage.py makemigrations
python manage.py migrate
python manage.py load_ingredients data/ingredients.csv
echo "from recipes.models import Tag; Tag.objects.bulk_create([ \
            Tag(name='Завтрак', slug='breakfast'), \
            Tag(name='Обед', slug='lunch'), \
            Tag(name='Полдник', slug='poldnik'), \
            Tag(name='Ужин', slug='dinner'), \
        ]);" | python manage.py shell
export DJANGO_SUPERUSER_EMAIL=admin@admin.ru
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=123
python manage.py createsuperuser --first_name Dima --last_name Tarasov --noinput
echo "Setup done."