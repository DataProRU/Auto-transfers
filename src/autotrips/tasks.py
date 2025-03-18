"""Celery tasks for autotrips app."""

import asyncio
import logging
from typing import cast

from celery import Task, shared_task
from django.contrib.auth import get_user_model

from accounts.models_types import UserProtocol

from .bot.bot import send_registration_notification

logger = logging.getLogger(__name__)
User = get_user_model()


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
        Exception: If notification sending fails

    """
    try:
        instance = User.objects.get(id=user_id)
        user = cast(UserProtocol, instance)
        if not user.full_name or not user.phone:
            logger.error("Failed to send notification: missing user data for %s", user_id)
            return None

        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(send_registration_notification(user_id))
            if success:
                return f"Notification for user {user_id} sent successfully"
            return None
        finally:
            loop.close()

    except User.DoesNotExist:
        logger.exception("User with ID %s not found", user_id)
        return None
    except Exception as exc:
        logger.exception("Error sending notification for user %s", user_id)
        raise self.retry(exc=exc) from exc
