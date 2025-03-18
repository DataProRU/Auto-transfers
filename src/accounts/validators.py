from django.core.exceptions import ValidationError
from django.core.files.base import File


class FileMaxSizeValidator:
    def __init__(self, max_size: int) -> None:
        self.max_size = max_size

    def __call__(self, value: File) -> None:
        if value.size > self.max_size:
            msg = f"Maximum size {self.max_size} exceeded."
            raise ValidationError(msg)
