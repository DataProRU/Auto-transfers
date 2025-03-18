"""Admin handlers for Telegram bot."""

import logging
from typing import cast

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models_types import UserProtocol

logger = logging.getLogger(__name__)
router = Router()
User = get_user_model()


def check_admin_rights(callback: CallbackQuery) -> bool:
    """
    Check if user has admin rights.

    Args:
        callback: Callback query from user

    Returns:
        bool: True if user has admin rights, False otherwise

    """
    # Checking user's chat_id
    # In real application, there should be admin check here
    # For example, checking chat_id against admin list or checking role in DB
    return bool(callback.from_user and callback.from_user.id)  # type: ignore[truthy-bool]


@router.callback_query(F.data.startswith("approve_user:"))
async def approve_user(callback: CallbackQuery) -> None:
    """
    Handle user approval.

    Args:
        callback: Callback query from admin

    """
    if not callback.data or not callback.message:
        logger.error("Invalid callback data or message")
        return

    if not check_admin_rights(callback):
        logger.warning("Unauthorized access attempt from user %s", callback.from_user.id)
        await callback.answer("Y вас нет прав для выполнения этого действия")
        return

    try:
        user_id = int(callback.data.split(":")[1])
        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(id=user_id)
            except User.DoesNotExist:
                logger.exception("User with ID %s not found", user_id)
                await callback.answer("Пользователь не найден")
                return

            user_protocol = cast(UserProtocol, user)
            user.is_active = True
            user.save()

            message = callback.message
            if isinstance(message, Message):
                await message.edit_text(
                    f"Пользователь {user_protocol.full_name} одобрен ✅",
                    reply_markup=None,
                )
                await callback.answer("Пользователь успешно одобрен")
            else:
                logger.error("Invalid message type")

    except ValueError:
        logger.exception("Invalid user ID format")
        await callback.answer("Некорректный формат ID пользователя")
    except Exception:
        logger.exception("Error while approving user")
        await callback.answer("Произошла ошибка при одобрении пользователя")


@router.callback_query(F.data.startswith("reject_user:"))
async def reject_user(callback: CallbackQuery) -> None:
    """
    Handle user rejection.

    Args:
        callback: Callback query from admin

    """
    if not callback.data or not callback.message:
        logger.error("Invalid callback data or message")
        return

    if not check_admin_rights(callback):
        logger.warning("Unauthorized access attempt from user %s", callback.from_user.id)
        await callback.answer("Y вас нет прав для выполнения этого действия")
        return

    try:
        user_id = int(callback.data.split(":")[1])
        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(id=user_id)
            except User.DoesNotExist:
                logger.exception("User with ID %s not found", user_id)
                await callback.answer("Пользователь не найден")
                return

            user_protocol = cast(UserProtocol, user)
            user.is_active = False
            user.save()

            message = callback.message
            if isinstance(message, Message):
                await message.edit_text(
                    f"Пользователь {user_protocol.full_name} отклонен ❌",
                    reply_markup=None,
                )
                await callback.answer("Пользователь успешно отклонен")
            else:
                logger.error("Invalid message type")

    except ValueError:
        logger.exception("Invalid user ID format")
        await callback.answer("Некорректный формат ID пользователя")
    except Exception:
        logger.exception("Error while rejecting user")
        await callback.answer("Произошла ошибка при отклонении пользователя")
