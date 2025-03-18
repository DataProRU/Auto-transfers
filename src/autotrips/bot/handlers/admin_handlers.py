"""Admin handlers for Telegram bot."""

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from django.contrib.auth import get_user_model

router = Router()
User = get_user_model()


@router.callback_query(F.data.startswith("approve_user:"))
async def approve_user(callback: CallbackQuery) -> None:
    """
    Handle user approval.

    Args:
        callback: Callback query from admin

    """
    if not callback.data or not callback.message:
        return

    user_id = int(callback.data.split(":")[1])
    user = User.objects.get(id=user_id)
    user.is_active = True
    user.save()

    message = callback.message
    if isinstance(message, Message):
        await message.edit_text(
            f"Пользователь {user.full_name} одобрен ✅",
            reply_markup=None,
        )


@router.callback_query(F.data.startswith("reject_user:"))
async def reject_user(callback: CallbackQuery) -> None:
    """
    Handle user rejection.

    Args:
        callback: Callback query from admin

    """
    if not callback.data or not callback.message:
        return

    user_id = int(callback.data.split(":")[1])
    user = User.objects.get(id=user_id)
    user.is_active = False
    user.save()

    message = callback.message
    if isinstance(message, Message):
        await message.edit_text(
            f"Пользователь {user.full_name} отклонен ❌",
            reply_markup=None,
        )
