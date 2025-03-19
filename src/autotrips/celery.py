"""Celery configuration for the project."""

import os
from typing import Never

from celery import Celery, Task
from celery.signals import after_setup_logger, after_setup_task_logger

from .logging_config import setup_logging

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

# Создание экземпляра Celery
app = Celery(
    "src.autotrips",
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0",
)

app.conf.broker_connection_retry_on_startup = True
app.conf.worker_pool = "solo"
app.conf.broker_connection_max_retries = None

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self: Task) -> str:
    """Debug task."""
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
