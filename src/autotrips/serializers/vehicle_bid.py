from typing import Any

from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from accounts.serializers.user import ClientSerializer
from autotrips.models.acceptance_report import AcceptenceReport
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
        OpenApiExample(
            "Title Update",
            summary="How titles update vehicles",
            value={
                "pickup_address": "Address",
                "took_title": "yes/no/consignment",
                "title_collection_date": "2025-11-11",
                "notified_logistician_by_title": True,
            },
            request_only=True,
            description="Title can set pickup address, took title and title collection date",
        ),
        OpenApiExample(
            "Inspector Update",
            value={
                "transit_number": "TN789012",
                "inspection_done": "yes/no/required_inspection/required_expertise",
                "number_sent": True,
                "inspection_paid": True,
                "inspection_date": "2024-06-15",
                "number_sent_date": "2024-06-16",
                "inspector_comment": "Updated inspection notes",
                "notified_logistician_by_inspector": True,
            },
            request_only=True,
            description="Inspector can set inspection data",
        ),
    ]
)
class BaseVehicleBidSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    v_type = VehicleTypeSerializer(read_only=True)

    always_read_only_fields = ["id", "vin", "brand", "model", "client"]

    read_only_fields: list[str] = []
    required_fields: list[str] = []
    protected_fields: list[str] = []
    optional_fields: list[str] = []

    class Meta:
        model = VehicleInfo
        fields = "__all__"

    def __init__(self, *args: tuple[Any], **kwargs: dict[str, Any]) -> None:  # noqa: C901
        super().__init__(*args, **kwargs)

        explicit_fields = (
            set(self.always_read_only_fields)
            | set(self.read_only_fields)
            | set(self.required_fields)
            | set(self.protected_fields)
            | set(self.optional_fields)
        )

        for field_name in list(self.fields):
            if field_name not in explicit_fields:
                self.fields.pop(field_name)

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
        "container_number",
        "arrival_date",
        "transporter",
        "recipient",
        "transit_method",
    ]
    required_fields = ["openning_date", "opened"]
    protected_fields = ["opened"]
    optional_fields = ["manager_comment"]

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        opened = validated_data.get("opened")
        if opened and not instance.opened:
            validated_data["approved_by_manager"] = True
        return super().update(instance, validated_data)


class TitleVehicleBidSerializer(BaseVehicleBidSerializer):
    read_only_fields = ["manager_comment", "transit_method"]
    required_fields = ["pickup_address", "notified_logistician_by_title"]
    protected_fields = ["pickup_address"]
    optional_fields = ["took_title", "title_collection_date"]

    def validate(self, attrs: dict[str, Any]) -> Any:  # noqa: ANN401
        took_title = attrs.get("took_title")
        title_collection_date = attrs.get("title_collection_date")
        if took_title in {VehicleInfo.TookTitle.YES, VehicleInfo.TookTitle.CONSIGNMENT} and not title_collection_date:
            raise serializers.ValidationError(
                {"title_collection_date": "Required if 'took_title' in the request body."}
            )

        return super().validate(attrs)

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        if instance.title_collection_date:
            raise serializers.ValidationError(
                {"detail": "Cannot update a bid that has already been completed (title collected)."}
            )

        new_title_date = validated_data.get("title_collection_date")
        notified_logistician_by_title = validated_data.get("notified_logistician_by_title")

        if new_title_date and not notified_logistician_by_title:
            raise serializers.ValidationError({"detail": "Cannot take title without logistician notification."})

        if new_title_date and not instance.title_collection_date:
            validated_data["approved_by_title"] = True

        return super().update(instance, validated_data)


class InspectorVehicleBidSerializer(BaseVehicleBidSerializer):
    read_only_fields = ["location", "transit_method"]
    required_fields = [
        "transit_number",
        "inspection_done",
        "number_sent",
        "inspection_paid",
        "notified_logistician_by_inspector",
    ]
    protected_fields = ["inspection_done"]
    optional_fields = ["inspection_date", "number_sent_date", "inspector_comment"]

    def validate(self, attrs: dict[str, Any]) -> Any:  # noqa: ANN401
        inspection_done = attrs.get("inspection_done")
        inspection_date = attrs.get("inspection_date")
        if inspection_done == VehicleInfo.InspectionDone.YES and not inspection_date:
            raise serializers.ValidationError({"inspection_date": "Required if 'inspection_done' is 'yes'."})

        number_sent = attrs.get("number_sent")
        number_sent_date = attrs.get("number_sent_date")
        if number_sent and not number_sent_date:
            raise serializers.ValidationError({"number_sent_date": "Required if 'number_sent' is true."})

        return super().validate(attrs)

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        new_inspection_date = validated_data.get("inspection_date")
        if new_inspection_date and not instance.inspection_date:
            validated_data["approved_by_inspector"] = True

        return super().update(instance, validated_data)

    def to_representation(self, instance: VehicleInfo) -> Any:  # noqa: ANN401
        response_data = super().to_representation(instance)
        acceptance_date = (
            AcceptenceReport.objects.filter(vin=instance.vin).values_list("acceptance_date", flat=True).last()
        )
        response_data["acceptance_date"] = acceptance_date
        return response_data


def get_vehicle_bid_serializer(user_role: str) -> type[serializers.ModelSerializer]:
    role_serializers = {
        "logistician": LogisticianVehicleBidSerializer,
        "admin": AdminVehicleBidSerialiser,
        "opening_manager": ManagerVehicleBidSerializer,
        "title": TitleVehicleBidSerializer,
        "inspector": InspectorVehicleBidSerializer,
    }
    return role_serializers.get(user_role, BaseVehicleBidSerializer)


class RejectBidSerializer(serializers.Serializer):
    logistician_comment = serializers.CharField(required=True, allow_blank=False)
