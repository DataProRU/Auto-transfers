from typing import Any

import pandas as pd
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from accounts.serializers.custom_image import HEIFImageField
from accounts.serializers.user import ClientSerializer
from accounts.validators import FileMaxSizeValidator
from autotrips.models.vehicle_info import VehicleDocumentPhoto, VehicleInfo, VehicleType

User = get_user_model()


class VehicleInfoListSerializer(serializers.ListSerializer):
    def validate(self, attrs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not attrs:
            return attrs

        client_ids = {vehicle_data.get("client") for vehicle_data in attrs}
        if len(client_ids) > 1:
            raise serializers.ValidationError(
                {"non_field_error": _("Can create multiply vehicles only for one client.")}
            )

        vins = [vehicle_data.get("vin") for vehicle_data in attrs]
        if len(vins) != len(set(vins)):
            raise serializers.ValidationError(
                {"vins_error": _("It is not possible to create multiple vehicles with the same VINs.")}
            )

        return attrs

    def create(self, validated_data: list[dict[str, Any]]) -> list[VehicleInfo]:
        vehicle_photos_data = []
        for vehicle in validated_data:
            photos = vehicle.pop("uploaded_document_photos", [])
            vehicle_photos_data.append(photos)

        vehicles = [VehicleInfo(**item) for item in validated_data]
        created_vehicles = VehicleInfo.objects.bulk_create(vehicles)

        vehicle_photos_to_create = [
            VehicleDocumentPhoto(vehicle=vehicle, image=photo)
            for vehicle, photos in zip(created_vehicles, vehicle_photos_data, strict=False)
            for photo in photos
        ]

        if vehicle_photos_to_create:
            VehicleDocumentPhoto.objects.bulk_create(vehicle_photos_to_create)

        return created_vehicles  # type: ignore[no-any-return]

    def update(self, _: VehicleInfo, __: dict[str, Any]) -> None:
        pass


class VehicleDocumentPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleDocumentPhoto
        fields = ["id", "image", "created"]


class VehicleInfoSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Roles.CLIENT), write_only=False, required=True
    )
    v_type = serializers.PrimaryKeyRelatedField(
        queryset=VehicleType.objects.all(), write_only=False, required=False, allow_null=True
    )
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    document_photos = VehicleDocumentPhotoSerializer(many=True, read_only=True)
    uploaded_document_photos = serializers.ListField(
        child=HEIFImageField(
            allow_empty_file=False,
            use_url=False,
            validators=[
                FileMaxSizeValidator(settings.MAX_UPLOAD_SIZE),
            ],
        ),
        write_only=True,
        required=False,
    )
    remove_document_photo_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = VehicleInfo
        fields = [
            "id",
            "client",
            "year_brand_model",
            "v_type",
            "vin",
            "container_number",
            "arrival_date",
            "transporter",
            "recipient",
            "comment",
            "document_photos",
            "uploaded_document_photos",
            "remove_document_photo_ids",
            "status",
            "status_changed",
            "creation_time",
            "price",
        ]
        read_only_fields = [
            "id",
            "status",
            "status_changed",
            "creation_time",
        ]
        extra_kwargs = {
            "arrival_date": {"error_messages": {"invalid": _("Enter a valid date in YYYY-MM-DD format.")}},
            "vin": {
                "validators": [
                    UniqueValidator(
                        queryset=VehicleInfo.objects.all(),
                        message={"message": _("Vehicle with this VIN already exists."), "error_type": "vin_exists"},
                    ),
                ]
            },
        }
        list_serializer_class = VehicleInfoListSerializer

    # def validate_arrival_date(self, value: date) -> date:  noqa: ERA001 (for the future)
    #     if value < datetime.now(UTC).date():
    #         raise serializers.ValidationError("Arrival date cannot be in the past")  noqa: ERA001
    #     return value  noqa: ERA001

    def to_representation(self, instance: VehicleInfo) -> Any:  # noqa: ANN401
        representation = super().to_representation(instance)
        representation["client"] = ClientSerializer(instance.client).data
        representation["v_type"] = VehicleTypeSerializer(instance.v_type).data if instance.v_type else None
        return representation

    def create(self, validated_data: dict[str, Any]) -> VehicleInfo:
        document_photos = validated_data.pop("uploaded_document_photos", [])
        vehicle = super().create(validated_data)

        for document_photo in document_photos:
            VehicleDocumentPhoto.objects.create(vehicle=vehicle, image=document_photo)

        return vehicle

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        remove_photo_ids = validated_data.pop("remove_document_photo_ids", [])
        if remove_photo_ids:
            VehicleDocumentPhoto.objects.filter(id__in=remove_photo_ids, vehicle=instance).delete()

        document_photos = validated_data.pop("uploaded_document_photos", [])
        for document_photo in document_photos:
            VehicleDocumentPhoto.objects.create(vehicle=instance, image=document_photo)

        return super().update(instance, validated_data)


class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ["id", "v_type"]


