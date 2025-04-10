from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.core.validators import RegexValidator


class FileMaxSizeValidator:
    def __init__(self, max_size: int) -> None:
        self.max_size = max_size

    def __call__(self, value: File) -> None:
        if value.size > self.max_size:
            msg = f"Maximum size {self.max_size} exceeded."
            raise ValidationError(msg)


telegram_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9_]{5,32}$",
    message="Telegram username must be 5-32 characters long, contain only letters, numbers and underscores.",
    code="invalid_telegram_username",
)
