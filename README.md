# Developer Landing Presentations API

Backend-сервис для формы обратной связи на лендинг-презентации разработчика.

Сервис принимает обращение пользователя, валидирует входные данные, анализирует комментарий через AI, сохраняет обращение в PostgreSQL, отправляет email владельцу сайта и копию пользователю, пишет JSON-логи и предоставляет Swagger/OpenAPI документацию.

## Возможности

- `POST /api/contact` - отправка формы обратной связи.
- `GET /api/health` - проверка состояния сервиса.
- `GET /api/metrics` - простая статистика по обращениям.
- Swagger UI: `/api/docs`.
- OpenAPI schema: `/api/schema`.
- Rate limiting для защиты формы от спама.
- AI-анализ тональности и типа обращения.
- Graceful fallback, если OpenAI API недоступен или ключ не настроен.
- Логирование HTTP-запросов и ошибок в файлы.
- PostgreSQL в отдельном Docker-контейнере.

## Стек

- Python 3.12+
- Django 6
- Django REST Framework
- drf-spectacular
- PostgreSQL 16
- OpenAI Python SDK
- Docker Compose
- uv
- pytest
- ruff
- gunicorn

## Структура проекта

```text
.
├── app/
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py       # настройки Django, DRF, CORS, БД, email, OpenAI, логов
│   │   ├── urls.py           # маршруты API и Swagger
│   │   ├── middleware.py     # логирование всех HTTP-запросов
│   │   ├── exceptions.py     # глобальная обработка DRF-ошибок
│   │   ├── logging.py        # JSON formatter для логов
│   │   ├── asgi.py
│   │   └── wsgi.py
│   └── contacts/
│       ├── models.py         # модель ContactRequest
│       ├── serializers.py    # валидация входных данных и схемы ответов
│       ├── views.py          # API endpoints и Swagger-описания
│       ├── services.py       # бизнес-логика создания обращения
│       ├── ai.py             # OpenAI-интеграция и fallback
│       ├── emails.py         # отправка email-уведомлений
│       ├── throttling.py     # rate limiting
│       ├── migrations/
│       └── tests/
├── scripts/
│   └── docker-up.ps1         # запуск Docker Compose с автоподбором порта
├── docker-compose.yml        # web + PostgreSQL
├── Dockerfile
├── pyproject.toml            # зависимости, pytest, ruff
├── uv.lock
├── ruff / ruff.cmd           # запуск ruff как в проекте-образце
└── .env.example
```

## Архитектура

Проект сделан по слоистой схеме:

```text
HTTP request
  -> View
  -> Serializer validation
  -> Service
  -> AI handler
  -> Model/PostgreSQL
  -> Email handler
  -> HTTP response
```

Роли слоев:

- `views.py` принимает HTTP-запросы, выбирает serializer, возвращает HTTP-статусы и содержит подробные Swagger-описания.
- `serializers.py` отвечает за валидацию `name`, `phone`, `email`, `comment`.
- `services.py` содержит основной сценарий обработки обращения.
- `ai.py` изолирует работу с OpenAI и fallback-логику.
- `emails.py` изолирует отправку писем.
- `models.py` описывает хранение обращения, AI-результатов и статусов отправки email.
- `middleware.py` логирует каждый запрос.
- `exceptions.py` централизует обработку API-ошибок.

## Переменные окружения

Скопируйте пример:

```powershell
copy .env.example .env
```

Основные переменные:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DJANGO_TIME_ZONE=Europe/Moscow

DB_NAME=developer_landing
DB_USER=developer_landing
DB_PASSWORD=developer_landing
DB_HOST=db
DB_PORT=5432

APP_PORT=8080
CONTACT_CREATE_RATE_LIMIT=5/min
CONTACTS_PAGE_SIZE=20
LOG_LEVEL=INFO

SITE_OWNER_EMAIL=owner@example.com
DEFAULT_FROM_EMAIL=no-reply@example.com
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.5
OPENAI_TIMEOUT_SECONDS=12
```

Что важно:

- `APP_PORT` - внешний порт API на вашей машине.
- `DB_*` - настройки PostgreSQL-контейнера.
- `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` печатает письма в консоль контейнера. Для реальной SMTP-отправки настройте `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`.
- `OPENAI_API_KEY` можно оставить пустым. Тогда AI-блок будет работать через fallback-правила.
- `CONTACT_CREATE_RATE_LIMIT=5/min` ограничивает частоту отправки формы.

## Запуск

Основной запуск идет через Docker Compose: поднимаются `db` с PostgreSQL и `web` с Django API.

На Windows:

```powershell
.\scripts\docker-up.ps1
```

Скрипт выбирает свободный порт начиная с `8080`. Если `8080` занят, будет использован `8081`, затем `8082` и так далее.

Запуск в фоне:

```powershell
.\scripts\docker-up.ps1 -Detached
```

Обычный Docker Compose без автоподбора порта:

```powershell
docker compose up --build
```

Остановить контейнеры:

```powershell
docker compose down
```

Остановить контейнеры и удалить данные PostgreSQL:

```powershell
docker compose down -v
```

## Адреса после запуска

Если выбран порт `8080`:

- Swagger UI: `http://127.0.0.1:8080/api/docs`
- OpenAPI schema: `http://127.0.0.1:8080/api/schema`
- Health check: `http://127.0.0.1:8080/api/health`
- Metrics: `http://127.0.0.1:8080/api/metrics`

