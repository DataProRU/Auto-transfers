from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from accounts.models.user import DocumentImage, User
from accounts.validators import FileMaxSizeValidator
from project.settings import MAX_UPLOAD_SIZE


class DocumentImageSerializer(serializers.ModelSerializer[DocumentImage]):
    class Meta:
        model = DocumentImage
        fields = ("id", "image", "created")
        read_only_fields = ("id", "created")

    def validate_image(self, value: UploadedFile) -> UploadedFile:
        FileMaxSizeValidator(MAX_UPLOAD_SIZE)(value)
        return value


class UserSerializer(serializers.ModelSerializer[User]):
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
    documents = DocumentImageSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "password",
            "password2",
            "email",
            "full_name",
            "phone",
            "telegram",
            "role",
            "is_approved",
            "is_onboarded",
            "documents",
        )
        read_only_fields = ("id", "is_approved", "is_onboarded")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        validated_data.pop("password2")
        return User.objects.create_user(**validated_data)
