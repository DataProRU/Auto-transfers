import asyncio
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from autotrips.bot.bot import send_registration_notification

User = get_user_model()

@receiver(post_save, sender=User)
def notify_admins_about_registration(sender, instance, created, **kwargs):
    """
    Отправляет уведомление администраторам при создании нового пользователя
    """
    if created and instance.role == User.Roles.USER:  # Только при создании нового приёмщика
        # Запускаем асинхронную функцию в синхронном контексте
        asyncio.run(send_registration_notification(user_id=instance.id)) 