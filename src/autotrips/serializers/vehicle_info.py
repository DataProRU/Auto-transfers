from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from accounts.serializers.user import ClientSerializer
from autotrips.models.vehicle_info import VehicleInfo, VehicleType
from autotrips.validators import CustomRegexValidator

User = get_user_model()


class VehicleInfoListSerializer(serializers.ListSerializer):
    def create(self, validated_data: dict[str, Any]) -> list[VehicleInfo]:
        vehicles = [VehicleInfo(**item) for item in validated_data]
        vehicles_idxs = {vehicle.client_id for vehicle in vehicles}
        vehicles_vins = {vehicle.vin for vehicle in vehicles}
        if len(vehicles_idxs) > 1:
            raise serializers.ValidationError({"non_field_error": "Can create multiply vehicles only for one client."})
        if len(vehicles_vins) < len(vehicles):
            raise serializers.ValidationError(
                {"vins_error": "It is not possible to create multiple vehicles with the same VINs."}
            )

        return VehicleInfo.objects.bulk_create(vehicles)  # type: ignore[no-any-return]

    def update(self, _: VehicleInfo, __: dict[str, Any]) -> None:
        pass


class VehicleInfoSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Roles.CLIENT), write_only=False, required=True
    )
    v_type = serializers.PrimaryKeyRelatedField(queryset=VehicleType.objects.all(), write_only=False, required=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)

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
            "status",
            "status_changed",
            "creation_time",
            "price",
        ]
        read_only_fields = [
            "status",
            "status_changed",
            "creation_time",
        ]
        extra_kwargs = {
            "arrival_date": {"error_messages": {"invalid": "Enter a valid date in YYYY-MM-DD format."}},
            "vin": {
                "validators": [
                    CustomRegexValidator(
                        regex=r"^[A-HJ-NPR-Z0-9]{17}$", message="Invalid VIN format.", error_type="vin_invalid"
                    ),
                    UniqueValidator(
                        queryset=VehicleInfo.objects.all(),
                        message={"message": "Vehicle with this VIN already exists.", "error_type": "vin_exists"},
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
        representation["v_type"] = VehicleTypeSerializer(instance.v_type).data
        return representation


class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ["id", "v_type"]
