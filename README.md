# Test Python Backend

Асинхронное REST API на Sanic, SQLAlchemy async и PostgreSQL.

## Данные по умолчанию

Пользователь:

- email: `user@example.com`
- password: `user12345`

Администратор:

- email: `admin@example.com`
- password: `admin12345`

Секрет для подписи платежного вебхука по умолчанию: `gfdmhghif38yrf9ew0jkf32`.

## Запуск через Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

API будет доступно на `http://localhost:8000`.

## Запуск без Docker

Нужен PostgreSQL и Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Создайте базу данных:

```bash
createdb test_python
```

Примените миграции и запустите приложение:

```bash
alembic upgrade head
sanic app.main:create_app --factory --host=0.0.0.0 --port=8000
```

## Основные эндпоинты

- `POST /auth/login` - авторизация пользователя или администратора.
- `GET /users/me` - данные текущего пользователя.
- `GET /users/me/accounts` - счета текущего пользователя.
- `GET /users/me/payments` - платежи текущего пользователя.
- `POST /admin/users` - создать пользователя, только администратор.
- `GET /admin/users` - список пользователей со счетами, только администратор.
- `GET /admin/users/{id}` - пользователь со счетами, только администратор.
- `PATCH /admin/users/{id}` - обновить пользователя, только администратор.
- `DELETE /admin/users/{id}` - удалить пользователя, только администратор.
- `POST /payments/webhook` - обработка платежного вебхука.

Для защищенных роутов передайте JWT:

```bash
Authorization: Bearer <access_token>
```

## Примеры запросов

Авторизация:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"user12345"}'
```

Вебхук платежа:

```bash
curl -X POST http://localhost:8000/payments/webhook \
  -H 'Content-Type: application/json' \
  -d '{
    "transaction_id": "5eae174f-7cd0-472c-bd36-35660f00132b",
    "user_id": 1,
    "account_id": 1,
    "amount": 100,
    "signature": "7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8"
  }'
```
