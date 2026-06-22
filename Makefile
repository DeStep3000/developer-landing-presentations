.PHONY: dev test lint migrate run

dev:
	docker-compose up --build -d

test:
	uv run pytest

lint:
	./ruff

migrate:
	uv run python app/manage.py migrate

run:
	uv run python app/manage.py runserver 0.0.0.0:8000
