# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
# WORKDIR /app

# Устанавливаем системные зависимости для psycopg2
# RUN apt-get update && apt-get install -y \
 #    libpq-dev \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
# RUN pip install poetry

# Копируем зависимости
# COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости проекта
# RUN poetry install --no-root

# Копируем исходный код проекта
# COPY src/ ./src/

# Устанавливаем рабочую директорию для Django-проекта
# WORKDIR /app/src

# Команда для запуска приложения
# CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]