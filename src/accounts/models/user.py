from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin"
        MANAGER = "manager"
        USER = "user"
        CLIENT = "client"

    objects = CustomUserManager()

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
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
    full_name = models.CharField(max_length=255, null=False, blank=False)
    phone = models.CharField(max_length=15, unique=True, null=False, blank=False)
    telegram = models.CharField(max_length=32, unique=True, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, default="")
    company = models.CharField(max_length=255, blank=True, default="")
    tg_user_id = models.BigIntegerField(unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.USER)
    is_approved = models.BooleanField(default=False)
    is_onboarded = models.BooleanField(default=False)

    USERNAME_FIELD = "phone"  # auth using phone
    REQUIRED_FIELDS: list[str] = ["username"]

    def __str__(self) -> str:
        return str(self.full_name)


class DocumentImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    image = models.ImageField(upload_to="documents/%Y/%m/%d/")
    created = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.user.full_name}_image_{self.id}"
