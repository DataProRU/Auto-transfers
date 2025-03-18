# Используем официальный образ Python
FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install poetry

# Копирование файлов проекта
COPY pyproject.toml poetry.lock ./

# Установка зависимостей
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Копирование исходного кода
COPY . .

# Создание директории для медиафайлов
RUN mkdir -p /app/media