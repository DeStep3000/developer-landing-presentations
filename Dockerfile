# syntax=docker/dockerfile:1.6

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_CACHE_DIR=/app/.uv-cache \
    HOME=/app \
    PYTHONPATH=/app/app

WORKDIR /app

RUN pip install --no-cache-dir -U pip uv \
    && groupadd -r app \
    && useradd -r -g app app

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

COPY --chown=app:app . .
RUN mkdir -p /app/logs && chown -R app:app /app

USER app
EXPOSE 8000

CMD ["uv", "run", "--no-sync", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
