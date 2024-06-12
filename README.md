# Foodgram

Foodgram - сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

#### Для локаьного запуска необходимо следующее:
- установленный docker
- ```.env``` файл следующего формата:
```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
SECRET_KEY="секретный ключ для джанго"
DJANGO_SERVER_STATUS_DEBUG="" или "DEBUG_MODE", чтобы включить режим дебага
ALLOWED_HOSTS="127.0.0.1 localhost"
DJANGO_DATABASE_DEVELOP="" или "DEVELOP_MODE", чтобы работать с тестовой БД sqlite3
```

####  Сервис запускается с помощью ```docker compose up```

Деплой в продакшен осуществляется автоматически при пуше в main ветку.

Подробную документацию можно посмотреть на /api/docs/ при локальном развертывании.

#### В сервисе доступны следующие взаимодействия:
- эндпоинты юзеров
    - users/ GET & POST юзеров
    - users/{id}/ GET юзера
    - users/me/ GET текущего юзера по токену
    - users/me/avatar/ GET, DELETE аватара текущего юзера по токену
    - users/set_password/ POST изменения пароля текущего юзера по токену
    - auth/token/login/ POST получение токена
    - auth/token/logout/ POST получение токена
- эндпоинты тэгов
    - tags/ GET тэгов
    - tags/{id}/ GET тэга
- эндпоинты ингредиентов
    - tags/ GET ингредиентов
    - tags/{id}/ GET ингредиента
- эндпоинты рецептов
    - recipes/ GET, POST рецепта
    - recipes/{id}/ GET, PATCH, DELETE рецепта
    - recipes/{id}/get-link/ GET короткой ссылки на рецепт
- эндпоинты списка покупок
    - recipes/download_shopping_cart/ GET для скачивания списка покупок
    - recipes/{id}/shopping_cart/ POST, DELETE рецепта в список покупок
- эндпоинты избранного
    - recipes/{id}/favorite/ POST, DELETE рецепта в избранное
- эндпоинты подписок
    - users/subscriptions/ GET подписок текущего юзера по токену
    - users/{id}/subscribe/ POST, DELETE подписки текущего юзера на другого юзера по токену


Используемые библиотеки:
- Django==3.2.3
- djangorestframework==3.12.4
- djoser==2.1.0
- Pillow==9.0.0
- djoser==2.1.0
- pyshorteners==1.0.1
- django-filter==23.1
- gunicorn==20.1.0
- psycopg2-binary==2.9.3
- django-cors-headers==3.13.0
- python_dotenv==1.0.1
- flake8==6.0.0

Версия Python:
Python 3.9.18

Автор:

> tizzhh  https://github.com/tizzhh

> darovadraste@gmail.com

> tizzhh.github.io