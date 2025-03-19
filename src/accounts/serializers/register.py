from typing import Any

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.validators import FileExtensionValidator, RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from accounts.models.user import DocumentImage, User
from accounts.serializers.user import DocumentImageSerializer
from accounts.validators import FileMaxSizeValidator


class UserRegistrationSerializer(serializers.ModelSerializer[User]):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    documents = serializers.ListField(
        child=serializers.ImageField(
            validators=[FileMaxSizeValidator(getattr(settings, "MAX_UPLOAD_SIZE", 10 * 1024 * 1024))]
        ),
        write_only=True,
        required=True,
    )
    phone = serializers.CharField(
        required=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Number should be in format: '+79991234567'.",
            ),
            UniqueValidator(queryset=User.objects.all(), message=("user with this phone already exists")),
        ],
    )
    images = DocumentImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(
            allow_empty_file=False,
            use_url=False,
            validators=[
                FileMaxSizeValidator(getattr(settings, "MAX_UPLOAD_SIZE", 10 * 1024 * 1024)),
                FileExtensionValidator(["jpeg", "jpg", "png"]),
            ],
        ),
        write_only=True,
        required=True,
    )
    telegram = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message=("user with this telegram already exists"))],
    )

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "password2",
            "email",
            "full_name",
            "phone",
            "telegram",
            "role",
            "documents",
            "images",
            "uploaded_images",
        )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        documents = validated_data.pop("documents")
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)

        for document in documents:
            DocumentImage.objects.create(user=user, image=document)

        user.images = DocumentImage.objects.filter(user=user)
        return user
