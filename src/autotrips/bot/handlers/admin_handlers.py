from aiogram import Router, F
from aiogram.types import CallbackQuery
from django.contrib.auth import get_user_model

router = Router()
User = get_user_model()

@router.callback_query(F.data.startswith("approve_user:"))
async def approve_user(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    user = User.objects.get(id=user_id)
    user.is_approved = True
    user.is_active = True
    user.save()
    
    await callback.message.edit_text(
        f"✅ Приёмщик {user.full_name} был успешно добавлен.",
        reply_markup=None
    )
    await callback.answer("Приёмщик добавлен")

@router.callback_query(F.data.startswith("reject_user:"))
async def reject_user(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    user = User.objects.get(id=user_id)
    user.delete()
    
    await callback.message.edit_text(
        f"❌ Приёмщик {user.full_name} был отклонен.",
        reply_markup=None
    )
    await callback.answer("Приёмщик отклонен") 