from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


class FileMaxSizeValidator:
    def __init__(self, max_size: int) -> None:
        self.max_size = max_size

    def __call__(self, value: UploadedFile) -> None:
        if value.size is not None and value.size > self.max_size:
            size_mb = f"{self.max_size / 1024 / 1024:.1f}"
            error_message = f"Размер файла не должен превышать {size_mb} МБ"
            raise ValidationError(error_message)
