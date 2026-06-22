import os
import sys
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-insecure-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in {"1", "true", "yes", "on"}
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "corsheaders",
    "drf_spectacular",
    "rest_framework",
    "contacts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "config.middleware.RequestLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [],
        "OPTIONS": {"context_processors": []},
    }
]

DATABASE_URL = os.getenv("DATABASE_URL")
IS_TESTING = any(Path(arg).name.startswith("pytest") or arg == "test" for arg in sys.argv)

if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=60)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:" if IS_TESTING else PROJECT_ROOT / "db.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Europe/Moscow")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if origin.strip()
]
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", str(DEBUG)).lower() in {
    "1",
    "true",
    "yes",
    "on",
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.getenv("CONTACTS_PAGE_SIZE", "20")),
    "EXCEPTION_HANDLER": "config.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "contact_create": os.getenv("CONTACT_CREATE_RATE_LIMIT", "5/min"),
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Developer Landing Contact API",
    "DESCRIPTION": (
        "REST API for a developer landing contact form. The service validates requests, "
        "runs AI-assisted classification and sentiment analysis, sends owner/user email "
        "notifications, applies rate limiting, and exposes operational metrics."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CONTACT_CREATE_RATE_LIMIT = os.getenv("CONTACT_CREATE_RATE_LIMIT", "5/min")
SITE_OWNER_EMAIL = os.getenv("SITE_OWNER_EMAIL", "owner@example.com")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@example.com")

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() in {"1", "true", "yes", "on"}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "12"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "config.logging.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "requests_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "requests.log",
            "formatter": "json",
            "encoding": "utf-8",
        },
        "errors_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "errors.log",
            "formatter": "json",
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "errors_file"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "requests": {
            "handlers": ["requests_file", "console"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
