from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AutotripsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "autotrips"
    verbose_name = _("Autotrips")

    def ready(self) -> None:
        import autotrips.signals  # noqa: F401
