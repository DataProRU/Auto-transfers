"""Скрипт для запуска Telegram бота."""

import os

from config import DJANGO_SETTINGS_MODULE

os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)

from bot.bot import run_bot

if __name__ == "__main__":
    run_bot()
