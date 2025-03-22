import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery as CallbackQueryType
from aiogram.types import Message
from django.conf import settings

from accounts.models import User
from services.table_service import table_manager

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Тестовый обработчик команды /start
@dp.message(CommandStart())
async def start_command(message: Message):
    await bot.send_message(
        chat_id=settings.TELEGRAM_GROUP_CHAT_ID,
        text="Бот работает! Это тестовое сообщение."
    )
    await message.answer("Сообщение отправлено в группу!")

@dp.callback_query(F.data.startswith("accept:"))
async def accept_callback(callback_query: CallbackQueryType):
    try:
        user_id = int(callback_query.data.split(":")[1])
        user = await asyncio.to_thread(User.objects.get, id=user_id)
        if not user.is_approved:
            clicker_telegram = callback_query.from_user.username
            try:
                clicker_user = await asyncio.to_thread(User.objects.get, telegram=clicker_telegram)
                if clicker_user.role in ["admin", "manager"]:
                    user.is_approved = True
                    await asyncio.to_thread(user.save)
                    await callback_query.answer()
                    await callback_query.message.edit_text(text="Пользователь принят")

                    # Запись в Google таблицу
                    document_url = f"api/v1/account/users/{user_id}/documents"
                    table_manager.append_row("База приемщиков", [user.full_name, user.phone, user.telegram, document_url])
                else:
                    await callback_query.answer("У вас нет прав для выполнения этого действия")
            except User.DoesNotExist:
                await callback_query.answer("Вы не авторизованы для выполнения этого действия")
        else:
            await callback_query.answer("Пользователь уже принят")
    except:
        await callback_query.answer("Ошибка при обработке запроса")

@dp.callback_query(F.data.startswith("reject:"))
async def reject_callback(callback_query: CallbackQueryType):
    try:
        user_id = int(callback_query.data.split(":")[1])
        user = await asyncio.to_thread(User.objects.get, id=user_id)
        if user.is_active:
            clicker_telegram = callback_query.from_user.username
            try:
                clicker_user = await asyncio.to_thread(User.objects.get, telegram=clicker_telegram)
                if clicker_user.role in ["admin", "manager"]:
                    user.is_active = False
                    await asyncio.to_thread(user.save)
                    await callback_query.answer()
                    await callback_query.message.edit_text(text="Пользователь отклонен")
                else:
                    await callback_query.answer("У вас нет прав для выполнения этого действия")
            except User.DoesNotExist:
                await callback_query.answer("Вы не авторизованы для выполнения этого действия")
        else:
            await callback_query.answer("Пользователь уже отклонен или неактивен")
    except:
        await callback_query.answer("Ошибка при обработке запроса")
