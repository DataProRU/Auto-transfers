from datetime import UTC, date, datetime
from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from autotrips.models.vehicle import VehicleInfo, VehicleType

User = get_user_model()


class VehicleInfoListSerializer(serializers.ListSerializer):
    def create(self, validated_data: dict[str, Any]) -> list[VehicleInfo]:
        vehicles = [VehicleInfo(**item) for item in validated_data]
        return VehicleInfo.objects.bulk_create(vehicles)  # type: ignore[no-any-return]

    def update(self, _: VehicleInfo, __: dict[str, Any]) -> None:
        pass


class VehicleInfoSerializer(serializers.ModelSerializer):
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Roles.CLIENT), source="client", write_only=True
    )
    client_name = serializers.CharField(source="client.full_name", read_only=True)
    v_type_id = serializers.PrimaryKeyRelatedField(queryset=VehicleType.objects.all(), source="v_type", write_only=True)
    v_type_name = serializers.CharField(source="v_type.v_type", read_only=True)

    class Meta:
        model = VehicleInfo
        fields = [
            "id",
            "client_id",
            "client_name",
            "brand",
            "model",
            "v_type_id",
            "v_type_name",
            "vin",
            "container_number",
            "arrival_date",
            "transporter",
            "recipient",
            "comment",
            "status",
            "status_changed",
            "creation_time",
        ]
        read_only_fields = [
            "client_name",
            "v_type_name",
            "status",
            "status_changed",
            "creation_time",
        ]
        extra_kwargs = {"arrival_date": {"error_messages": {"invalid": "Enter a valid date in YYYY-MM-DD format"}}}
        list_serializer_class = VehicleInfoListSerializer

    def validate_arrival_date(self, value: date) -> date:
        if value < datetime.now(UTC).date():
            raise serializers.ValidationError("Arrival date cannot be in the past")
        return value
