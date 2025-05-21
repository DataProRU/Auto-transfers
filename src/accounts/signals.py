import asyncio
import logging
from typing import Any

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import AiogramError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from services.table_service import crm_table_manager

from .models import User

logger = logging.getLogger(__name__)
URL = settings.FRONTEND_URL
WORKSHEET = settings.CLIENTS_WORKSHEET


class SpreadsheetError(Exception):
    """Custom exception for google table-related errors."""


class NotificationError(Exception):
    """Custom exception for telegram-related errors."""


def _build_user_register_keyboard(user_id: int) -> InlineKeyboardMarkup:
    accept_button = InlineKeyboardButton(text="Принять", callback_data=f"accept:{user_id}")
    reject_button = InlineKeyboardButton(text="Отклонить", callback_data=f"reject:{user_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[accept_button, reject_button]])


def _build_client_register_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Обработать", callback_data="process_report:")]]
    )


def _get_register_user_text(user: User) -> str:
    """Generate user registration notification text."""
    documents_url = f"Ссылка на документы: {URL}docs/{user.id}"
    return f"Зарегистрирован новый приемщик:\n👤 {user.full_name}\n📱 {user.phone}\n{documents_url}"


def _get_register_client_text(user: User) -> str:
    """Generate client registration notification text."""
    return f"Зарегистрирован новый клиент:\n👤 {user.full_name}\n📱 {user.phone}\n✉️ @{user.telegram}"


async def _send_telegram_notification(bot: Bot, chat_id: str, text: str, keyboard: InlineKeyboardMarkup) -> None:
    """Help to send Telegram message with proper error handling."""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.info("Telegram notification sent successfully.")
    except AiogramError as e:
        msg = f"Telegram API error: {e!s}"
        logger.exception(msg)
    except Exception as e:
        msg = f"Failed to send Telegram notification: {e!s}"
        raise NotificationError(msg) from e


def _handle_client_registration(instance: User) -> None:
    """Handle the registration process for client users."""
    try:
        create_datetime = timezone.now().strftime("%Y-%m-%d %H:%M")
        data = [
            create_datetime,
            instance.full_name,
            instance.company,
            instance.phone,
            instance.telegram,
            instance.address,
            instance.email,
        ]
        crm_table_manager.append_row(WORKSHEET, data)
    except Exception as e:
        msg = f"Failed to write client registration data into table: {e!s}"
        raise SpreadsheetError(msg) from e


def _prepare_notification_content(instance: User) -> tuple[str, InlineKeyboardMarkup]:
    """Prepare the notification text and keyboard based on user role."""
    if instance.role == User.Roles.USER:
        text = _get_register_user_text(instance)
        keyboard = _build_user_register_keyboard(instance.id)
    else:
        text = _get_register_client_text(instance)
        keyboard = _build_client_register_keyboard()

    return text, keyboard


def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """Get existing event loop or create a new one."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def _handle_notification_sending(text: str, keyboard: InlineKeyboardMarkup) -> None:
    """Handle the async notification sending process."""
    from telegram_bot.bot import bot

    try:
        loop = _get_or_create_event_loop()
        coro = _send_telegram_notification(
            bot=bot, chat_id=settings.TELEGRAM_GROUP_CHAT_ID, text=text, keyboard=keyboard
        )

        if loop.is_running():
            asyncio.create_task(coro)  # noqa: RUF006
        else:
            loop.run_until_complete(coro)

    except Exception as e:
        msg = f"Failed to process notification sending: {e!s}"
        raise NotificationError(msg) from e


@receiver(post_save, sender=User)
def send_registration_notification(sender: User, instance: User, created: bool, **kwargs: dict[Any, str]) -> None:  # noqa: ARG001, FBT001
    """Send Telegram notification when new user is created."""
    if not created:
        return

    try:
        if instance.role == User.Roles.CLIENT:
            _handle_client_registration(instance)

        text, keyboard = _prepare_notification_content(instance)

        _handle_notification_sending(text, keyboard)

    except SpreadsheetError as e:
        msg = f"Failed to update spreadsheet for client {instance.full_name}: {e!s}"
        logger.exception(msg)
    except NotificationError as e:
        msg = f"Failed to send Telegram notification: {e!s}"
        logger.exception(msg)
    except Exception as e:
        msg = f"Unexpected error in registration notification: {e!s}"
        logger.exception(msg)
