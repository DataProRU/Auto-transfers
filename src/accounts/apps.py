"""Django application configuration."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for accounts app."""

    name = "accounts"

    def ready(self) -> None:
        """Import signals when app is ready."""
        # Импортируем сигналы при загрузке приложения
