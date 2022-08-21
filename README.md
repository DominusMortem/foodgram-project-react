# Foodgram
Cервис для публикаций и обмена рецептами.

Авторизованные пользователи могут подписываться на понравившихся авторов, добавлять рецепты в избранное, в покупки, скачивать список покупок. Неавторизованным пользователям доступна регистрация, авторизация, просмотр рецептов других пользователей.

## Стек технологий
Python 3.10.0, Django 3.2.15, Django REST Framework 3.13.1

## Установка
Для запуска локально, создайте файл `.env` в директории `/backend/` с содержанием:
```
SECRET_KEY=любой_секретный_ключ_на_ваш_выбор
DEBUG=False
DB_ENGINE=django.db.backends.postgresql
DB_NAME=имя_вашей_базы_данных
POSTGRES_USER=имя_пользователя
POSTGRES_PASSWORD=пароль
DB_HOST=127.0.0.1
DB_PORT=5432 
```

## Запуск
Запустить командную строку в директории `infra` ввести команду `docker-compose up`.
После успешного запуска выполняем команды:
```
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --no-input
```
Cайт доступен по адресу `localhost/`
