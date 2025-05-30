import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.exceptions import AiogramError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery as CallbackQueryType
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from accounts.models import User
from services.table_service import table_manager

URL = settings.FRONTEND_URL
WORKSHEET = settings.CHECKER_WORKSHEET
logger = logging.getLogger(__name__)

try:
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
except Exception as e:  # noqa: BLE001
    bot = None  # type: ignore[assignment]
    msg = f"Bot is disabled. Telegram bot configuration error: {e}"
    logger.warning(msg)

dp = Dispatcher()


class PasswordResetStates(StatesGroup):
    confirm_reset = State()
    enter_new_password = State()


def check_user_permission(user: User) -> None:
    if user.role not in [User.Roles.ADMIN, User.Roles.MANAGER]:
        raise PermissionError


def get_password_reset_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отменить сброс пароля")]],
        resize_keyboard=True,
        selective=True,
    )


def get_main_keyboard(user: User) -> ReplyKeyboardMarkup:
    """Генерирует клавиатуру на основе роли и статуса пользователя."""
    buttons = []

    # Кнопка только для админов и менеджеров
    # if user.role in [User.Roles.ADMIN, User.Roles.MANAGER]:
    #     buttons.append([KeyboardButton(text="Отправить тестовое сообщение в группу")])  # noqa: ERA001

    # Кнопка сброса пароля только при привязанном ID
    if user.tg_user_id:
        buttons.append([KeyboardButton(text="Сбросить пароль")])

    # Всегда показываем кнопку привязки если ID не привязан
    if not user.tg_user_id:
        buttons.append([KeyboardButton(text="Привязать Telegram ID")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, selective=True)


def get_unauthorized_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для непривязанных пользователей."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Привязать Telegram ID")]], resize_keyboard=True, selective=True
    )


@dp.message(CommandStart())
async def start_command(message: Message) -> None:
    """Обработчик команды /start с динамической клавиатурой."""
    try:
        # Пытаемся найти пользователя по привязанному ID
        user = await asyncio.to_thread(User.objects.get, tg_user_id=message.from_user.id)  # type: ignore[union-attr]
        keyboard = get_main_keyboard(user)
        await message.answer("Выберите действие:", reply_markup=keyboard)
    except User.DoesNotExist:
        # Пользователь не привязан - минимальная клавиатура
        keyboard = get_unauthorized_keyboard()
        await message.answer("🔑 Для начала работы привяжите свой Telegram ID:", reply_markup=keyboard)


@dp.message(F.text == "Отправить тестовое сообщение в группу")
async def send_test_message(message: Message) -> None:
    """Обработчик тестового сообщения с проверкой прав."""
    try:
        user = await asyncio.to_thread(User.objects.get, tg_user_id=message.from_user.id)  # type: ignore[union-attr]
        check_user_permission(user)

        await bot.send_message(chat_id=settings.TELEGRAM_GROUP_CHAT_ID, text="Бот работает! Это тестовое сообщение.")
        await message.answer("✅ Сообщение отправлено в группу!")

    except User.DoesNotExist:
        await message.answer("❌ Аккаунт не привязан!")
    except PermissionError:
        await message.answer("⛔ У вас недостаточно прав для этого действия!")


@dp.message(F.text == "Привязать Telegram ID")
async def bind_tg_user_id(message: Message) -> None:
    """Обработчик привязки Telegram ID."""
    try:
        # Ищем пользователя по telegram username
        user = await asyncio.to_thread(User.objects.get, telegram=message.from_user.username)  # type: ignore[union-attr]

        if user.tg_user_id:
            await message.answer("✅ Ваш аккаунт уже привязан!")
            return

        user.tg_user_id = message.from_user.id  # type: ignore[union-attr]
        await asyncio.to_thread(user.save)

        # Показываем обновленную клавиатуру
        await message.answer("✅ Аккаунт успешно привязан!", reply_markup=get_main_keyboard(user))

    except User.DoesNotExist:
        await message.answer("❌ Аккаунт не найден. Обратитесь к администратору.")
    except IntegrityError:
        await message.answer("❌ Этот Telegram ID уже привязан к другому аккаунту.")


@dp.message(F.text == "Сбросить пароль")
async def start_password_reset(message: Message, state: FSMContext) -> None:
    try:
        user = await asyncio.to_thread(User.objects.get, tg_user_id=message.from_user.id)  # type: ignore[union-attr]

        # Добавляем проверку привязки аккаунта через клавиатуру
        if not user.tg_user_id:
            await message.answer("❌ Сначала привяжите Telegram ID", reply_markup=get_main_keyboard(user))
            return

        await message.answer(
            "⚠️ Вы уверены, что хотите сбросить пароль?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Нет")]], resize_keyboard=True
            ),
        )
        await state.set_state(PasswordResetStates.confirm_reset)

    except User.DoesNotExist:
        await message.answer("❌ Аккаунт не привязан!", reply_markup=get_unauthorized_keyboard())


@dp.message(PasswordResetStates.confirm_reset, F.text.in_(["Да", "Нет"]))
async def handle_reset_confirmation(message: Message, state: FSMContext) -> None:
    user = await asyncio.to_thread(User.objects.get, tg_user_id=message.from_user.id)  # type: ignore[union-attr]

    if message.text == "Нет":
        await message.answer(
            "❌ Сброс пароля отменен.",
            reply_markup=get_main_keyboard(user) if user else get_unauthorized_keyboard(),
        )
        await state.clear()
        return

    await message.answer(
        "🔐 Введите новый пароль (минимум 8 символов, буквы и цифры):", reply_markup=get_password_reset_keyboard()
    )
    await state.set_state(PasswordResetStates.enter_new_password)


