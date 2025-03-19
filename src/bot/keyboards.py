"""Клавиатуры для Telegram бота."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_registration_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для подтверждения/отклонения регистрации.

    Args:
        user_id: ID пользователя для создания кнопок.

    Returns:
        InlineKeyboardMarkup: Клавиатура c кнопками подтверждения/отклонения.

    """
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=f"approve_{user_id}",
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject_{user_id}",
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