class VehicleExcelUploadSerializer(serializers.Serializer):
    COLUMN_YEAR_BRAND_MODEL = "Год Марка Модель"
    COLUMN_VIN = "VIN"

    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role=User.Roles.CLIENT), required=True)
    excel_file = serializers.FileField(
        required=True,
        validators=[
            FileMaxSizeValidator(settings.MAX_UPLOAD_SIZE),
        ],
    )

    def validate_excel_file(self, value: UploadedFile) -> UploadedFile:
        if not value.name.lower().endswith((".xlsx", ".xls")):
            raise serializers.ValidationError(_("File must be an Excel file (.xlsx or .xls)"))

        try:
            excel_df = pd.read_excel(value, engine="openpyxl" if value.name.endswith(".xlsx") else None)
        except pd.errors.EmptyDataError as exc:
            raise serializers.ValidationError(_("Excel file is empty")) from exc
        except Exception as exc:
            raise serializers.ValidationError(_("Error reading Excel file: %(error)s") % {"error": str(exc)}) from exc

        required_columns = [self.COLUMN_YEAR_BRAND_MODEL, self.COLUMN_VIN]
        missing_columns = [col for col in required_columns if col not in excel_df.columns]

        if missing_columns:
            raise serializers.ValidationError(
                _("Excel file is missing required columns: %(columns)s") % {"columns": ", ".join(missing_columns)}
            )

        if excel_df.empty:
            raise serializers.ValidationError(_("Excel file contains no data"))

        return value

    def create(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        client = validated_data["client"]
        excel_file = validated_data["excel_file"]

        excel_df = self._read_excel(excel_file)

        vehicles_to_create, validation_errors = self._prepare_vehicles(excel_df, client)
        if validation_errors:
            raise serializers.ValidationError({"errors": validation_errors})

        db_errors = self._check_existing_vins(vehicles_to_create)
        if db_errors:
            raise serializers.ValidationError({"errors": db_errors})

        return self._bulk_create_vehicles(vehicles_to_create)

    def _read_excel(self, excel_file: UploadedFile) -> pd.DataFrame:
        return pd.read_excel(excel_file, engine="openpyxl" if excel_file.name.endswith(".xlsx") else None)

    def _prepare_vehicles(
        self, df: pd.DataFrame, client: AbstractUser
    ) -> tuple[list[VehicleInfo], list[dict[str, Any]]]:
        vehicles_to_create: list[VehicleInfo] = []
        vins_in_file: set[str] = set()
        validation_errors: list[dict[str, Any]] = []

        for index, row in df.iterrows():
            row_num = index + 2  # +2 because Excel rows start at 1 and have header
            try:
                raw_year_brand_model = row[self.COLUMN_YEAR_BRAND_MODEL]
                raw_vin = row[self.COLUMN_VIN]

                year_brand_model = "" if pd.isna(raw_year_brand_model) else str(raw_year_brand_model).strip()
                vin = "" if pd.isna(raw_vin) else str(raw_vin).strip()

                if not year_brand_model:
                    validation_errors.append(
                        {
                            "row": row_num,
                            "vin": vin or "N/A",
                            "error": _("year_brand_model cannot be empty"),
                        }
                    )
                    continue

                if not vin:
                    validation_errors.append(
                        {
                            "row": row_num,
                            "vin": "N/A",
                            "error": _("VIN cannot be empty"),
                        }
                    )
                    continue

                if vin in vins_in_file:
                    validation_errors.append(
                        {
                            "row": row_num,
                            "vin": vin,
                            "error": _("Duplicate VIN within file: %s") % vin,
                        }
                    )
                    continue

                vins_in_file.add(vin)
                vehicles_to_create.append(
                    VehicleInfo(
                        client=client,
                        year_brand_model=year_brand_model,
                        vin=vin,
                    )
                )

            except Exception as e:  # noqa: BLE001
                validation_errors.append(
                    {"row": row_num, "vin": str(row.get("vin", "N/A")), "error": _("Data processing error: %s") % e}
                )

        return vehicles_to_create, validation_errors

    def _check_existing_vins(self, vehicles_to_create: list[VehicleInfo]) -> list[dict[str, Any]]:
        existing_vins = set(
            VehicleInfo.objects.filter(vin__in=[v.vin for v in vehicles_to_create]).values_list("vin", flat=True)
        )

        if not existing_vins:
            return []

        db_errors: list[dict[str, Any]] = [
            {"row": "N/A", "vin": vehicle.vin, "error": _("VIN already exists in database: %s") % vehicle.vin}
            for vehicle in vehicles_to_create
            if vehicle.vin in existing_vins
        ]

        return db_errors

    def _bulk_create_vehicles(self, vehicles_to_create: list[VehicleInfo]) -> dict[str, Any]:
        try:
            created_vehicles = VehicleInfo.objects.bulk_create(vehicles_to_create)

            return {
                "created_count": len(created_vehicles),
                "errors": [],
                "vehicles": VehicleInfoSerializer(created_vehicles, many=True).data,
            }

        except Exception as e:
            raise serializers.ValidationError(
                {"errors": [{"row": "N/A", "vin": "N/A", "error": _("Bulk create failed: %s") % e}]}
            ) from e
