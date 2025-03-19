"""Модуль для работы с Telegram ботом."""

import asyncio
import functools
import logging
from collections.abc import Callable, Coroutine
from typing import Any, Never, TypeVar

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from accounts.models.user import User
from bot.config import ADMIN_GROUP_ID, ADMIN_URL, BOT_TOKEN
import bot.handlers as handlers_module
from bot.keyboards import get_registration_keyboard

logger = logging.getLogger(__name__)

T = TypeVar("T")


def get_user_info_message(user: User) -> str:
    """
    Формирует информационное сообщение о пользователе.

    Args:
        user: Объект пользователя

    Returns:
        str: Отформатированное сообщение с информацией о пользователе
    """
    return (
        f"👤 Пользователь: {user.get_full_name()}\n"
        f"📧 Email: {user.email}\n"
        f"📱 Телефон: {user.phone or 'Не указан'}\n"
        f"📅 Дата регистрации: {user.date_joined.strftime('%d.%m.%Y %H:%M')}"
    )


async def send_message_to_telegram_chat(message: str) -> bool:
    """
    Отправляет сообщение в указанный Telegram чат.

    Args:
        message: Текст сообщения

    Returns:
        bool: True если сообщение отправлено успешно, False в противном случае
    """
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=message,
            parse_mode=ParseMode.HTML
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
        return False


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (TelegramAPIError,),
) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    """
    Декоратор для повторных попыток выполнения функции при ошибках.

    Args:
        max_retries: Максимальное количество попыток
        delay: Задержка между попытками в секундах
        exceptions: Кортеж исключений, при которых нужно повторять попытку

    Returns:
        Callable: Декорированная функция
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
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Попытка {attempt + 1}/{max_retries} не удалась: {e}. "
                            f"Повторная попытка через {delay} секунд..."
                        )
                        await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


@retry_on_error()
async def send_registration_notification(user_data: dict[str, str]) -> None:
    """
    Отправляет уведомление о регистрации нового пользователя.

    Args:
        user_data: Словарь с данными пользователя
    """
    bot = Bot(token=BOT_TOKEN)
    message = (
        f"🆕 Новый пользователь зарегистрировался!\n\n"
        f"👤 Имя: {user_data.get('first_name', 'Не указано')}\n"
        f"📧 Email: {user_data.get('email', 'Не указан')}\n"
        f"📱 Телефон: {user_data.get('phone', 'Не указан')}\n\n"
        f"🔗 Админка: {ADMIN_URL}"
    )
    await bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=message,
        parse_mode=ParseMode.HTML,
        reply_markup=get_registration_keyboard(user_data.get("id", ""))
    )


async def start_bot() -> None:
    """Запускает бота."""
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    handlers_module.register_handlers(dp)
    await dp.start_polling(bot)


def run_bot() -> None:
    """Запускает бота в отдельном потоке."""
    asyncio.run(start_bot())
