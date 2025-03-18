"""Celery configuration for the project."""

import os

from celery import Celery, Task

# Установка переменной окружения для настроек Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Создание экземпляра Celery
app = Celery("autotrips")

# Загрузка настроек из файла settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматическая загрузка задач из всех зарегистрированных приложений Django
app.autodiscover_tasks()

# Настройка брокера сообщений (Redis)
app.conf.broker_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Настройка бэкенда для хранения результатов
app.conf.result_backend = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Настройки очередей
app.conf.task_queues = {
    "default": {
        "exchange": "default",
        "routing_key": "default",
        "queue_arguments": {"x-max-priority": 10},
    },
    "high_priority": {
        "exchange": "high_priority",
        "routing_key": "high_priority",
        "queue_arguments": {"x-max-priority": 20},
    },
}

# Настройки для обработки ошибок
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

# Настройки для мониторинга
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True


@app.task(bind=True)
def debug_task(self: Task) -> None:
    """Test task to check Celery functionality."""
    logger = app.log.get_default_logger()
    logger.info("Request: %r", self.request)
