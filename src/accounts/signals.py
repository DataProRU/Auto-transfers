import asyncio
import logging
from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User

logger = logging.getLogger(__name__)


def build_keyboard(user_id: int) -> InlineKeyboardMarkup:
    accept_button = InlineKeyboardButton(text="Принять", callback_data=f"accept:{user_id}")
    reject_button = InlineKeyboardButton(text="Отклонить", callback_data=f"reject:{user_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[accept_button, reject_button]])


@receiver(post_save, sender=User)
def send_registration_notification(sender: User, instance: User, created: bool, **kwargs: dict[Any, str]) -> None:  # noqa: ARG001, FBT001
    from telegram_bot.bot import bot
    URL = settings.FRONTEND_URL
    if created:
        msg = f"Создан новый пользователь: {instance.full_name}"
        logger.info(msg)
        keyboard = build_keyboard(instance.id)
        documents_url = f"Ссылка на документы: {URL}/docs/{instance.id}"
        text = f"Зарегистрирован новый приемщик:\n{instance.full_name}\n{instance.phone}\n{documents_url}"
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                asyncio.create_task(  # noqa: RUF006
                    bot.send_message(
                        chat_id=settings.TELEGRAM_GROUP_CHAT_ID,
                        text=text,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                )
            else:
                loop.run_until_complete(
                    bot.send_message(
                        chat_id=settings.TELEGRAM_GROUP_CHAT_ID,
                        text=text,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                )
            logger.info("Уведомление отправлено успешно.")
        except Exception as e:
            msg = f"Ошибка при отправке уведомления: {e}"
            logger.exception(msg)
