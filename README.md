# Auto-transfers

Система автоматизации работы с перевозчиками.

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/DataProRU/Auto-transfers.git
cd Auto-transfers
```

2. Создайте файл `.env` и заполните его:
```bash
# Database settings
DATABASE_URL=postgres://autotrips:autotrips@localhost:5432/autotrips
SECRET_KEY=your-secret-key

# Telegram Bot settings
BOT_TOKEN=your_bot_token_here
ADMIN_GROUP_ID=your_admin_group_id_here
ADMIN_URL=http://localhost:8000/admin/
```

3. Запустите проект через Docker Compose:
```bash
docker-compose up --build
```

4. Откройте в браузере:
- Админ-панель: http://localhost:8000/admin/
- pgAdmin: http://localhost:5050/

## Разработка

1. Установите Poetry:
```bash
pip install poetry
```

2. Установите зависимости:
```bash
poetry install
```

3. Примените миграции:
```bash
poetry run python src/manage.py migrate
```

4. Создайте суперпользователя:
```bash
poetry run python src/manage.py createsuperuser
```

5. Запустите сервер разработки:
```bash
poetry run python src/manage.py runserver
```

6. Запустите бота:
```bash
poetry run python src/manage.py runbot
```