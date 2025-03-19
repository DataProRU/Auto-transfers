"""Модуль для работы c Telegram ботом."""

import asyncio
import logging
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config import ADMIN_GROUP_ID, ADMIN_URL, BOT_TOKEN
from bot.handlers import register_handlers
from bot.keyboards import get_registration_keyboard

logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


async def send_registration_notification(user_data: dict[str, Any]) -> None:
    """
    Отправляет уведомление o регистрации нового пользователя в админ группу.

    Args:
        user_data: Данные пользователя для отправки в уведомлении.

    """
    try:
        message_text = (
            f"🆕 Новая заявка на регистрацию!\n\n"
            f"👤 ФИО: {user_data['full_name']}\n"
            f"📱 Телефон: {user_data['phone']}\n"
            f"📧 Telegram: {user_data['telegram']}\n"
            f"🔗 Админ панель: {ADMIN_URL}"
        )

        keyboard = get_registration_keyboard(user_data["id"])

        await bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=message_text,
            reply_markup=keyboard,
        )
        logger.info("Registration notification sent successfully")
    except Exception:
        logger.exception("Error while sending registration notification")
        raise


async def start_bot() -> None:
    """Запускает бота в асинхронном контексте."""
    try:
        register_handlers(dp)
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Error while starting bot")
        raise


def run_bot() -> None:
    """Запускает бота в синхронном контексте."""
    asyncio.run(start_bot())
