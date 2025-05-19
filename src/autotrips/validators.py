from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from rest_framework.exceptions import ValidationError as DRFValidationError


class CustomRegexValidator:
    def __init__(self, regex: str, message: str | None = None, error_type: str | None = None) -> None:
        self.regex_validator = RegexValidator(regex=regex, message=message)
        self.error_type = error_type if error_type else "invalid"

    def __call__(self, value: str) -> None:
        try:
            self.regex_validator(value)
        except ValidationError as e:
            raise DRFValidationError({"message": e.message, "error_type": self.error_type}) from e
