from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Создает инлайн-клавиатуру с кнопками одобрения/отклонения регистрации"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=f"approve_user:{user_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"reject_user:{user_id}"
        )
    )
    return keyboard 