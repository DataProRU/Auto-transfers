from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin"
        MANAGER = "manager"
        USER = "user"

    full_name = models.CharField(max_length=255, null=False, blank=False)
    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.USER)
    phone = models.CharField(max_length=15, unique=True, null=False, blank=False)
    telegram = models.CharField(max_length=32, unique=True, null=False, blank=False)
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = "phone"  # auth using phone
    REQUIRED_FIELDS: list[str] = []

    username = None


class DocumentImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    image = models.ImageField(upload_to="documents/%Y/%m/%d/")

    def __str__(self) -> str:
        return f"{self.user.full_name}_image_{self.id}"
