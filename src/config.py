"""
Централизованная конфигурация проекта.

Этот модуль содержит все настройки проекта, загружаемые из переменных окружения.
"""

import os
from typing import Final

from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки Django
DJANGO_SETTINGS_MODULE: Final[str] = "project.settings"
SECRET_KEY: Final[str] = os.getenv("SECRET_KEY", "django-insecure-1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p")
DEBUG: Final[bool] = os.getenv("DEBUG", "False").lower() == "true"
ENVIRONMENT: Final[str] = os.getenv("ENVIRONMENT", "development")

# Настройки базы данных
DATABASE_URL: Final[str] = os.getenv(
    "DATABASE_URL",
    "postgres://autotrips:autotrips@localhost:5432/autotrips",
)

# Настройки Redis и Celery
REDIS_URL: Final[str] = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_BROKER_URL: Final[str] = REDIS_URL
CELERY_RESULT_BACKEND: Final[str] = REDIS_URL

# Настройки Telegram бота
BOT_TOKEN: Final[str] = os.getenv("BOT_TOKEN", "")
ADMIN_GROUP_ID: Final[str] = os.getenv("ADMIN_GROUP_ID", "")
ADMIN_URL: Final[str] = os.getenv("ADMIN_URL", "http://localhost:8000/admin/")

# Настройки безопасности
ALLOWED_HOSTS: Final[list[str]] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CORS_ALLOWED_ORIGINS: Final[list[str]] = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

# Настройки для загрузки файлов
MEDIA_ROOT: Final[str] = os.getenv("MEDIA_ROOT", "media")
STATIC_ROOT: Final[str] = os.getenv("STATIC_ROOT", "static")
