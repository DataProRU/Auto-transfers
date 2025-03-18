from rest_framework import serializers

from accounts.models.user import DocumentImage, User


class DocumentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentImage
        fields = ["id", "image", "created"]


class UserSerializer(serializers.ModelSerializer):
    documents = DocumentImageSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "phone",
            "telegram",
            "role",
            "is_approved",
            "is_onboarded",
            "documents",
        ]
