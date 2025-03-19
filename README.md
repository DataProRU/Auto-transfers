# Auto-transfers

Система управления автопоездками с интеграцией Telegram бота.

## Требования

- Python 3.12+
- PostgreSQL 14+
- Redis 7+
- Poetry

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/auto-transfers.git
cd auto-transfers
```

2. Установите зависимости с помощью Poetry:
```bash
poetry install
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Отредактируйте `.env` файл, установив необходимые значения переменных окружения.

5. Примените миграции базы данных:
```bash
poetry run python src/manage.py migrate
```

6. Создайте суперпользователя:
```bash
poetry run python src/manage.py createsuperuser
```

## Запуск

1. Запустите Redis:
```bash
docker-compose up -d redis
```

2. Запустите Celery:
```bash
poetry run celery -A project worker -l info
```

3. Запустите Django сервер:
```bash
poetry run python src/manage.py runserver
```

4. Запустите Telegram бота:
```bash
poetry run python src/run_bot.py
```

## Разработка

### Линтинг и типизация

Проект использует `ruff` для линтинга и `mypy` для проверки типов:

```bash
# Запуск линтера
poetry run ruff check .

# Запуск проверки типов
poetry run mypy .
```

### Тесты

Запуск тестов:

```bash
poetry run pytest
```

## Структура проекта

```
src/
├── accounts/          # Приложение для управления пользователями
├── autotrips/         # Приложение для управления поездками
├── bot/              # Telegram бот
└── project/          # Основные настройки Django
```

## API документация

API документация доступна по адресу `/api/schema/swagger-ui/` после запуска сервера.

## Лицензия

MIT