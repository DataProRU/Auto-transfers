"""Telegram bot module."""

import asyncio
import logging
from typing import cast

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser

from accounts.types import UserProtocol

from .config import ADMIN_GROUP_ID, ADMIN_URL, BOT_TOKEN
from .handlers.admin_handlers import router as admin_router
from .keyboards.admin_keyboards import get_approval_keyboard

logger = logging.getLogger(__name__)
User = get_user_model()


async def get_bot() -> tuple[Bot, Dispatcher]:
    """
    Create and return bot instance.

    Returns:
        tuple[Bot, Dispatcher]: Bot and dispatcher instances

    """
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(admin_router)
    return bot, dp


@sync_to_async
def get_user(user_id: int) -> AbstractBaseUser | None:
    """
    Get user from database.

    Args:
        user_id: User ID

    Returns:
        User | None: User object or None if not found

    """
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.exception("User with ID %s not found", user_id)
        return None


async def send_registration_notification(user_id: int) -> bool:
    """
    Send registration notification to admin group.

    Args:
        user_id: User ID

    Returns:
        bool: True if notification sent successfully, False otherwise

    """
    if not ADMIN_GROUP_ID:
        raise ValueError("ADMIN_GROUP_ID is not set")

    bot, _ = await get_bot()
    try:
        instance = await get_user(user_id)
        if not instance:
            logger.error("Failed to send notification: user %s not found", user_id)
            return False

        user = cast(UserProtocol, instance)
        if not user.full_name or not user.phone:
            logger.error("Failed to send notification: missing user data for %s", user_id)
            return False

        documents_url = f"{ADMIN_URL}accounts/documentimage/?user__id__exact={user_id}"

        message_text = (
            "📝 New receiver registered:\n\n"
            f"👤 Full name: {user.full_name}\n"
            f"📱 Phone: {user.phone}\n"
            f"🔗 <a href='{documents_url}'>Identity documents</a>"
        )

        try:
            await bot.send_message(
                chat_id=int(ADMIN_GROUP_ID),
                text=message_text,
                reply_markup=get_approval_keyboard(user_id),
                parse_mode="HTML",
            )
            logger.info("Registration notification for user %s sent successfully", user_id)
        except TelegramAPIError:
            logger.exception("Telegram API error while sending notification")
            return False
        else:
            return True

    except Exception:
        logger.exception("Unexpected error while sending notification")
        return False
    finally:
        await bot.session.close()


async def start_bot() -> None:
    """Start the bot."""
    bot, dp = await get_bot()
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


def run_bot() -> None:
    """Run the bot in synchronous context."""
    asyncio.run(start_bot())
