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
from rest_framework import viewsets
from rest_framework.decorators import action
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
        summary="List all vehicle bids (admin only)",
        description="Returns a flat list of all vehicle bids. Only accessible by admins.",
        responses={
            200: OpenApiResponse(
                description="A list of vehicle bids.", response=LogisticianVehicleBidSerializer(many=True)
            )
        },
    ),
    retrieve=extend_schema(
        summary="Retrieve a vehicle bid",
        description="Retrieve a single vehicle bid by ID.",
        responses={
            200: OpenApiResponse(description="A vehicle bid instance.", response=LogisticianVehicleBidSerializer)
        },
    ),
)
class VehicleBidViewSet(viewsets.ModelViewSet):
    queryset = VehicleInfo.objects.select_related("client", "v_type").order_by("-id")
    permission_classes = (VehicleBidAccessPermission,)
    http_method_names = ["get", "patch", "list", "retrieve", "update"]

    def get_serializer_class(self) -> Any:  # noqa: ANN401
        role = self.request.user.role
        return get_vehicle_bid_serializer(role)

    def get_queryset(self) -> QuerySet:
        role = self.request.user.role
        qs = super().get_queryset()
        if role in {User.Roles.ADMIN, User.Roles.LOGISTICIAN}:
            return qs
        return qs.none()

    def list(self, request: Request, *args: tuple[str], **kwargs: dict[str, Any]) -> Response:
        role = request.user.role
        if role != "admin":
            raise PermissionDenied("You do not have permission to view all bids.")
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Logistician dashboard: grouped vehicle bids",
        description="Returns grouped vehicle bids for logisticians, grouped by 'untouched' and 'in_progress'. "
        "Optional 'status' query parameter filters by vehicle status.",
        parameters=[
            OpenApiParameter(
                name="status",
                description="Vehicle status to filter by (e.g., 'initial').",
                required=True,
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
                description="Grouped vehicle bids by status and approval.",
                response=LogisticianVehicleBidSerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Grouped bids",
                        value={
                            "untouched": [
                                {
                                    "id": 1,
                                    "vin": "...",
                                    "brand": "...",
                                    "model": "...",
                                    "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                                },
                            ],
                            "in_progress": [
                                {
                                    "id": 3,
                                    "vin": "...",
                                    "brand": "...",
                                    "model": "...",
                                    "client": {"id": 4, "full_name": "Jane Smith", "email": "jane@example.com"},
                                },
                            ],
                        },
                    )
                ],
            )
        },
    )
    @action(detail=False, methods=["get"], url_path="logistician-dashboard")
    def logistician_dashboard(self, request: Request) -> Response:
        if request.user.role != "logistician":
            return PermissionDenied("You do not have permission to access logistician dashboard.")

        status_param = request.query_params.get("status", "initial")
        base_qs = self.get_queryset().filter(status=status_param)
        group_param = LOGISTICIAN_GROUPS.get(status_param, {})
        data = {}
        for group_name, group_filter in group_param.items():
            qs = base_qs.filter(**group_filter)
            data[group_name] = self.get_serializer(qs, many=True).data

        return Response(data)
