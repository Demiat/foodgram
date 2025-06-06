![Foodgram Action](https://github.com/Demiat/foodgram/actions/workflows/main.yml/badge.svg?event=push)

# О Проекте

Foodgram (https://100yp.ddns.net) - это проект, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». 

## Доступный функционал

Зарегистрированные пользователи могут:
- добавлять рецепты
- подписываться на других авторов рецептов
- добавлять рецепты в избранное
- добавлять рецепты в список покупок и скачивать файл

# Стек и развёртывание проекта на продакш-сервере

Внимание! Проект работает с версией Python 3.9+

Для работы проекта необходимо, чтобы на Вашем сервере был установлен
docker (https://docs.docker.com/engine/install/ubuntu/)
и корневой веб-сервер для проксирования потока в проект.

Проект представляет из себя 4 контейнера docker, логически
связанных между собой сетью докера (compose) и проксированием между ними nginx:
- backend: django приложение бэкенда
- frontend: SPA-приложение на React
- db: база данных Postgres
- gateway: nginx веб-сервер


## Развёртывание проекта

## Локально

1) Склонировать репозиторий:
```
git clone git@github.com:Demiat/foodgram.git
```

2) Создать виртуальное окружение: 
```
cd backend/
python -m venv venv
```

3) Активировать виртуальное окружение:
- для linux ```source venv/bin/activate```
- для windows ```source venv/Scripts/activate```

4) Установить зависимости: ```pip install -r requirements.txt```

5) Есть возможность заполнить базу данными, используя команды:
- Для загрузки продуктов:
```
python manage.py load_products data/ingredients.json
```
- Для загрузки тегов:
```
python manage.py load_tags data/tags.json
```

6) Создать файл с переменными окружения .env со следующими полями:
```
USE_POSTGRES=True
```
где: 
- True - использование POSTGRES
- False - использование SQLite

- Заполняется для использования Postgres
```
POSTGRES_DB=<имя базы>
POSTGRES_USER=<пользователь postgres>
POSTGRES_PASSWORD=<пароль пользователя postgres>
DB_HOST=<имя хоста базы>
DB_PORT=<порт базы>
DB_NAME=<имя базы>
```
- Остальные настройки для settings.py Django-приложения
```
SECRET_KEY=<секретный ключ django-приложения, взять из settings.py>
ALLOWED_HOSTS=<список разрешенных хостов, без пробелов через запятую>
DEBUG=<False или True> 
```

## На удаленном сервере:

7) Скопировать файл docker-compose.production.yml
в целевую директорию на Вашем удаленном сервере

### Ручной запуск

- sudo docker compose -f docker-compose.production.yml pull
- sudo docker compose -f docker-compose.production.yml up -d

### Автоматизированный запуск

- При команде git push в ветку main проект тестируется 
и разворачивается автоматически.
- При git push в иную ветку производится только тестирование.

## Дополнительная информация

Управление проектом доступно по REST API.
Документация к API доступна по адресам:
- [Документация API swagger](https://dvp.zapto.org/swagger/)
- [Документация API redoc](https://dvp.zapto.org/redoc/)

Доступ к админ-панели осуществляется через следующий URL:
Администраторам: [Администраторская панель](https://dvp.zapto.org/admin/)

Сервер доступен по адресу:
Основной сервер: [Сервер приложения](https://dvp.zapto.org/)


Автор: [Тарасов Дмитрий](https://github.com/Demiat)