from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from telegram_bot.bot import bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from django.conf import settings

def build_keyboard(user_id: int) -> InlineKeyboardMarkup:
    accept_button = InlineKeyboardButton(
        text="Принять",
        callback_data=f"accept:{user_id}"
    )
    reject_button = InlineKeyboardButton(
        text="Отклонить",
        callback_data=f"reject:{user_id}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[accept_button, reject_button]])
    return keyboard

@receiver(post_save, sender=User)
def send_registration_notification(sender, instance: User, created: bool, **kwargs) -> None:
    if created:
        keyboard = build_keyboard(instance.id)
        text = f"Зарегистрирован новый приемщик:\n{instance.full_name}\n{instance.phone}\nСсылка на документы: api/v1/account/users/{instance.id}/documents"
        asyncio.run(bot.send_message(chat_id=settings.TELEGRAM_GROUP_CHAT_ID, text=text, reply_markup=keyboard))