from typing import Any

from django.conf import settings
from django.core.validators import FileExtensionValidator, RegexValidator
from rest_framework import serializers
from validators import FileMaxSizeValidator

from accounts.models.user import User, DocumentImage


class DocumentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentImage
        fields = "__all__"


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    phone = serializers.CharField(
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Номер телефона должен быть в формате: '+79991234567'.",
            )
        ]
    )
    images = DocumentImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(
            allow_empty_file=False,
            use_url=False,
            validators=[
                FileMaxSizeValidator(settings.MAX_UPLOAD_SIZE),
                FileExtensionValidator(["jpeg", "jpg", "png"]),
            ],
        ),
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            "full_name",
            "phone",
            "telegram",
            "images",
            "uploaded_images",
            "password",
        )

    def create(self, validated_data: dict[str, Any]) -> User:
        uploaded_images = validated_data.pop("uploaded_images")
        user = User.objects.create(**validated_data)

        for image in uploaded_images:
            DocumentImage.objects.create(user=user, image=image)

        return user
