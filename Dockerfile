FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md alembic.ini ./
COPY app ./app
COPY alembic ./alembic
COPY scripts ./scripts

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir . \
    && chmod +x ./scripts/entrypoint.sh

EXPOSE 8000

CMD ["./scripts/entrypoint.sh"]
