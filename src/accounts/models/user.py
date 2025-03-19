from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone

from accounts.models.managers import CustomUserManager


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin", "Администратор"
        MANAGER = "manager", "Менеджер"
        DRIVER = "driver", "Водитель"

    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Обязательное поле. Не более 150 символов.",
        error_messages={
            "unique": "Пользователь с таким именем уже существует.",
        },
    )
    email = models.EmailField(
        unique=True,
        error_messages={
            "unique": "Пользователь с таким email уже существует.",
        },
    )
    phone = models.CharField(max_length=20, blank=True, default="")
    telegram = models.CharField(max_length=32, blank=True, default="")
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=Roles.choices)
    is_approved = models.BooleanField(default=False)
    is_onboarded = models.BooleanField(default=False)

    objects = CustomUserManager()

    username_validator = UnicodeUsernameValidator()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email", "full_name", "role"]

    def __str__(self) -> str:
        return self.full_name


class DocumentImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    image = models.ImageField(upload_to="documents/")
    created = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.user.full_name}_image_{self.pk}"
