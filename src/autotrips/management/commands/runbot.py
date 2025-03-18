"""Command to run Telegram bot."""

from typing import Any

from django.core.management.base import BaseCommand

from autotrips.bot.bot import run_bot


class Command(BaseCommand):
    """Command to run Telegram bot."""

    help = "Запускает Telegram бота"

    def handle(self, *args: tuple[Any, ...], **options: dict[str, Any]) -> None:
        """
        Handle the command.

        Args:
            *args: Additional arguments
            **options: Additional options

        """
        self.stdout.write(self.style.SUCCESS("Запуск Telegram бота..."))
        run_bot()
