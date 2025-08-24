from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin", _("Admin")
        MANAGER = "manager", _("Manager")
        USER = "user", _("User")
        CLIENT = "client", _("Client")
        LOGISTICIAN = "logistician", _("Logistician")
        OPENING_MANAGER = "opening_manager", _("Opening manager")
        TITLE = "title", _("Title")
        INSPECTOR = "inspector", _("Inspector")
        RE_EXPORT = "re_export", _("Re-Export")

    objects = CustomUserManager()

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("Username"),
        max_length=150,
        unique=True,
        help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
        null=True,
        blank=True,
    )
    full_name = models.CharField(_("Full name"), max_length=255, null=False, blank=False)
    phone = models.CharField(_("Phone"), max_length=15, unique=True, null=False, blank=False)
    telegram = models.CharField(_("Telegram"), max_length=32, unique=True, null=True, blank=True)
    address = models.CharField(_("Address"), max_length=255, null=True, blank=True)  # noqa: DJ001
    company = models.CharField(_("Company"), max_length=255, null=True, blank=True)  # noqa: DJ001
    tg_user_id = models.BigIntegerField(_("Telegram user ID"), unique=True, null=True, blank=True)
    role = models.CharField(_("Role"), max_length=15, choices=Roles.choices, default=Roles.USER)
    is_approved = models.BooleanField(_("Is approved"), default=False)
    is_onboarded = models.BooleanField(_("Is onboarded"), default=False)

    USERNAME_FIELD = "phone"  # auth using phone
    REQUIRED_FIELDS: list[str] = ["username"]

    def __str__(self) -> str:
        return str(self.full_name)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class DocumentImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents", verbose_name=_("User"))
    image = models.ImageField(_("Image"), upload_to="documents/%Y/%m/%d/")
    created = models.DateTimeField(_("Created"), default=timezone.now)

    def __str__(self) -> str:
        return f"{self.user.full_name}_image_{self.id}"

    class Meta:
        verbose_name = _("Document photo")
        verbose_name_plural = _("Documents photos")
