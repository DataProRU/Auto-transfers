"""Обработчики команд Telegram бота."""

import logging

from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


async def start_command(message: Message) -> None:
    """
    Обработчик команды /start.

    Args:
        message: Сообщение от пользователя.

    """
    await message.answer("Привет! Я бот для управления регистрациями пользователей.")


async def help_command(message: Message) -> None:
    """
    Обработчик команды /help.

    Args:
        message: Сообщение от пользователя.

    """
    help_text = (
        "Доступные команды:\n"
        "/start - Начать работу c ботом\n"
        "/help - Показать это сообщение"
    )
    await message.answer(help_text)


async def approve_user(callback: CallbackQuery, user_id: int) -> None:
    """
    Обработчик подтверждения регистрации пользователя.

    Args:
        callback: Callback запрос от кнопки.
        user_id: ID пользователя для подтверждения.

    """
    try:
        user = await User.objects.aget(id=user_id)
        user.is_active = True
        await user.asave()

        await callback.message.edit_text(
            f"✅ Пользователь {user.full_name} успешно подтвержден!",
            reply_markup=None,
        )
        logger.info("User %s approved successfully", user_id)
    except Exception:
        logger.exception("Error while approving user")
        await callback.answer("Произошла ошибка при подтверждении пользователя")


async def reject_user(callback: CallbackQuery, user_id: int) -> None:
    """
    Обработчик отклонения регистрации пользователя.

    Args:
        callback: Callback запрос от кнопки.
        user_id: ID пользователя для отклонения.

    """
    try:
        user = await User.objects.aget(id=user_id)
        await user.adelete()

        await callback.message.edit_text(
            f"❌ Пользователь {user.full_name} отклонен.",
            reply_markup=None,
        )
        logger.info("User %s rejected successfully", user_id)
    except Exception:
        logger.exception("Error while rejecting user")
        await callback.answer("Произошла ошибка при отклонении пользователя")


def register_handlers(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики команд бота.

    Args:
        dp: Диспетчер бота.

    """
    dp.message.register(start_command, Command("start"))
    dp.message.register(help_command, Command("help"))

    dp.callback_query.register(
        approve_user,
        F.data.startswith("approve_"),
        lambda c: {"user_id": int(c.data.split("_")[1])},
    )
    dp.callback_query.register(
        reject_user,
        F.data.startswith("reject_"),
        lambda c: {"user_id": int(c.data.split("_")[1])},
    )
