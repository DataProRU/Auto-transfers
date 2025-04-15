import re
from typing import Any

from django.conf import settings
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from accounts.models.user import DocumentImage, User
from accounts.serializers.user import DocumentImageSerializer
from accounts.validators import FileMaxSizeValidator, telegram_validator


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[
            RegexValidator(
                regex=re.compile(
                    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_\-+=<>?[\]{};:\/<>,.'\-_...])[A-Za-z\d!@#$%^&*()"
                    r"_\-+=<>?[\]{};:\/<>,.'\-_...]{6,20}$"
                ),
                message="password must contain at least one uppercase letter, one lowercase letter, one digit,"
                " and one special character",
            )
        ],
    )

    phone = serializers.CharField(
        required=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Number should be in format: '+79991234567'.",
            ),
            UniqueValidator(queryset=User.objects.all(), message=("User with this phone already exists.")),
        ],
    )
    images = DocumentImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(
            allow_empty_file=False,
            use_url=False,
            validators=[
                FileMaxSizeValidator(settings.MAX_UPLOAD_SIZE),
            ],
        ),
        write_only=True,
        required=True,
    )
    telegram = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message=("User with this telegram already exists.")),
            telegram_validator,
        ],
    )

    class Meta:
        model = User
        fields = (
            "id",
            "full_name",
            "phone",
            "telegram",
            "images",
            "uploaded_images",
            "password",
        )

    def create(self, validated_data: dict[str, Any]) -> User:
        uploaded_images = validated_data.pop("uploaded_images")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        for image in uploaded_images:
            DocumentImage.objects.create(user=user, image=image)

        user.images = DocumentImage.objects.filter(user=user)
        return user
