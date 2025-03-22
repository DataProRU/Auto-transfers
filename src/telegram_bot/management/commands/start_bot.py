from django.core.management.base import BaseCommand

from telegram_bot.bot import bot, dp


class Command(BaseCommand):
    help = "Start the Telegram Bot"

    async def start_bot(self):
        await dp.start_polling(bot)

    def handle(self, *args, **options):
        import asyncio
        asyncio.run(self.start_bot())
