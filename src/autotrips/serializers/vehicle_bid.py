from typing import Any

from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from accounts.serializers.user import ClientSerializer
from autotrips.models.vehicle_info import VehicleInfo, VehicleTransporter
from autotrips.serializers.vehicle_info import VehicleTypeSerializer


class AdminVehicleBidSerialiser(serializers.ModelSerializer):
    client = ClientSerializer()
    v_type = VehicleTypeSerializer()

    class Meta:
        model = VehicleInfo
        fields = "__all__"


class VehicleTransporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleTransporter
        fields = "__all__"


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Logistician Initial Update",
            summary="How logisticians update vehicles",
            value={
                "transit_method": "t1",
                "acceptance_type": None,
                "location": "Some location",
                "requested_title": False,
                "notified_parking": False,
                "notified_inspector": False,
            },
            request_only=True,
            description="Logisticians can set transit method and location for initial vehicles."
            "Use X-Vehicle-Status: initial header.",
        ),
        OpenApiExample(
            "Logistician Loading Update",
            summary="How logisticians update vehicles",
            value={
                "logistician_keys_number": 1,
                "vehicle_transporter": 1,
            },
            request_only=True,
            description="Logisticians can set logistician keys number and vehicle transporter to mark vehicle"
            "as 'ready for receiver' for loading vehicles."
            "Use X-Vehicle-Status: loading header.",
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
        OpenApiExample(
            "ReExport Update",
            value={
                "export": True,
                "prepared_documents": True,
            },
            request_only=True,
            description="ReExport can set export and prepared documents",
        ),
        OpenApiExample(
            "Receiver Update",
            summary="How receivers update vehicles",
            value={
                "vehicle_arrival_date": "2025-12-01",
                "receive_vehicle": True,
                "receive_documents": True,
                "full_acceptance": False,
                "receiver_keys_number": 2,
            },
            request_only=True,
            description="Receiver can set vehicle arrival date, mark vehicle and documents as received, "
            "indicate full acceptance, and specify the number of keys received.",
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


class LogisticianInitialVehicleBidSerializer(BaseVehicleBidSerializer):
    read_only_fields = [
        "container_number",
        "arrival_date",
        "openning_date",
        "opened",
        "transporter",
        "recipient",
        "approved_by_inspector",
        "approved_by_title",
        "approved_by_re_export",
    ]
    required_fields = ["transit_method", "notified_parking", "notified_inspector"]
    protected_fields = ["transit_method", "requested_title"]
    optional_fields = ["location", "acceptance_type", "requested_title"]

    def validate(self, attrs: dict[str, Any]) -> Any:  # noqa: ANN401
        acceptance_type = attrs.get("acceptance_type")
        transit_method = attrs.get("transit_method")
        if transit_method == VehicleInfo.TransitMethod.WITHOUT_OPENNING and not acceptance_type:
            raise serializers.ValidationError(
                {"acceptance_type": "Required if 'transit_method' is 'without_openning'."}
            )

        requested_title = attrs.get("requested_title")
        if (
            transit_method == VehicleInfo.TransitMethod.WITHOUT_OPENNING
            and acceptance_type == VehicleInfo.AcceptanceType.WITH_RE_EXPORT
            and not requested_title
        ):
            raise serializers.ValidationError({"requested_title": "Required if 'acceptance_type' is 'with_re_export'."})

        return super().validate(attrs)

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        transit_method = validated_data.get("transit_method")
        requested_title = validated_data.get("requested_title")
        if transit_method and not instance.transit_method:
            validated_data["approved_by_logistician"] = True

        if (
            transit_method in {VehicleInfo.TransitMethod.T1, VehicleInfo.TransitMethod.RE_EXPORT}
            and instance.opened
            and not requested_title
        ):
            raise serializers.ValidationError(
                {"requested_title": "Required if 'transit_method' is 't1' or 're_export' and container was opened."}
            )
        return super().update(instance, validated_data)


class LogisticianLoadingVehicleBidSerializer(BaseVehicleBidSerializer):
    read_only_fields = [
        "container_number",
        "arrival_date",
        "openning_date",
        "transporter",
        "recipient",
        "transit_method",
        "location",
        "approved_by_inspector",
        "approved_by_title",
        "approved_by_re_export",
        "requested_title",
        "notified_parking",
        "notified_inspector",
        "v_type",
    ]
    required_fields = ["logistician_keys_number", "vehicle_transporter"]
    protected_fields = ["logistician_keys_number", "vehicle_transporter"]

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        if instance.logistician_keys_number and instance.vehicle_transporter and instance.approved_by_receiver:
            raise serializers.ValidationError(
                {"detail": "Cannot update a bid that has already been completed (approved by receiver)."}
            )

        if (instance.logistician_keys_number or validated_data.get("logistician_keys_number")) and (
            instance.vehicle_transporter or validated_data.get("vehicle_transporter")
        ):
            validated_data["ready_for_receiver"] = True
        return super().update(instance, validated_data)

    def to_representation(self, instance: VehicleInfo) -> Any:  # noqa: ANN401
        data = super().to_representation(instance)
        if instance.vehicle_transporter:
            data["vehicle_transporter"] = VehicleTransporterSerializer(instance.vehicle_transporter).data
        return data


class ManagerVehicleBidSerializer(BaseVehicleBidSerializer):
    read_only_fields = [
        "container_number",
        "arrival_date",
        "transporter",
        "recipient",
        "transit_method",
    ]
    required_fields = ["opened", "openning_date"]
    protected_fields = ["opened", "openning_date"]
    optional_fields = ["manager_comment"]

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        opened = validated_data.get("opened")
        openning_date = validated_data.get("openning_date")
        if all([opened, openning_date]) and not instance.approved_by_manager:
            validated_data["approved_by_manager"] = True
        return super().update(instance, validated_data)


class TitleVehicleBidSerializer(BaseVehicleBidSerializer):
    read_only_fields = ["manager_comment", "transit_method"]
    required_fields = ["took_title"]
    protected_fields = ["took_title"]
    optional_fields = ["pickup_address", "title_collection_date"]

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

        title_collection_date = validated_data.get("title_collection_date")
        if title_collection_date and not instance.title_collection_date:
            validated_data["approved_by_title"] = True

        return super().update(instance, validated_data)


class InspectorVehicleBidSerializer(BaseVehicleBidSerializer):
    read_only_fields = ["location", "transit_method"]
    required_fields = ["inspection_done"]
    protected_fields = ["inspection_done", "inspection_date"]
    optional_fields = [
        "inspection_date",
        "number_sent_date",
        "inspector_comment",
        "transit_number",
        "number_sent",
        "inspection_paid",
        "notified_logistician_by_inspector",
    ]

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
            instance.reports.order_by("-acceptance_date").values_list("acceptance_date", flat=True).first()
        )
        response_data["acceptance_date"] = acceptance_date
        return response_data


class ReExportVehicleBidSerializer(BaseVehicleBidSerializer):
    read_only_fields = ["transit_method", "recipient", "price", "title_collection_date"]
    protected_fields = ["export", "prepared_documents"]
    required_fields = ["export", "prepared_documents"]

    def validate(self, attrs: dict[str, Any]) -> Any:  # noqa: ANN401
        export = attrs.get("export")
        prepared_documents = attrs.get("prepared_documents")
        if export and not prepared_documents:
            raise serializers.ValidationError({"prepared_documents": "Cannot export without prepared documents."})
        return super().validate(attrs)

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        if instance.export:
            raise serializers.ValidationError({"detail": "Cannot update a vehicle that has already been exported."})

        export = validated_data.get("export")
        if export and not instance.export:
            validated_data["approved_by_re_export"] = True
        return super().update(instance, validated_data)


class ReceiverVehicleBidSerializer(BaseVehicleBidSerializer):
    vehicle_transporter = VehicleTransporterSerializer(read_only=True)

    read_only_fields = ["transit_method", "vehicle_transporter"]
    required_fields = [
        "vehicle_arrival_date",
        "receive_vehicle",
        "receive_documents",
        "full_acceptance",
        "receiver_keys_number",
    ]
    protected_fields = ["vehicle_arrival_date", "receiver_keys_number"]

    def update(self, instance: VehicleInfo, validated_data: dict[str, Any]) -> VehicleInfo:
        if instance.full_acceptance:
            raise serializers.ValidationError({"detail": "Cannot update a vehicle that has already been accept."})

        full_acceptance = validated_data.get("full_acceptance")
        if full_acceptance and not instance.full_acceptance:
            validated_data["approved_by_receiver"] = True
        return super().update(instance, validated_data)


def get_vehicle_bid_serializer(user_role: str, status: str | None) -> type[serializers.ModelSerializer]:
    if user_role == "logistician" and status:
        logistician_serializers = {
            "initial": LogisticianInitialVehicleBidSerializer,
            "loading": LogisticianLoadingVehicleBidSerializer,
        }
        return logistician_serializers.get(status, LogisticianInitialVehicleBidSerializer)

    role_serializers = {
        "logistician": LogisticianInitialVehicleBidSerializer,
        "admin": AdminVehicleBidSerialiser,
        "opening_manager": ManagerVehicleBidSerializer,
        "title": TitleVehicleBidSerializer,
        "inspector": InspectorVehicleBidSerializer,
        "re_export": ReExportVehicleBidSerializer,
        "user": ReceiverVehicleBidSerializer,
    }
    return role_serializers.get(user_role, BaseVehicleBidSerializer)


class RejectBidSerializer(serializers.Serializer):
    logistician_comment = serializers.CharField(required=True, allow_blank=False)