# Обработчик ввода нового пароля
@dp.message(PasswordResetStates.enter_new_password)
async def process_new_password(message: Message, state: FSMContext) -> None:
    user = await asyncio.to_thread(User.objects.get, tg_user_id=message.from_user.id)  # type: ignore[union-attr]

    if message.text == "Отменить сброс пароля":
        await message.answer(
            "❌ Сброс пароля отменен.",
            reply_markup=get_main_keyboard(user) if user else get_unauthorized_keyboard(),
        )
        await state.clear()
        return

    new_password = message.text.strip()  # type: ignore[union-attr]

    try:
        # Стандартная валидация пароля Django
        await asyncio.to_thread(validate_password, new_password, user=user)
    except ValidationError as e:
        # Преобразование стандартных ошибок в русские сообщения
        error_messages = []
        for error in e.error_list:
            if error.code == "password_too_short":
                error_messages.append("❌ Пароль должен содержать минимум 8 символов")
            elif error.code == "password_entirely_numeric":
                error_messages.append("❌ Пароль не может состоять только из цифр")
            elif error.code == "password_too_common":
                error_messages.append("❌ Пароль слишком распространён")
            elif error.code == "password_too_similar":
                error_messages.append("❌ Пароль слишком похож на ваши личные данные")
            else:
                error_messages.append(f"❌ {error.message}")

        await message.answer("\n".join(error_messages))
        return

    try:
        await asyncio.to_thread(user.set_password, new_password)
        await asyncio.to_thread(user.save)

        await message.answer("✅ Пароль успешно изменен!", reply_markup=get_main_keyboard(user))

    except Exception as e:
        msg = f"Password reset error: {e!s}"
        logger.exception(msg)
        await message.answer(
            "❌ Произошла ошибка при изменении пароля",
            reply_markup=get_main_keyboard(user) if user else get_unauthorized_keyboard(),
        )
    finally:
        await state.clear()


@dp.callback_query(F.data.startswith("accept:"))
async def accept_callback(callback_query: CallbackQueryType) -> None:
    try:
        user_id = int(callback_query.data.split(":")[1])  # type: ignore[union-attr]
        user = await asyncio.to_thread(User.objects.get, id=user_id)
        if not user.is_approved:
            clicker_telegram = callback_query.from_user.username
            try:
                clicker_user = await asyncio.to_thread(User.objects.get, telegram=clicker_telegram)
                if clicker_user.role in ["admin", "manager"]:
                    user.is_approved = True
                    accept_datetime = timezone.now().strftime("%Y-%m-%d %H:%M")
                    documents_url = f"Ссылка на документы: {URL}docs/{user.id}"
                    data = [accept_datetime, user.full_name, user.phone, user.telegram, documents_url]
                    table_manager.append_row(WORKSHEET, data)
                    await asyncio.to_thread(user.save)
                    await callback_query.answer()
                    await callback_query.message.edit_text(text="Пользователь принят")  # type: ignore[union-attr]
                else:
                    await callback_query.answer("У вас нет прав для выполнения этого действия")
            except User.DoesNotExist:
                await callback_query.answer("Вы не авторизованы для выполнения этого действия")
        else:
            await callback_query.answer("Пользователь уже принят")
    except Exception as e:  # noqa: BLE001
        await callback_query.answer(f"Ошибка при обработке запроса: {e}")


@dp.callback_query(F.data.startswith("reject:"))
async def reject_callback(callback_query: CallbackQueryType) -> None:
    try:
        user_id = int(callback_query.data.split(":")[1])  # type: ignore[union-attr]
        user = await asyncio.to_thread(User.objects.get, id=user_id)
        if user.is_active:
            clicker_telegram = callback_query.from_user.username
            try:
                clicker_user = await asyncio.to_thread(User.objects.get, telegram=clicker_telegram)
                if clicker_user.role in ["admin", "manager"]:
                    user.is_active = False
                    await asyncio.to_thread(user.save)
                    await callback_query.answer()
                    await callback_query.message.edit_text(text="Пользователь отклонен")  # type: ignore[union-attr]
                else:
                    await callback_query.answer("У вас нет прав для выполнения этого действия")
            except User.DoesNotExist:
                await callback_query.answer("Вы не авторизованы для выполнения этого действия")
        else:
            await callback_query.answer("Пользователь уже отклонен или неактивен")
    except Exception:  # noqa: BLE001
        await callback_query.answer("Ошибка при обработке запроса")


@dp.callback_query(F.data.startswith("process_report:"))
async def process_report_callback(callback: CallbackQueryType) -> None:
    """Handle report processing callback with proper error handling and user feedback."""
    try:
        if not callback.message or not isinstance(callback.message, Message):
            await callback.answer("❌ Сообщение не найдено")
            return

        user = await asyncio.to_thread(User.objects.get, tg_user_id=callback.from_user.id)

        try:
            check_user_permission(user)
        except PermissionError:
            await callback.answer("⛔ У вас недостаточно прав для этого действия!")
            return

        text = f"✅ {callback.message.text}\n\n🛠 *Обработал*: @{callback.from_user.username}"
        try:
            await callback.message.edit_text(text=text, parse_mode=ParseMode.MARKDOWN)
            await callback.answer()

        except AiogramError as e:
            if "can't parse entities" in str(e):
                await callback.message.edit_text(text=text, parse_mode=None)
                await callback.answer()
            else:
                raise

    except Exception:
        logger.exception("Error processing report callback")
        try:
            await callback.answer("❌ Ошибка обработки запроса")
        except Exception as answer_error:
            msg = f"Failed to send error answer: {answer_error}"
            logger.exception(msg)
