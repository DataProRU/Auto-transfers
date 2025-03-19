from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.serializers.user import UserSerializer
from accounts.validators import FileMaxSizeValidator
from autotrips.models.acceptance_report import AcceptenceReport, CarPhoto, DocumentPhoto, KeyPhoto
from project.settings import MAX_UPLOAD_SIZE

User = get_user_model()


class UserReportSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = AcceptenceReport
        fields = ("id", "vin", "model", "place", "status", "report_time")


class CarPhotoSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = CarPhoto
        fields = ("id", "photo", "created")


class KeyPhotoSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = KeyPhoto
        fields = ("id", "photo", "created")


class DocumentPhotoSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = DocumentPhoto
        fields = ("id", "photo", "created")


class AcceptanceReportSerializer(serializers.ModelSerializer[Any]):
    reporter = UserSerializer(read_only=True)
    car_photos = CarPhotoSerializer(many=True, read_only=True)
    key_photos = KeyPhotoSerializer(many=True, read_only=True)
    document_photos = DocumentPhotoSerializer(many=True, read_only=True)

    car_photos_upload = serializers.ListField(
        child=serializers.ImageField(
            validators=[
                FileMaxSizeValidator(MAX_UPLOAD_SIZE),
            ]
        ),
        write_only=True,
        required=False,
    )

    key_photos_upload = serializers.ListField(
        child=serializers.ImageField(
            validators=[
                FileMaxSizeValidator(MAX_UPLOAD_SIZE),
            ]
        ),
        write_only=True,
        required=False,
    )

    document_photos_upload = serializers.ListField(
        child=serializers.ImageField(
            validators=[
                FileMaxSizeValidator(MAX_UPLOAD_SIZE),
            ]
        ),
        write_only=True,
        required=False,
    )

    class Meta:
        model = AcceptenceReport
        fields = (
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
            "car_photos",
            "key_photos",
            "document_photos",
            "car_photos_upload",
            "key_photos_upload",
            "document_photos_upload",
        )
        read_only_fields = (
            "reporter",
            "report_number",
            "report_time",
            "acceptance_date",
            "car_photos",
            "key_photos",
            "document_photos",
        )

    def create(self, validated_data: dict[str, Any]) -> AcceptenceReport:
        uploaded_car_photos = validated_data.pop("car_photos_upload")
        uploaded_key_photos = validated_data.pop("key_photos_upload")
        uploaded_doc_photos = validated_data.pop("document_photos_upload")

        report = AcceptenceReport.objects.create(**validated_data)

        for car_photo in uploaded_car_photos:
            CarPhoto.objects.create(report=report, image=car_photo)

        for key_photo in uploaded_key_photos:
            KeyPhoto.objects.create(report=report, image=key_photo)

        for doc_photo in uploaded_doc_photos:
            DocumentPhoto.objects.create(report=report, image=doc_photo)

        return report

    def validate_photo_1(self, value: object) -> object:
        FileMaxSizeValidator(MAX_UPLOAD_SIZE)(value)
        return value

    def validate_photo_2(self, value: object) -> object:
        FileMaxSizeValidator(MAX_UPLOAD_SIZE)(value)
        return value

    def validate_photo_3(self, value: object) -> object:
        FileMaxSizeValidator(MAX_UPLOAD_SIZE)(value)
        return value
