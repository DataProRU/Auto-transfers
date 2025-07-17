from typing import Any

from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from accounts.serializers.user import ClientSerializer
from autotrips.models.vehicle_info import VehicleInfo
from autotrips.serializers.vehicle_info import VehicleTypeSerializer


class AdminVehicleBidSerialiser(serializers.ModelSerializer):
    client = ClientSerializer()
    v_type = VehicleTypeSerializer()

    class Meta:
        model = VehicleInfo
        fields = "__all__"


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Logistician Update",
            summary="How logisticians update vehicles",
            value={
                "transit_method": "t1",
                "location": "Some location",
                "requested_title": False,
                "notified_parking": False,
                "notified_inspector": False,
            },
            request_only=True,
            description="Logisticians can set transit method and location",
        ),
        OpenApiExample(
            "Manager Update",
            summary="How opening managers update vehicles",
            value={"openning_date": "2025-11-11", "opened": False, "manager_comment": "comment"},
            request_only=True,
            description="Managers can set openning date, opened and manager comment",
        ),
    ]
)
class BaseVehicleBidSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    v_type = VehicleTypeSerializer(read_only=True)

    always_read_only_fields = ["id", "vin", "brand", "model"]

    read_only_fields: list[str] = []
    required_fields: list[str] = []
    protected_fields: list[str] = []
    optional_fields: list[str] = []

    class Meta:
        model = VehicleInfo
        fields = "__all__"

    def __init__(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

        for field_name in self.always_read_only_fields:
            if field_name in self.fields:
                self.fields[field_name].read_only = True
        for field_name in self.read_only_fields:
            if field_name in self.fields:
                self.fields[field_name].read_only = True
        for field_name in self.required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
                self.fields[field_name].allow_null = False
        for field_name in self.optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False
                self.fields[field_name].allow_null = True

    def to_representation(self, instance: VehicleInfo) -> Any:  # noqa: ANN401
        rep = super().to_representation(instance)
        field_names = (
            set(self.always_read_only_fields)
            | set(self.read_only_fields)
            | set(self.required_fields)
            | set(self.protected_fields)
            | set(self.optional_fields)
        )
        return {k: v for k, v in rep.items() if k in field_names}

    def validate(self, attrs: dict[str, Any]) -> Any:  # noqa: ANN401
        if self.instance:
            for field_name in self.protected_fields:
                old_value = getattr(self.instance, field_name, None)
                new_value = attrs.get(field_name, old_value)
                if old_value and not new_value:
                    raise serializers.ValidationError(
                        {field_name: f"{field_name.replace('_', ' ').capitalize()} can't be unset once it was set."}
                    )
        return super().validate(attrs)


class LogisticianVehicleBidSerializer(BaseVehicleBidSerializer):
    read_only_fields = [
        "client",
        "container_number",
        "arrival_date",
        "openning_date",
        "transporter",
        "recipient",
        "approved_by_inspector",
        "approved_by_title",
        "approved_by_re_export",
    ]
    required_fields = ["transit_method", "requested_title", "notified_parking", "notified_inspector"]
    protected_fields = ["transit_method"]
    optional_fields = ["location"]

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        if "transit_method" in validated_data:
            old_value = instance.transit_method
            new_value = validated_data["transit_method"]
            if not old_value and new_value:
                validated_data["approved_by_logistician"] = True
        return super().update(instance, validated_data)


class ManagerVehicleBidSerializer(BaseVehicleBidSerializer):
    read_only_fields = [
        "client",
        "container_number",
        "arrival_date",
        "transporter",
        "recipient",
        "transit_method",
    ]
    required_fields = ["openning_date", "opened"]
    protected_fields = ["openning_date"]
    optional_fields = ["manager_comment"]

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        if "openning_date" in validated_data:
            old_value = instance.openning_date
            new_value = validated_data["openning_date"]
            if not old_value and new_value:
                validated_data["approved_by_manager"] = True
        return super().update(instance, validated_data)


def get_vehicle_bid_serializer(user_role: str) -> type[serializers.ModelSerializer]:
    role_serializers = {
        "logistician": LogisticianVehicleBidSerializer,
        "admin": AdminVehicleBidSerialiser,
        "opening_manager": ManagerVehicleBidSerializer,
    }
    return role_serializers.get(user_role, BaseVehicleBidSerializer)


class RejectBidSerializer(serializers.Serializer):
    logistician_comment = serializers.CharField(required=True, allow_blank=False)
