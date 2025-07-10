from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from autotrips.models.vehicle_info import VehicleInfo
from autotrips.serializers.vehicle_bid import (
    LogisticianVehicleBidSerializer,
    RejectBidSerializer,
    get_vehicle_bid_serializer,
)
from project.permissions import AdminLogistianVehicleBidAccessPermission, VehicleBidAccessPermission

User = get_user_model()


LOGISTICIAN_GROUPS = {
    "initial": {
        "untouched": {"approved_by_logistician": False},
        "in_progress": {"approved_by_logistician": True},
    },
}

MANAGER_GROUPS = {
    "untouched": {"approved_by_manager": False},
    "in_progress": {"approved_by_manager": True},
}

TITLE_GROUPS = {
    "untouched": {"pickup_address__isnull": True},
    "in_progress": {"pickup_address__isnull": False, "approved_by_title": False},
    "completed": {"approved_by_title": True},
}


@extend_schema_view(
    list=extend_schema(
        summary="List vehicle bids (admin: flat list, logistician: grouped, opening_manager: grouped, title: grouped)",
        description="Admins receive a flat list of all vehicle bids. Logisticians receive grouped bids by "
        "status and approval. Opening managers receive grouped bids by approval status and arrival date. "
        "Title role receives grouped bids by pickup address and approval.",
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
                description="Flat list for admin or grouped for logistician/opening_manager/title.",
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
                                "comment": "Admin comment",
                                "status": "loading",
                                "status_changed": "2024-06-01T12:00:00Z",
                                "transit_method": "t1",
                                "location": "Warehouse 1",
                                "requested_title": True,
                                "notified_parking": True,
                                "notified_inspector": False,
                                "logistician_comment": "Urgent",
                                "opened": False,
                                "manager_comment": None,
                                "pickup_address": "123 Main St",
                                "took_title": "yes",
                                "title_collection_date": "2024-06-03",
                                "transit_number": "TN123456",
                                "inspection_done": "yes",
                                "inspection_date": "2024-06-04",
                                "number_sent": True,
                                "number_sent_date": "2024-06-05",
                                "inspection_paid": True,
                                "inspector_comment": "Passed inspection",
                                "approved_by_logistician": True,
                                "approved_by_manager": False,
                                "approved_by_inspector": False,
                                "approved_by_title": False,
                                "approved_by_re_export": False,
                                "approved_by_reciever": False,
                                "creation_time": "2024-06-01T10:00:00Z",
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
                                },
                            ],
                            "in_progress": [
                                {
                                    "id": 2,
                                    "vin": "2HGCM82633A004353",
                                    "brand": "Toyota",
                                    "model": "Camry",
                                    "client": {"id": 3, "full_name": "Jane Smith", "email": "jane@example.com"},
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
                                },
                            ],
                        },
                    ),
                    OpenApiExample(
                        "Opening manager grouped list",
                        value={
                            "untouched": [
                                {
                                    "id": 1,
                                    "vin": "1HGCM82633A004352",
                                    "brand": "Honda",
                                    "model": "Accord",
                                    "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                                    "container_number": "CONT1234567",
                                    "arrival_date": "2024-06-01",
                                    "transporter": "TransCo",
                                    "recipient": "Jane Smith",
                                    "transit_method": "t1",
                                    "openning_date": None,
                                    "opened": False,
                                    "manager_comment": None,
                                },
                            ],
                            "in_progress": [
                                {
                                    "id": 2,
                                    "vin": "2HGCM82633A004353",
                                    "brand": "Toyota",
                                    "model": "Camry",
                                    "client": {"id": 3, "full_name": "Jane Smith", "email": "jane@example.com"},
                                    "container_number": "CONT7654321",
                                    "arrival_date": "2024-06-03",
                                    "transporter": "MoveIt",
                                    "recipient": "John Doe",
                                    "transit_method": "re_export",
                                    "openning_date": "2024-06-04",
                                    "opened": True,
                                    "manager_comment": "Container opened and inspected",
                                },
                            ],
                        },
                    ),
                    OpenApiExample(
                        "Title grouped list",
                        value={
                            "untouched": [
                                {
                                    "id": 1,
                                    "vin": "1HGCM82633A004352",
                                    "brand": "Honda",
                                    "model": "Accord",
                                    "pickup_address": None,
                                    "took_title": None,
                                    "title_collection_date": None,
                                },
                            ],
                            "in_progress": [
                                {
                                    "id": 2,
                                    "vin": "2HGCM82633A004353",
                                    "brand": "Toyota",
                                    "model": "Camry",
                                    "pickup_address": "123 Main St",
                                    "took_title": "yes",
                                    "title_collection_date": None,
                                },
                            ],
                            "completed": [
                                {
                                    "id": 3,
                                    "vin": "3HGCM82633A004354",
                                    "brand": "BMW",
                                    "model": "X5",
                                    "pickup_address": "456 Elm St",
                                    "took_title": "yes",
                                    "title_collection_date": "2024-06-10",
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
                        "Logistician single bid",
                        value={
                            "id": 1,
                            "vin": "1HGCM82633A004352",
                            "brand": "Honda",
                            "model": "Accord",
                            "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
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
                        },
                    ),
                    OpenApiExample(
                        "Manager single bid",
                        value={
                            "id": 2,
                            "vin": "2HGCM82633A004353",
                            "brand": "Toyota",
                            "model": "Camry",
                            "client": {"id": 3, "full_name": "Jane Smith", "email": "jane@example.com"},
                            "container_number": "CONT7654321",
                            "arrival_date": "2024-06-03",
                            "transporter": "MoveIt",
                            "recipient": "John Doe",
                            "transit_method": "re_export",
                            "openning_date": "2024-06-04",
                            "opened": True,
                            "manager_comment": "Container opened and inspected",
                        },
                    ),
                    OpenApiExample(
                        "Title single bid",
                        value={
                            "id": 3,
                            "vin": "3HGCM82633A004354",
                            "brand": "BMW",
                            "model": "X5",
                            "pickup_address": "456 Elm St",
                            "took_title": "yes",
                            "title_collection_date": "2024-06-10",
                        },
                    ),
                ],
            )
        },
    ),
    update=extend_schema(
        summary="Update a vehicle bid",
        description="Update a vehicle bid by ID. Only fields allowed by the serializer and role can be updated."
        "The example shows admin, logistician, opening_manager, and title update payloads.",
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
                            "comment": "Admin updated comment",
                            "status": "ready_for_transport",
                            "status_changed": "2024-06-05T10:00:00Z",
                            "transit_method": "t1",
                            "location": "Warehouse 1",
                            "requested_title": True,
                            "notified_parking": True,
                            "notified_inspector": True,
                            "logistician_comment": "Admin updated comment",
                            "opened": False,
                            "manager_comment": None,
                            "pickup_address": "123 Main St",
                            "took_title": "yes",
                            "title_collection_date": "2024-06-03",
                            "transit_number": "TN123456",
                            "inspection_done": "yes",
                            "inspection_date": "2024-06-04",
                            "number_sent": True,
                            "number_sent_date": "2024-06-05",
                            "inspection_paid": True,
                            "inspector_comment": "Passed inspection",
                            "approved_by_logistician": True,
                            "approved_by_manager": False,
                            "approved_by_inspector": False,
                            "approved_by_title": False,
                            "approved_by_re_export": False,
                            "approved_by_reciever": False,
                            "creation_time": "2024-06-01T10:00:00Z",
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
                        },
                    ),
                    OpenApiExample(
                        "Opening manager update",
                        value={
                            "id": 3,
                            "vin": "3HGCM82633A004354",
                            "brand": "BMW",
                            "model": "X5",
                            "client": {"id": 4, "full_name": "Alice Brown", "email": "alice@example.com"},
                            "container_number": "CONT9876543",
                            "arrival_date": "2024-06-05",
                            "transporter": "FastShip",
                            "recipient": "Alice Brown",
                            "transit_method": "t1",
                            "openning_date": "2024-06-06",
                            "opened": True,
                            "manager_comment": "Container opened and contents verified",
                        },
                    ),
                    OpenApiExample(
                        "Title update",
                        value={
                            "id": 4,
                            "vin": "4HGCM82633A004355",
                            "brand": "Audi",
                            "model": "A4",
                            "pickup_address": "789 Oak Ave",
                            "took_title": "yes",
                            "title_collection_date": "2024-06-15",
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
        if role == User.Roles.OPENING_MANAGER:
            allowed_date = timezone.now() + timedelta(days=7)
            return qs.filter(
                status=VehicleInfo.Statuses.INITIAL,
                approved_by_logistician=True,
                arrival_date__lte=allowed_date,
                transit_method__in=[VehicleInfo.TransitMethod.T1, VehicleInfo.TransitMethod.RE_EXPORT],
            )
        if role == User.Roles.TITLE:
            return qs.filter(approved_by_logistician=True, approved_by_manager=True)
        return qs.none()

    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        role = request.user.role

        if role == User.Roles.ADMIN:
            return self.get_admin_list(request, *args, **kwargs)

        if role == User.Roles.LOGISTICIAN:
            return self.get_logistician_grouped_list(request)

        if role == User.Roles.OPENING_MANAGER:
            return self.get_manager_grouped_list()

        if role == User.Roles.TITLE:
            return self.get_title_grouped_list()

        raise PermissionDenied("You do not have permission to view bids.")

    def get_admin_list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        return super().list(request, *args, **kwargs)

    def get_logistician_grouped_list(self, request: Request) -> Response:
        status_param = request.query_params.get("status", "initial")
        base_qs = self.get_queryset().filter(status=status_param)
        group_param = LOGISTICIAN_GROUPS.get(status_param, {})
        data = {}
        for group_name, group_filter in group_param.items():
            qs = base_qs.filter(**group_filter)
            data[group_name] = self.get_serializer(qs, many=True).data
        return Response(data)

    def get_manager_grouped_list(self) -> Response:
        base_qs = self.get_queryset()
        data = {}
        for group_name, group_filter in MANAGER_GROUPS.items():
            qs = base_qs.filter(**group_filter)
            data[group_name] = self.get_serializer(qs, many=True).data
        return Response(data)

    def get_title_grouped_list(self) -> Response:
        base_qs = self.get_queryset()
        data = {}
        for group_name, group_filter in TITLE_GROUPS.items():
            qs = base_qs.filter(**group_filter)
            data[group_name] = self.get_serializer(qs, many=True).data
        return Response(data)

    @extend_schema(
        summary="Reject a vehicle bid",
        description="Mark the status of a particular bid as 'rejected'."
        " Only admins and logisticians can perform this action. A 'logistician_comment' is required before rejection.",
        request=RejectBidSerializer,
        responses={
            200: OpenApiResponse(
                description="Bid marked as rejected.",
                response=LogisticianVehicleBidSerializer,
                examples=[
                    OpenApiExample(
                        "Rejected bid",
                        value={
                            "id": 1,
                            "vin": "1HGCM82633A004352",
                            "brand": "Honda",
                            "model": "Accord",
                            "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
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
                            "requested_title": False,
                            "notified_parking": False,
                            "notified_inspector": False,
                        },
                    )
                ],
            )
        },
    )
    @action(
        detail=True, methods=["put"], url_path="reject", permission_classes=(AdminLogistianVehicleBidAccessPermission,)
    )
    def reject(self, request: Request, pk: int | None = None) -> Response:
        req_serializer = RejectBidSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)
        comment = req_serializer.data.get("logistician_comment")

        bid = self.get_object()
        if bid.approved_by_logistician:
            return Response({"detail": "You can't reject approved bid."}, status=status.HTTP_400_BAD_REQUEST)

        bid.status = VehicleInfo.Statuses.REJECTED
        bid.logistician_comment = comment
        bid.save(update_fields=["status", "logistician_comment", "status_changed"])
        resp_serializer = self.get_serializer(bid)
        return Response(resp_serializer.data)
