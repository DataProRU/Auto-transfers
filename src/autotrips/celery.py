"""Celery configuration for the project."""

import os
from typing import Never

from celery import Celery, Task
from celery.signals import after_setup_logger, after_setup_task_logger
from django.core.exceptions import ImproperlyConfigured

from .logging_config import setup_logging

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autotrips.settings")

# Создание экземпляра Celery
app = Celery("autotrips")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Настройка брокера сообщений (Redis)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
if not REDIS_URL:
    raise ImproperlyConfigured("REDIS_URL environment variable is not set")

app.conf.broker_url = REDIS_URL
app.conf.result_backend = REDIS_URL

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
app.conf.task_track_started = True
app.conf.task_time_limit = 3600  # 1 hour
app.conf.task_soft_time_limit = 3300  # 55 minutes

# Настройки для мониторинга
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 1000

# Настройки для обработки ошибок
app.conf.task_annotations = {
    "*": {
        "rate_limit": "10/s",
        "max_retries": 3,
        "default_retry_delay": 60,
        "autoretry_for": (Exception,),
        "retry_backoff": True,
        "retry_backoff_max": 600,
    }
}


@app.task(bind=True)
def debug_task(self: Task) -> str:
    """
    Debug task.

    Args:
        self: Task instance

    Returns:
        str: Debug message

    """
    return f"Request: {self.request!r}"


# Настройка логирования
@after_setup_logger.connect
def setup_celery_logging(*_args: Never, **_kwargs: Never) -> None:
    """Configure Celery logging."""
    setup_logging()


@after_setup_task_logger.connect
def setup_celery_task_logging(*_args: Never, **_kwargs: Never) -> None:
    """Configure Celery task logging."""
    setup_logging()
