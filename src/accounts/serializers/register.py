import re
from typing import Any

from django.conf import settings
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from accounts.models.user import DocumentImage, User
from accounts.serializers.custom_image import HEIFImageField
from accounts.serializers.user import DocumentImageSerializer
from accounts.validators import CustomRegexValidator, FileMaxSizeValidator


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
            CustomRegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Number should be in format: '+79991234567'.",
                error_type="phone_invalid",
            ),
            UniqueValidator(
                queryset=User.objects.all(),
                message={"message": "User with this phone already exists.", "error_type": "phone_exists"},
            ),
        ],
    )
    images = DocumentImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=HEIFImageField(
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
            CustomRegexValidator(
                regex=r"^[a-zA-Z0-9_]{5,32}$",
                message="Telegram username must be 5-32 characters long, contain only letters, "
                "numbers and underscores.",
                error_type="telegram_invalid",
            ),
            UniqueValidator(
                queryset=User.objects.all(),
                message={"message": "User with this telegram already exists.", "error_type": "telegram_exists"},
            ),
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


class ClientRegistrationSerializer(serializers.ModelSerializer):
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
            CustomRegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Number should be in format: '+79991234567'.",
                error_type="phone_invalid",
            ),
            UniqueValidator(
                queryset=User.objects.all(),
                message={"message": "Client with this phone already exists.", "error_type": "phone_exists"},
            ),
        ],
    )
    telegram = serializers.CharField(
        required=True,
        validators=[
            CustomRegexValidator(
                regex=r"^[a-zA-Z0-9_]{5,32}$",
                message="Telegram username must be 5-32 characters long, contain only letters, "
                "numbers and underscores.",
                error_type="telegram_invalid",
            ),
            UniqueValidator(
                queryset=User.objects.all(),
                message={"message": "Client with this telegram already exists.", "error_type": "telegram_exists"},
            ),
        ],
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message={"message": "Client with this email already exists.", "error_type": "email_exists"},
            ),
        ],
    )
    address = serializers.CharField(max_length=255, required=True)

    class Meta:
        model = User
        fields = (
            "id",
            "full_name",
            "phone",
            "telegram",
            "company",
            "address",
            "email",
            "password",
        )

    def create(self, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.role = User.Roles.CLIENT
        user.is_approved = True
        user.is_onboarded = True
        user.set_password(password)
        user.save()
        return user
