import asyncio
from aiogram import Bot, Dispatcher
from django.contrib.auth import get_user_model
from django.conf import settings

from .config import BOT_TOKEN, ADMIN_GROUP_ID, ADMIN_URL
from .handlers.admin_handlers import router as admin_router
from .keyboards.admin_keyboards import get_approval_keyboard

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(admin_router)

User = get_user_model()

async def send_registration_notification(user_id: int):
    """
    Отправляет уведомление о новой регистрации в группу администраторов
    """
    user = User.objects.get(id=user_id)
    documents_url = f"{ADMIN_URL}accounts/documentimage/?user__id__exact={user_id}"
    
    message_text = (
        f"📝 Зарегистрирован новый приёмщик:\n\n"
        f"👤 ФИО: {user.full_name}\n"
        f"📱 Телефон: {user.phone}\n"
        f"🔗 <a href='{documents_url}'>Документы, подтверждающие личность</a>"
    )
    
    await bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=message_text,
        reply_markup=get_approval_keyboard(user_id),
        parse_mode="HTML"
    )

async def start_bot():
    """Запускает бота"""
    await dp.start_polling(bot)

def run_bot():
    """Запускает бота в синхронном контексте"""
    asyncio.run(start_bot()) 