"""Celery tasks for autotrips app."""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from enum import Enum, auto
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast

from celery import Task, shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction

from accounts.models_types import UserProtocol
from bot.services import send_message_to_telegram_chat

logger = logging.getLogger(__name__)
User = get_user_model()

T = TypeVar("T")
P = ParamSpec("P")


def handle_async_errors(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, T]:
    """
    Handle async errors in Celery tasks.

    Args:
        func: Async function to decorate
    Returns:
        Callable: Synchronous wrapper function

    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return asyncio.run(func(*args, **kwargs))
        except Exception:
            logger.exception("Error in async function execution")
            raise

    return wrapper


class NotificationStatus(Enum):
    """Notification status."""

    SUCCESS = auto()
    FAILURE = auto()


def _process_notification_result(status: NotificationStatus, user_id: int) -> str | None:
    """
    Process notification result.

    Args:
        status: Notification status
        user_id: User ID
    Returns:
        str | None: Success message or None if failed

    """
    if status == NotificationStatus.SUCCESS:
        return f"Notification for user {user_id} sent successfully"
    return None


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_registration_notification_task(self: Task, user_id: int) -> str | None:
    """
    Send registration notification to admin group.

    Args:
        self: Celery task instance
        user_id: User ID
    Returns:
        str | None: Success message or None if failed
    Raises:
        ValidationError: If user_id is not an integer
        Exception: If notification sending fails

    """
    if not isinstance(user_id, int):
        raise ValidationError("User ID must be an integer")

    try:
        with transaction.atomic():
            try:
                instance = User.objects.select_for_update().get(id=user_id)
            except User.DoesNotExist:
                logger.exception("User with ID %s not found", user_id)
                return None

            user = cast(UserProtocol, instance)
            if not user.full_name or not user.phone:
                logger.error("Failed to send notification: missing user data for %s", user_id)
                return None

            @handle_async_errors
            async def send_notification() -> bool:
                success = await send_registration_notification(user_id)
                return bool(success)

            success = send_notification()
            status = NotificationStatus.SUCCESS if success else NotificationStatus.FAILURE
            return _process_notification_result(status, user_id)

    except Exception as exc:
        logger.exception("Error sending notification for user %s", user_id)
        raise self.retry(exc=exc) from exc


@shared_task
async def send_registration_notification(user_id: int) -> bool:
    try:
        user = await User.objects.aget(id=user_id)
        message = (
            f"Новый пользователь зарегистрирован!\n\n"
            f"ФИО: {user.full_name}\n"
            f"Телефон: {user.phone}\n"
            f"Telegram: {user.telegram}\n"
            f"Роль: {user.get_role_display()}"
        )
        chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)
        if chat_id is None:
            return False
        await send_message_to_telegram_chat(chat_id, message)
    except (ObjectDoesNotExist, ConnectionError, OSError) as e:
        logger.exception("Ошибка при отправке уведомления", exc_info=e)
        return False
    else:
        return True


@shared_task
async def send_notification(user_id: int) -> bool:
    try:
        success = await send_registration_notification(user_id)
        return bool(success)
    except (ObjectDoesNotExist, ConnectionError, OSError) as e:
        logger.exception("Ошибка при отправке уведомления", exc_info=e)
        return False
