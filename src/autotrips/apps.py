from django.apps import AppConfig


class AutotripsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "autotrips"

    def ready(self) -> None:
        import autotrips.signals  # noqa: F401
