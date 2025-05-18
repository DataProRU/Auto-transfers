from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.core.validators import RegexValidator
from rest_framework.exceptions import ValidationError as DRFValidationError


class FileMaxSizeValidator:
    def __init__(self, max_size: int) -> None:
        self.max_size = max_size

    def __call__(self, value: File) -> None:
        if value.size > self.max_size:
            msg = f"Maximum size {self.max_size} exceeded."
            raise ValidationError(msg)


class CustomRegexValidator:
    def __init__(self, regex: str, message: str | None = None, error_type: str | None = None) -> None:
        self.regex_validator = RegexValidator(regex=regex, message=message)
        self.error_type = error_type if error_type else "invalid"

    def __call__(self, value: str) -> None:
        try:
            self.regex_validator(value)
        except ValidationError as e:
            raise DRFValidationError({"message": e.message, "error_type": self.error_type}) from e
