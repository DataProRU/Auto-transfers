import asyncio
from aiogram import Bot, Dispatcher
from django.contrib.auth import get_user_model

from .config import BOT_TOKEN, ADMIN_GROUP_ID
from .handlers.admin_handlers import router as admin_router
from .keyboards.admin_keyboards import get_approval_keyboard

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(admin_router)

User = get_user_model()

async def send_registration_notification(user_id: int, email: str, full_name: str):
    """
    Отправляет уведомление о новой регистрации в группу администраторов
    """
    message_text = (
        f"📝 Новая регистрация!\n\n"
        f"👤 Пользователь: {full_name}\n"
        f"📧 Email: {email}\n"
    )
    
    await bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=message_text,
        reply_markup=get_approval_keyboard(user_id)
    )

async def start_bot():
    """Запускает бота"""
    await dp.start_polling(bot)

def run_bot():
    """Запускает бота в синхронном контексте"""
    asyncio.run(start_bot()) 