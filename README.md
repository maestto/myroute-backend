# MyRoute Backend

Backend-часть проекта MyRoute на `FastAPI`.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

## Команды

- `ruff check app tests` — линтер
- `pytest` — тесты
- `uvicorn app.main:app --reload` — локальный запуск

## Git Strategy

- `dev` — активная разработка и ежедневные коммиты.
- `main` — стабильная версия, обновляется после завершения спринта.
