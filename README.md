# Foodgram
Cервис для публикаций и обмена рецептами.

Авторизованные пользователи могут подписываться на понравившихся авторов, добавлять рецепты в избранное, в покупки, скачивать список покупок. Неавторизованным пользователям доступна регистрация, авторизация, просмотр рецептов других пользователей.

![Foodgram Workflow](https://github.com/DominusMortem/foodgram-project-react/actions/workflows/foodgram_workflow.yaml/badge.svg)

## Стек технологий
Python 3.10.0, Django 3.2.15, Django REST Framework 3.13.1, PostgeSQL, Docker, Yandex.Cloud

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

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/DominusMortem/foodgram-project-react
```
Запушить к себе в репозиторий:

```
git add .
git commit -m 'текст комментария'
git push
```
Во вкладке Settings -> Secrets -> Action
Добавить переменные окружения.

Подключится к серверу по SSH
```
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --no-input
```
Для наполнения базы данных разместите файл fixtures.json в папке foodgram-project-react\backend:
```
docker-compose exec web python manage.py loaddata fixtures.json
```

## Сайт
Сайт доступен по ссылке:
[http://84.252.142.183/](http://84.252.142.183/)

## Документация к API
Документация доступна на сервере:
[http://84.252.142.183/api/docs/](http://84.252.142.183/api/docs/)

## Доступ к админке

[http://84.252.142.183/admin/](http://84.252.142.183/admin/)
почта: test@test.test
пароль: admin12345

