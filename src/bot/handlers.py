"""Обработчики команд Telegram бота."""

import logging

from aiogram import Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from accounts.models.user import User
import bot.bot as bot_module

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """
    Обработчик команды /start.

    Args:
        message: Сообщение от пользователя.

    """
    await message.answer(
        "Привет! Я бот для управления пользователями. "
        "Я буду отправлять вам уведомления o новых регистрациях "
        "и позволю вам одобрять или отклонять пользователей."
    )


async def help_command(message: Message) -> None:
    """
    Обработчик команды /help.

    Args:
        message: Сообщение от пользователя.

    """
    help_text = "Доступные команды:\n/start - Начать работу c ботом\n/help - Показать это сообщение"
    await message.answer(help_text)


@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback: CallbackQuery) -> None:
    if not callback.message or not callback.data:
        return

    user_id = int(callback.data.split("_")[1])
    try:
        user = await User.objects.aget(id=user_id)
        user.is_approved = True
        await user.asave()

        if isinstance(callback.message, Message):
            await callback.message.edit_text(
                bot_module.get_user_info_message(user) + "\n\n✅ Пользователь одобрен",
                reply_markup=None,
            )
    except User.DoesNotExist:
        if isinstance(callback.message, Message):
            await callback.message.edit_text(
                "❌ Пользователь не найден",
                reply_markup=None,
            )
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("reject_"))
async def reject_user(callback: CallbackQuery) -> None:
    if not callback.message or not callback.data:
        return

    user_id = int(callback.data.split("_")[1])
    try:
        user = await User.objects.aget(id=user_id)
        user.is_approved = False
        await user.asave()

        if isinstance(callback.message, Message):
            await callback.message.edit_text(
                bot_module.get_user_info_message(user) + "\n\n❌ Пользователь отклонен",
                reply_markup=None,
            )
    except User.DoesNotExist:
        if isinstance(callback.message, Message):
            await callback.message.edit_text(
                "❌ Пользователь не найден",
                reply_markup=None,
            )
    finally:
        await callback.answer()


def register_handlers(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики команд бота.

    Args:
        dp: Диспетчер бота.

    """
    dp.message.register(start_handler, Command("start"))
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
