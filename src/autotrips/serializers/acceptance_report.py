from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from accounts.validators import FileMaxSizeValidator
from autotrips.models.acceptance_report import AcceptenceReport, CarPhoto, DocumentPhoto, KeyPhoto

User = get_user_model()


class UserReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "phone", "telegram"]


class CarPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarPhoto
        fields = ["id", "image", "created"]


class KeyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyPhoto
        fields = ["id", "image", "created"]


class DocumentPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentPhoto
        fields = ["id", "image", "created"]


class AcceptanceReportSerializer(serializers.ModelSerializer):
    reporter = UserReportSerializer(read_only=True)
    car_photos = CarPhotoSerializer(many=True, read_only=True)
    uploaded_car_photos = serializers.ListField(
        child=serializers.ImageField(
            allow_empty_file=False,
            use_url=False,
            validators=[
                FileMaxSizeValidator(settings.MAX_UPLOAD_SIZE),
                FileExtensionValidator(["jpeg", "jpg", "png"]),
            ],
        ),
        write_only=True,
        required=True,
    )
    key_photos = KeyPhotoSerializer(many=True, read_only=True)
    uploaded_key_photos = serializers.ListField(
        child=serializers.ImageField(
            allow_empty_file=False,
            use_url=False,
            validators=[
                FileMaxSizeValidator(settings.MAX_UPLOAD_SIZE),
                FileExtensionValidator(["jpeg", "jpg", "png"]),
            ],
        ),
        write_only=True,
        required=True,
    )
    document_photos = DocumentPhotoSerializer(many=True, read_only=True)
    uploaded_document_photos = serializers.ListField(
        child=serializers.ImageField(
            allow_empty_file=False,
            use_url=False,
            validators=[
                FileMaxSizeValidator(settings.MAX_UPLOAD_SIZE),
                FileExtensionValidator(["jpeg", "jpg", "png"]),
            ],
        ),
        write_only=True,
        required=True,
    )

    class Meta:
        model = AcceptenceReport
        fields = [
            "id",
            "vin",
            "reporter",
            "model",
            "place",
            "comment",
            "report_number",
            "report_time",
            "acceptance_date",
            "status",
            "uploaded_car_photos",
            "uploaded_key_photos",
            "uploaded_document_photos",
            "car_photos",
            "key_photos",
            "document_photos",
        ]
        read_only_fields = ["report_number", "report_time", "acceptance_date"]

    def create(self, validated_data: dict[str, Any]) -> AcceptenceReport:
        uploaded_car_photos = validated_data.pop("uploaded_car_photos")
        uploaded_key_photos = validated_data.pop("uploaded_key_photos")
        uploaded_doc_photos = validated_data.pop("uploaded_document_photos")

        report = AcceptenceReport.objects.create(**validated_data)

        for car_photo in uploaded_car_photos:
            CarPhoto.objects.create(report=report, image=car_photo)

        for key_photo in uploaded_key_photos:
            KeyPhoto.objects.create(report=report, image=key_photo)

        for doc_photo in uploaded_doc_photos:
            DocumentPhoto.objects.create(report=report, image=doc_photo)

        return report
