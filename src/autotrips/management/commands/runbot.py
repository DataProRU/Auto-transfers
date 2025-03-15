from django.core.management.base import BaseCommand
from autotrips.bot.bot import run_bot

class Command(BaseCommand):
    help = 'Запускает Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Запуск Telegram бота...'))
        run_bot() 