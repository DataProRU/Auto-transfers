import asyncio
import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from telegram_bot.bot import bot

from .models import User

logger = logging.getLogger(__name__)

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
        logger.info(f"Создан новый пользователь: {instance.full_name}")
        keyboard = build_keyboard(instance.id)
        text = f"Зарегистрирован новый приемщик:\n{instance.full_name}\n{instance.phone}\nСсылка на документы: api/v1/account/users/{instance.id}/documents"
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                asyncio.create_task(
                    bot.send_message(chat_id=settings.TELEGRAM_GROUP_CHAT_ID, text=text, reply_markup=keyboard)
                )
            else:
                loop.run_until_complete(
                    bot.send_message(chat_id=settings.TELEGRAM_GROUP_CHAT_ID, text=text, reply_markup=keyboard)
                )
            logger.info("Уведомление отправлено успешно.")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")
