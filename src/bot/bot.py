"""Модуль для работы с Telegram ботом."""

import asyncio
import functools
import logging
from collections.abc import Callable, Coroutine
from typing import Any, Never, TypeVar

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from bot.config import ADMIN_GROUP_ID, ADMIN_URL, BOT_TOKEN
from bot.handlers import register_handlers
from bot.keyboards import get_registration_keyboard

logger = logging.getLogger(__name__)

T = TypeVar("T")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (TelegramAPIError,),
) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    """
    Декоратор для повторных попыток выполнения функции при возникновении ошибок.

    Args:
        max_retries: Максимальное количество попыток.
        delay: Задержка между попытками в секундах.
        exceptions: Кортеж исключений, при которых нужно повторять попытки.

    Returns:
        Декорированная функция.

    """

    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args: Never, **kwargs: Never) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        logger.exception(
                            "Failed after %d attempts. Last error: %s",
                            max_retries,
                            str(last_exception),
                        )
                    await asyncio.sleep(delay)
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator


@retry_on_error()
async def send_registration_notification(user_data: dict[str, str]) -> None:
    """
    Отправляет уведомление о регистрации нового пользователя в админ группу.

    Args:
        user_data: Данные пользователя для отправки в уведомлении.

    Raises:
        TelegramAPIError: При ошибке отправки сообщения в Telegram.

    """
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


async def start_bot() -> None:
    """
    Запускает бота в асинхронном контексте.

    Raises:
        Exception: При ошибке запуска бота.

    """
    try:
        register_handlers(dp)
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Failed to start bot")
        raise


def run_bot() -> None:
    """
    Запускает бота в синхронном контексте.

    Raises:
        Exception: При ошибке запуска бота.

    """
    try:
        asyncio.run(start_bot())
    except Exception:
        logger.exception("Bot stopped with error")
        raise
