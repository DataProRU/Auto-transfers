from typing import Any

from django.core.management.base import BaseCommand

from telegram_bot.bot import bot, dp


class Command(BaseCommand):
    help = "Start the Telegram Bot"

    async def start_bot(self) -> None:
        await dp.start_polling(bot)

    def handle(self, *args: tuple[Any], **options: dict[str, Any]) -> None:
        import asyncio

        asyncio.run(self.start_bot())