Если скрипт выбрал другой порт, замените `8080` на порт из строки `Using APP_PORT=...`.

## API

### POST `/api/contact`

Создает обращение.

Поля запроса:

- `name` - имя, минимум 2 символа.
- `phone` - телефон, минимум 7 цифр; разрешены `+`, пробелы, скобки, дефисы и точки.
- `email` - валидный email.
- `comment` - комментарий, минимум 10 символов.

Пример:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8080/api/contact" `
  -ContentType "application/json" `
  -Body '{"name":"Ada Lovelace","phone":"+7 999 123-45-67","email":"ada@example.com","comment":"Здравствуйте! Хочу обсудить backend API для проекта."}'
```

Успешный ответ возвращает `201`:

```json
{
  "id": 1,
  "name": "Ada Lovelace",
  "phone": "+7 999 123-45-67",
  "email": "ada@example.com",
  "comment": "Здравствуйте! Хочу обсудить backend API для проекта.",
  "status": "received",
  "sentiment": "neutral",
  "request_type": "consultation",
  "ai_reply": "Спасибо за обращение...",
  "ai_provider": "fallback:rules",
  "ai_fallback_reason": "OPENAI_API_KEY is not configured",
  "owner_email_sent": true,
  "user_email_sent": true,
  "created_at": "2026-06-22T13:00:00Z",
  "updated_at": "2026-06-22T13:00:00Z"
}
```

Возможные ошибки:

- `400` - невалидные данные формы.
- `429` - превышен rate limit.
- `502` - обращение сохранено, но email-уведомление не отправилось.

### GET `/api/health`

```powershell
Invoke-RestMethod http://127.0.0.1:8080/api/health
```

### GET `/api/metrics`

```powershell
Invoke-RestMethod http://127.0.0.1:8080/api/metrics
```

Возвращает количество обращений, статистику по статусам, тональности, типам обращений и дату последнего обращения.

## AI-интеграция

AI-блок находится в `app/contacts/ai.py`.

При наличии `OPENAI_API_KEY` сервис вызывает OpenAI Responses API и просит вернуть JSON:

```json
{
  "sentiment": "positive | neutral | negative",
  "request_type": "job_offer | consultation | feedback | question | other",
  "auto_reply": "короткий ответ пользователю на русском языке"
}
```

Если ключ не задан или OpenAI недоступен, используется fallback:

- тональность определяется по простым ключевым словам;
- тип обращения определяется по словам вроде `работа`, `вакансия`, `проект`, `консультация`, `вопрос`;
- пользователю формируется стандартный ответ;
- причина fallback сохраняется в `ai_fallback_reason`.

## Email

После сохранения обращения сервис отправляет два письма:

- владельцу сайта на `SITE_OWNER_EMAIL`;
- пользователю на email из формы.

По умолчанию используется console backend:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Это удобно для локальной проверки: письма не уходят наружу, а выводятся в лог контейнера `web`.

Посмотреть логи:

```powershell
docker compose logs -f web
```

## Логи

Файлы логов создаются в папке `logs/`:

- `logs/requests.log` - все HTTP-запросы в JSON-формате.
- `logs/errors.log` - ошибки и исключения.

Пример записи:

```json
{
  "timestamp": "2026-06-22T14:40:54+00:00",
  "level": "INFO",
  "logger": "requests",
  "message": "request handled",
  "method": "POST",
  "path": "/api/contact",
  "status_code": 201,
  "duration_ms": 24.7
}
```

## Проверка вручную

После запуска:

1. Откройте `http://127.0.0.1:8080/api/docs`.
2. Выполните `GET /api/health`.
3. Выполните `POST /api/contact` с валидными данными.
4. Выполните `POST /api/contact` с коротким `comment`, чтобы получить `400`.
5. Выполните `GET /api/metrics` и проверьте, что счетчик обращений изменился.
6. Проверьте `logs/requests.log`.
7. Проверьте `docker compose logs -f web`, там должны быть email-сообщения при console backend.

## Автотесты

Перед первым запуском установите зависимости:

```powershell
uv sync
```

Запустить тесты:

```powershell
uv run pytest
```

Тесты покрывают:

- доступность Swagger/OpenAPI;
- создание обращения;
- валидацию телефона и комментария;
- health endpoint;
- metrics endpoint;
- rate limiting;
- AI fallback helpers.

## Линтер и форматирование

Windows:

```powershell
.\ruff.cmd
```

Linux/macOS:

```bash
./ruff
```

Скрипт запускает:

```bash
uv run ruff check . --fix
uv run ruff format .
```

## Полезные команды

Проверить состояние контейнеров:

```powershell
docker compose ps
```

Посмотреть логи API:

```powershell
docker compose logs -f web
```

Посмотреть логи PostgreSQL:

```powershell
docker compose logs -f db
```

Применить миграции вручную:

```powershell
docker compose exec web uv run --no-sync python app/manage.py migrate
```

Открыть Django shell внутри контейнера:

```powershell
docker compose exec web uv run --no-sync python app/manage.py shell
```
