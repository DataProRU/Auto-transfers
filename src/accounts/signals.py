"""Signals for handling events in accounts app."""

import logging
from typing import cast

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models.signals import post_save
from django.dispatch import receiver

from autotrips.tasks import send_registration_notification_task

from .models_types import UserProtocol

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def notify_admins_about_registration(
    instance: AbstractBaseUser,
    created: bool,
    **_: None,
) -> None:
    """
    Send notification to admins about new user registration.

    Args:
        instance: Model instance
        created: Flag indicating if object was created
        **_: Additional arguments (unused)

    """
    user = cast(UserProtocol, instance)
    if created and user.role == User.Roles.USER:
        try:
            # Check for required data
            if not user.full_name or not user.phone:
                logger.warning(
                    "Skipping notification for user %s: missing required data",
                    user.id,
                )
                return

            # Send task to high priority queue
            send_registration_notification_task.apply_async(
                args=[user.id],
                queue="high_priority",
                countdown=1,  # Small delay to ensure DB save
            )
            logger.info("Notification task for user %s queued", user.id)
        except Exception:
            logger.exception("Error queuing notification task")
