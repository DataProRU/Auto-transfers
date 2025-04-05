import asyncio
import logging
from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from asgiref.sync import async_to_sync
from django.conf import settings
from django.db.models.signals import post_save
from django.utils import timezone

from autotrips.models.acceptance_report import AcceptenceReport
from services.table_service import table_manager

logger = logging.getLogger(__name__)


class PostReportSaveSignalReciever:
    WORKSHEET = settings.REPORTS_WORKSHEET
    URL = settings.FRONTEND_URL

    def build_data_to_table(self, report: AcceptenceReport) -> list[str]:
        report_time_local = timezone.localtime(report.report_time)
        report_time = report_time_local.strftime("%d.%m.%Y %H:%M:%S")
        acceptance_date = report.acceptance_date.strftime("%d.%m.%Y")
        reporter = report.reporter
        car_photos = f"{self.URL}reports/{report.id}/car-photos"
        key_photos = f"{self.URL}reports/{report.id}/key-photos"
        doc_photos = f"{self.URL}reports/{report.id}/doc-photos"

        return [
            report_time,
            reporter.phone,
            reporter.full_name,
            report.report_number,
            acceptance_date,
            report.vin,
            report.model,
            car_photos,
            key_photos,
            doc_photos,
            report.place,
            report.comment,
            report.status,
        ]

    def build_telegram_message(self, report: AcceptenceReport) -> tuple[str, InlineKeyboardMarkup]:
        message = (
            "<b>🚗 Зарегистрировано повреждённое авто</b>\n"
            f"📅 Дата принятия: {report.acceptance_date.strftime('%d.%m.%Y')}\n"
            f"🔢 VIN номер: <code>{report.vin}</code>\n"
            f"📸 Ссылка на фото авто:\n"
            f"   <a href='{self.URL}reports/{report.id}/car-photos/'>{self.URL}reports/{report.id}/car-photos/</a>\n"
            f"🔑 Ссылка на фото ключей:\n"
            f"   <a href='{self.URL}reports/{report.id}/key-photos/'>{self.URL}reports/{report.id}/key-photos/</a>\n"
            f"📄 Ссылка на документы:\n"
            f"   <a href='{self.URL}reports/{report.id}/doc-photos/'>{self.URL}reports/{report.id}/doc-photos/</a>\n"
            f"📍 Местонахождение: {report.place}\n"
            f"💬 Комментарий: {report.comment}\n"
            f"👤 Приёмщик: {report.reporter.full_name}\n"
            f"📱 Телефон: {report.reporter.phone}\n"
            f"✉️ Telegram: @{report.reporter.telegram.lstrip('@')}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="Проработать",
                callback_data=f"process_report:{report.id}"
            )
        ]])

        return message, keyboard

    def send_telegram_notification(self, report: AcceptenceReport) -> None:
        """Отправка уведомления в Telegram"""
        from telegram_bot.bot import bot
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            message, keyboard = self.build_telegram_message(report)
            logger.info(f"Generated message: {message}")

            if loop.is_running():
                asyncio.create_task(
                    bot.send_message(
                        chat_id=settings.TELEGRAM_GROUP_CHAT_ID,
                        text=message,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                )
            else:
                loop.run_until_complete(
                    bot.send_message(
                        chat_id=settings.TELEGRAM_GROUP_CHAT_ID,
                        text=message,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                )
            logger.info("Уведомление отправлено успешно.")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def __call__(
            self,
            sender: AcceptenceReport,
            instance: AcceptenceReport,
            created: bool,  # noqa: FBT001
            **kwargs: dict[str, Any],
    ) -> None:
        if created:
            row = self.build_data_to_table(instance)
            table_manager.append_row(self.WORKSHEET, row)
            # Отправка в Telegram если авто повреждено
            if instance.status == AcceptenceReport.Statuses.FAILED:
                self.send_telegram_notification(instance)


reciever = PostReportSaveSignalReciever()
post_save.connect(receiver=reciever, sender=AcceptenceReport)
