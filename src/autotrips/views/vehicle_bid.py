from typing import Any

from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from autotrips.models.vehicle_info import VehicleInfo
from autotrips.serializers.vehicle_bid import (
    LogisticianVehicleBidSerializer,
    get_vehicle_bid_serializer,
)
from project.permissions import VehicleBidAccessPermission

User = get_user_model()


LOGISTICIAN_GROUPS = {
    "initial": {
        "untouched": {"approved_by_logistician": False},
        "in_progress": {"approved_by_logistician": True},
    },
}


@extend_schema_view(
    list=extend_schema(
        summary="List vehicle bids (admin: flat list, logistician: grouped)",
        description="Admins receive a flat list of all vehicle bids. Logisticians receive grouped bids by status"
        " and approval. The 'status' query parameter is required for logisticians.",
        parameters=[
            OpenApiParameter(
                name="status",
                description="Vehicle status to filter by (e.g., 'initial'). Required for logisticians.",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample("Initial", value="initial"),
                    OpenApiExample("Loading", value="loading"),
                    OpenApiExample("Transport", value="ready_for_transport"),
                    OpenApiExample("Approve", value="requires_approval"),
                ],
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Flat list for admin or grouped for logistician.",
                response=LogisticianVehicleBidSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Admin flat list",
                        value=[
                            {
                                "id": 1,
                                "vin": "1HGCM82633A004352",
                                "brand": "Honda",
                                "model": "Accord",
                                "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                                "v_type": {"id": 1, "name": "Sedan"},
                                "container_number": "CONT1234567",
                                "arrival_date": "2024-06-01",
                                "openning_date": "2024-06-02",
                                "transporter": "TransCo",
                                "recipient": "Jane Smith",
                                "approved_by_inspector": False,
                                "approved_by_title": False,
                                "approved_by_re_export": False,
                                "transit_method": "t1",
                                "location": "Warehouse 1",
                                "requested_title": True,
                                "notified_parking": True,
                                "notified_inspector": False,
                                "logistician_comment": "Urgent",
                                "approved_by_logistician": True,
                                "status": "loading",
                                "status_changed": "2024-06-01T12:00:00Z",
                            },
                        ],
                    ),
                    OpenApiExample(
                        "Logistician grouped list",
                        value={
                            "untouched": [
                                {
                                    "id": 1,
                                    "vin": "1HGCM82633A004352",
                                    "brand": "Honda",
                                    "model": "Accord",
                                    "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                                    "v_type": {"id": 1, "name": "Sedan"},
                                    "container_number": "CONT1234567",
                                    "arrival_date": "2024-06-01",
                                    "openning_date": "2024-06-02",
                                    "transporter": "TransCo",
                                    "recipient": "Jane Smith",
                                    "approved_by_inspector": False,
                                    "approved_by_title": False,
                                    "approved_by_re_export": False,
                                    "transit_method": "t1",
                                    "location": "Warehouse 1",
                                    "requested_title": True,
                                    "notified_parking": True,
                                    "notified_inspector": False,
                                    "logistician_comment": "Urgent",
                                    "approved_by_logistician": False,
                                    "status": "initial",
                                    "status_changed": "2024-06-01T12:00:00Z",
                                },
                            ],
                            "in_progress": [
                                {
                                    "id": 2,
                                    "vin": "2HGCM82633A004353",
                                    "brand": "Toyota",
                                    "model": "Camry",
                                    "client": {"id": 3, "full_name": "Jane Smith", "email": "jane@example.com"},
                                    "v_type": {"id": 2, "name": "Sedan"},
                                    "container_number": "CONT7654321",
                                    "arrival_date": "2024-06-03",
                                    "openning_date": "2024-06-04",
                                    "transporter": "MoveIt",
                                    "recipient": "John Doe",
                                    "approved_by_inspector": True,
                                    "approved_by_title": False,
                                    "approved_by_re_export": False,
                                    "transit_method": "re_export",
                                    "location": "Warehouse 2",
                                    "requested_title": False,
                                    "notified_parking": False,
                                    "notified_inspector": True,
                                    "logistician_comment": "Check docs",
                                    "approved_by_logistician": True,
                                    "status": "loading",
                                    "status_changed": "2024-06-03T09:00:00Z",
                                },
                            ],
                        },
                    ),
                ],
            )
        },
    ),
    retrieve=extend_schema(
        summary="Retrieve a vehicle bid",
        description="Retrieve a single vehicle bid by ID.",
        responses={
            200: OpenApiResponse(
                description="A vehicle bid instance.",
                response=LogisticianVehicleBidSerializer,
                examples=[
                    OpenApiExample(
                        "Single bid",
                        value={
                            "id": 1,
                            "vin": "1HGCM82633A004352",
                            "brand": "Honda",
                            "model": "Accord",
                            "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                            "v_type": {"id": 1, "name": "Sedan"},
                            "container_number": "CONT1234567",
                            "arrival_date": "2024-06-01",
                            "openning_date": "2024-06-02",
                            "transporter": "TransCo",
                            "recipient": "Jane Smith",
                            "approved_by_inspector": False,
                            "approved_by_title": False,
                            "approved_by_re_export": False,
                            "transit_method": "t1",
                            "location": "Warehouse 1",
                            "requested_title": True,
                            "notified_parking": True,
                            "notified_inspector": False,
                            "logistician_comment": "Urgent",
                            "approved_by_logistician": True,
                            "status": "loading",
                            "status_changed": "2024-06-01T12:00:00Z",
                        },
                    )
                ],
            )
        },
    ),
    update=extend_schema(
        summary="Update a vehicle bid",
        description="Update a vehicle bid by ID. Only fields allowed by the serializer and role can be updated."
        " The example shows both admin and logistician update payloads.",
        request=LogisticianVehicleBidSerializer,
        responses={
            200: OpenApiResponse(
                description="Updated vehicle bid instance.",
                response=LogisticianVehicleBidSerializer,
                examples=[
                    OpenApiExample(
                        "Admin update",
                        value={
                            "id": 1,
                            "vin": "1HGCM82633A004352",
                            "brand": "Honda",
                            "model": "Accord",
                            "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                            "v_type": {"id": 1, "name": "Sedan"},
                            "container_number": "CONT1234567",
                            "arrival_date": "2024-06-01",
                            "openning_date": "2024-06-02",
                            "transporter": "TransCo",
                            "recipient": "Jane Smith",
                            "approved_by_inspector": True,
                            "approved_by_title": True,
                            "approved_by_re_export": True,
                            "transit_method": "t1",
                            "location": "Warehouse 1",
                            "requested_title": True,
                            "notified_parking": True,
                            "notified_inspector": True,
                            "logistician_comment": "Admin updated comment",
                            "approved_by_logistician": True,
                            "status": "ready_for_transport",
                            "status_changed": "2024-06-05T10:00:00Z",
                        },
                    ),
                    OpenApiExample(
                        "Logistician update",
                        value={
                            "id": 2,
                            "vin": "2HGCM82633A004353",
                            "brand": "Toyota",
                            "model": "Camry",
                            "client": {"id": 3, "full_name": "Jane Smith", "email": "jane@example.com"},
                            "v_type": {"id": 2, "name": "Sedan"},
                            "container_number": "CONT7654321",
                            "arrival_date": "2024-06-03",
                            "openning_date": "2024-06-04",
                            "transporter": "MoveIt",
                            "recipient": "John Doe",
                            "approved_by_inspector": False,
                            "approved_by_title": False,
                            "approved_by_re_export": False,
                            "transit_method": "re_export",
                            "location": "Warehouse 2",
                            "requested_title": False,
                            "notified_parking": False,
                            "notified_inspector": True,
                            "logistician_comment": "Logistician updated comment",
                            "approved_by_logistician": True,
                            "status": "loading",
                            "status_changed": "2024-06-06T11:00:00Z",
                        },
                    ),
                ],
            )
        },
    ),
)
class VehicleBidViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    queryset = VehicleInfo.objects.select_related("client", "v_type").order_by("-id")
    permission_classes = (VehicleBidAccessPermission,)
    http_method_names = ["get", "put"]

    def get_serializer_class(self) -> Any:  # noqa: ANN401
        role = self.request.user.role
        return get_vehicle_bid_serializer(role)

    def get_queryset(self) -> QuerySet:
        role = self.request.user.role
        qs = super().get_queryset()
        if role in {User.Roles.ADMIN, User.Roles.LOGISTICIAN}:
            return qs
        return qs.none()

    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        role = request.user.role

        if role == "admin":
            return self.get_admin_list(request, *args, **kwargs)

        if role == "logistician":
            return self.get_logistician_grouped_list(request, *args, **kwargs)

        raise PermissionDenied("You do not have permission to view bids.")

    def get_admin_list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        return super().list(request, *args, **kwargs)

    def get_logistician_grouped_list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        status_param = request.query_params.get("status", "initial")
        base_qs = self.get_queryset().filter(status=status_param)
        group_param = LOGISTICIAN_GROUPS.get(status_param, {})
        data = {}
        for group_name, group_filter in group_param.items():
            qs = base_qs.filter(**group_filter)
            data[group_name] = self.get_serializer(qs, many=True).data
        return Response(data)
