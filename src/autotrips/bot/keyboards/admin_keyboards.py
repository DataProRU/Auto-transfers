"""Admin keyboards for Telegram bot."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with approve/reject buttons.

    Args:
        user_id: User ID to create buttons for

    Returns:
        InlineKeyboardMarkup: Keyboard with approve/reject buttons

    """
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Одобрить",
                callback_data=f"approve_user:{user_id}",
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject_user:{user_id}",
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
