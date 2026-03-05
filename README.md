# MyRoute Backend

Backend-часть проекта MyRoute на `FastAPI`.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
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
- `GET /api/v1/trips/{trip_id}/members` (Bearer token, список участников поездки)
- `POST /api/v1/trips/{trip_id}/invites` (Bearer token, owner-only, создание инвайта)
- `POST /api/v1/invites/{token}/accept` (Bearer token, принятие инвайта)
- `GET /api/v1/trips/{trip_id}/stops` (Bearer token, список остановок маршрута)
- `POST /api/v1/trips/{trip_id}/stops` (Bearer token, editor/owner, добавление остановки)
- `PATCH /api/v1/trips/{trip_id}/stops/{stop_id}` (Bearer token, editor/owner, редактирование остановки)
- `DELETE /api/v1/trips/{trip_id}/stops/{stop_id}` (Bearer token, editor/owner, удаление остановки)

## Environment notes

- `FRONTEND_BASE_URL` — базовый URL frontend для генерации `invite_url`.
- `CORS_ORIGINS` — CSV список origin для frontend (`http://localhost:5173` по умолчанию).

## Git Strategy

- `dev` — активная разработка и ежедневные коммиты.
- `main` — стабильная версия, обновляется после завершения спринта.
