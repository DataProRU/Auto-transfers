from typing import Any

from rest_framework import serializers

from autotrips.models.vehicle_info import VehicleInfo


class BaseVehicleBidSerializer(serializers.ModelSerializer):
    always_read_only_fields = ["id", "vin", "brand", "model"]

    read_only_fields: list[str] = []
    required_fields: list[str] = []
    protected_fields: list[str] = []

    class Meta:
        model = VehicleInfo
        fields = "__all__"

    def __init__(self, _: tuple[Any], __: dict[str, Any]) -> None:
        super().__init__(_, __)

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

    def to_representation(self, instance: VehicleInfo) -> Any:  # noqa: ANN401
        rep = super().to_representation(instance)
        field_names = (
            set(self.always_read_only_fields)
            | set(self.read_only_fields)
            | set(self.required_fields)
            | set(self.protected_fields)
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
    required_fields = ["transit_method", "location", "requested_title", "notified_parking", "notified_inspector"]
    protected_fields = ["transit_method"]

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        if "transit_method" in validated_data:
            old_value = instance.transit_method
            new_value = validated_data["transit_method"]
            if not old_value and new_value:
                validated_data["approved_by_logistician"] = True
        return super().update(instance, validated_data)


def get_vehicle_info_serializer(user_role: str) -> type[BaseVehicleBidSerializer]:
    role_serializers = {
        "logistician": LogisticianVehicleBidSerializer,
    }
    return role_serializers.get(user_role, BaseVehicleBidSerializer)
