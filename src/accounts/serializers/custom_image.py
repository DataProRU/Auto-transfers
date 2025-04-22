import io
from typing import Any

from django.core.files.base import ContentFile
from PIL import Image
from pillow_heif import register_heif_opener
from rest_framework import serializers

register_heif_opener()


class HEIFImageField(serializers.ImageField):
    def to_internal_value(self, data: Any) -> ContentFile:  # noqa: ANN401
        image = super().to_internal_value(data)

        if image.name.lower().endswith((".heif", ".heic")):
            try:
                with Image.open(image) as img:
                    converted_img = img
                    if img.mode != "RGB":
                        converted_img = img.convert("RGB")

                    output = io.BytesIO()
                    converted_img.save(output, format="JPEG", quality=95)
                    output.seek(0)

                    file_name = f"{image.name.split('.')[0]}.jpg"
                    image = ContentFile(output.read(), name=file_name)

            except Exception as e:
                msg = f"Failed to process HEIF image: {e!s}"
                raise serializers.ValidationError(msg) from e

        return image
