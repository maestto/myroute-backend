# MyRoute Backend

Backend-часть проекта MyRoute на `FastAPI`.

## Быстрый старт (Docker)

Требуется только Docker.

```bash
docker compose up --build
```

Поднимает PostgreSQL, применяет миграции, заливает демо-данные и запускает API на `http://localhost:8000`. Этого достаточно, если склонирован один этот репозиторий.

Весь стенд вместе с клиентом — одной командой, если репозиторий `myroute-frontend` лежит рядом:

```bash
docker compose --profile full up --build
```

Добавляет клиент на `http://localhost:5173`. Клиент стартует только после того, как API ответит на `/health`. Путь к репозиторию фронтенда меняется переменной `FRONTEND_DIR`.

Клиент можно поднять и из его собственного репозитория (`cd ../myroute-frontend && docker compose up --build`) — тогда бэкенд и фронтенд разворачиваются независимо.

Демо-аккаунты (пароль у всех `demo-pass-123`):

- `demo@myroute.dev` — владелец поездки «Неделя в Сочи», редактор «Казань — Нижний Новгород»
- `ivan@myroute.dev` — владелец «Казань — Нижний Новгород»
- `olga@myroute.dev`, `anna@myroute.dev` — участники с ролями viewer
- Открытый инвайт-токен для «Сочи» (роль editor): `demo-invite-sochi`

Переменные (см. `.env.example`): `SEED_DEMO_DATA=0` отключает сиды, `BACKEND_PORT` и `FRONTEND_PORT` меняют публикуемые порты, `FRONTEND_DIR` — путь к репозиторию фронтенда.

Перед демо — чистый старт, чтобы в базе были только демо-данные:

```bash
docker compose down -v && docker compose --profile full up --build
```

Проверка: `curl localhost:8000/health` → `{"status":"ok"}`, Swagger — `http://localhost:8000/docs`.

## Локальный запуск без Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head            # нужен PostgreSQL, см. DATABASE_URL в app/core/config.py
python -m scripts.seed          # опционально, демо-данные
uvicorn app.main:app --reload
```

## Команды

- `ruff check app tests` — линтер
- `pytest` — тесты
- `alembic upgrade head` — применить миграции
- `uvicorn app.main:app --reload` — локальный запуск

## Минимальная структура

- `app/core/` — базовые настройки приложения
- `app/api/` — маршрутизация API
- `app/api/v1/endpoints/` — endpoint-модули версии API
- `app/domain/` — доменные правила
- `app/services/` — use-case слой
- `app/db/` — слой БД
- `app/realtime/` — real-time слой
- `app/integrations/` — внешние интеграции

## Health endpoints

- `GET /health`
- `GET /api/v1/health`

## Auth endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login` (OAuth2 form: `username`, `password`)
- `GET /api/v1/users/me` (Bearer token)

## Trips and Collaboration endpoints

- `GET /api/v1/trips` (Bearer token, список поездок пользователя)
- `POST /api/v1/trips` (Bearer token, создание поездки)
- `GET /api/v1/trips/{trip_id}` (Bearer token, overview поездки для участника)
- `PATCH /api/v1/trips/{trip_id}` (Bearer token, owner-only, частичное редактирование; даты не могут исключить существующие остановки и активности)
- `DELETE /api/v1/trips/{trip_id}` (Bearer token, owner-only, удаление поездки со всеми данными)
- `GET /api/v1/trips/{trip_id}/members` (Bearer token, список участников поездки)
- `POST /api/v1/trips/{trip_id}/members` (Bearer token, owner-only, добавление зарегистрированного пользователя по email)
- `POST /api/v1/trips/{trip_id}/invites` (Bearer token, owner-only, создание инвайта)
- `POST /api/v1/invites/{token}/accept` (Bearer token, принятие инвайта)
- `GET /api/v1/trips/{trip_id}/stops` (Bearer token, список остановок маршрута)
- `POST /api/v1/trips/{trip_id}/stops` (Bearer token, editor/owner, добавление остановки)
- `PATCH /api/v1/trips/{trip_id}/stops/{stop_id}` (Bearer token, editor/owner, редактирование остановки)
- `DELETE /api/v1/trips/{trip_id}/stops/{stop_id}` (Bearer token, editor/owner, удаление остановки)
- `GET /api/v1/trips/{trip_id}/activities` (Bearer token, активности поездки по дням)
- `POST /api/v1/trips/{trip_id}/activities` (Bearer token, editor/owner, добавление активности; дата — внутри дат поездки)
- `PATCH /api/v1/trips/{trip_id}/activities/{activity_id}` (Bearer token, editor/owner)
- `DELETE /api/v1/trips/{trip_id}/activities/{activity_id}` (Bearer token, editor/owner)

`budget_spent` в обзоре поездки — сумма стоимостей активностей.

## Environment notes

- `FRONTEND_BASE_URL` — базовый URL frontend для генерации `invite_url`.
- `CORS_ORIGINS` — CSV список origin для frontend (`http://localhost:5173` по умолчанию).

## Git Strategy

- `dev` — активная разработка и ежедневные коммиты.
- `main` — стабильная версия, обновляется после завершения спринта.
