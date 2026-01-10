Для запуска приложения

1. Склонируйте репозиторий
2. Установите pyenv
https://github.com/pyenv/pyenv
```
pyenv install 3.12.7
pyenv local 3.12.7
```
3. Создайте и запустите виртуальное окружение poetry
```
poetry env use python3.12 # или 3.12.7
eval $(poetry env activate) 
```
Документация
```
https://python-poetry.org/docs/managing-environments/#bash-csh-zsh
```
4. Установите библиотеки
```
poetry install
```
5. Разверните базу данных и MinIO
```
 docker compose up -d
```

MinIO будет доступен по адресу:
- API: http://localhost:9000
- Web Console: http://localhost:9001
- Логин: MINIO_ROOT_USER=
- Пароль: MINIO_ROOT_PASSWORD=
- MINIO_REGION_NAME="us-east-1"

6. Настройте переменные окружения

Создайте файл `.env` в корне проекта. Скопируйте содержимое из файла `.env.example` и замените пароли на свои:

```bash
# Database Configuration (for Docker services)
POSTGRES_DB=autotrips
POSTGRES_USER=autotrips
POSTGRES_PASSWORD=your_secure_database_password_here

# MinIO Configuration (for Docker services)
MINIO_ROOT_USER=your_minio_admin_username
MINIO_ROOT_USER=your_secure_minio_password_here
MINIO_REGION_NAME=us-east-1

# Django Application Configuration
DATABASE_NAME=autotrips
DATABASE_USER=autotrips
DATABASE_PASSWORD=your_secure_database_password_here
DATABASE_HOST=localhost
DATABASE_PORT=5432
SECRET_KEY=your-very-long-and-secure-secret-key-here-change-this-in-production
DEBUG=1
ALLOWED_HOSTS=
FRONTEND_URL=http://localhost:5173/

# S3/MinIO Configuration (for Django storages)
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=your_minio_admin_username_or_s3_key
S3_SECRET_ACCESS_KEY=your_secure_minio_password_or_s3_access
S3_STORAGE_BUCKET_NAME=autotrips

# Telegram Bot Configuration (optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_GROUP_CHAT_ID=your_telegram_group_chat_id

# Google Sheets Configuration (optional)
TABLE_ID=your_google_table_id
CRM_TABLE_ID=your_crm_table_id
TABLE_CREDS=path/to/your/service-account-creds.json
VINS_WORKSHEET=База VIN
CHECKER_WORKSHEET=База приемщиков
REPORTS_WORKSHEET=Принятие авто 2
CLIENTS_WORKSHEET=База клиентов
VEHICLES_WORKSHEET=Заявки на ТС

# Admin Configuration
ADMIN_FULLNAME=Your Name
ADMIN_PHONE=+1234567890
ADMIN_TELEGRAM=@your_username
ADMIN_PASSWORD=your_secure_admin_password
```

Просто скопируйте файл `.env.example` и отредактируйте его:
```bash
cp .env.example .env
# Затем отредактируйте .env файл с вашими значениями
```

## Хранение файлов (S3/MinIO)

Приложение использует гибкую систему хранения файлов, которая автоматически переключается между локальным и облачным хранилищем.

### Локальная разработка (MinIO)
Для разработки используется MinIO - S3-совместимое хранилище, запущенное в Docker:
- **Эндпоинт**: `http://localhost:9000`
- **Консоль MinIO**: `http://localhost:9001`
- **Логин/Пароль**: Настраивается в переменных `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD`

### Продакшн (Облачное S3)
В продакшне используются переменные для подключения к реальному S3-совместимому хранилищу:
- **Эндпоинт**: Ваш S3 endpoint (например, от reg.ru или AWS)
- **Ключи доступа**: `S3_ACCESS_KEY_ID` и `S3_SECRET_ACCESS_KEY`
- **Бакет**: `S3_STORAGE_BUCKET_NAME`

### Логика работы
Приложение проверяет наличие всех S3 переменных окружения:
- Если все переменные заданы → использует S3/MinIO хранилище
- Если какие-то переменные отсутствуют → использует локальное файловое хранилище


7. Примените миграции
```
poetry run python src/manage.py migrate
```
8. Запустите приложение
```
poetry run python src/manage.py runserver
```
9. Запустите телеграм бота
```
poetry run python src/manage.py start_bot
```
10. Импортировать VIN номера (опционально)
```
poetry run python src/manage.py import_vehicles /path/to/file.xlsx --sheet-name "Sheet name" --skip-rows 1
```