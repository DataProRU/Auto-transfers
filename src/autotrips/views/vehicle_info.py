from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from autotrips.models.vehicle import VehicleInfo
from autotrips.serializers.vehicle_info import VehicleInfoSerializer
from project.permissions import VehicleAccessPermission

User = get_user_model()


class VehicleInfoViewSet(viewsets.ModelViewSet):
    queryset = VehicleInfo.objects.select_related("client", "v_type").order_by("-id")
    serializer_class = VehicleInfoSerializer
    permission_classes = (VehicleAccessPermission,)

    @extend_schema(
        summary="Create vehicle(s)",
        description="""Create one or multiple vehicles.
        For single creation, send a JSON object.
        For bulk creation, send a JSON array of objects.
        All operations are atomic.""",
        request=OpenApiRequest(
            request=VehicleInfoSerializer,
            examples=[
                OpenApiExample(
                    "Single vehicle creation",
                    value={
                        "client_id": 1,
                        "brand": "Toyota",
                        "model": "Camry",
                        "v_type_id": 1,
                        "vin": "4T1BF1FKXEU123456",
                        "container_number": "CNTR001",
                        "arrival_date": "2023-12-15",
                        "transporter": "ABC Logistics",
                        "recipient": "XYZ Dealership",
                        "comment": "New shipment",
                    },
                    request_only=True,
                ),
                OpenApiExample(
                    "Bulk vehicle creation",
                    value=[
                        {
                            "client_id": 1,
                            "brand": "Toyota",
                            "model": "Camry",
                            "v_type_id": 1,
                            "vin": "4T1BF1FKXEU123456",
                            "container_number": "CNTR001",
                            "arrival_date": "2023-12-15",
                            "transporter": "ABC Logistics",
                            "recipient": "XYZ Dealership",
                        },
                        {
                            "client_id": 1,
                            "brand": "Honda",
                            "model": "Accord",
                            "v_type_id": 2,
                            "vin": "1HGCM82633A123456",
                            "container_number": "CNTR002",
                            "arrival_date": "2023-12-16",
                            "transporter": "DEF Logistics",
                            "recipient": "UVW Dealership",
                        },
                    ],
                    request_only=True,
                ),
            ],
        ),
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=VehicleInfoSerializer,
                description="Vehicle(s) created successfully",
                examples=[
                    OpenApiExample(
                        "Single vehicle response",
                        value={
                            "id": 1,
                            "client_id": 1,
                            "client_name": "John Doe",
                            "brand": "Toyota",
                            "model": "Camry",
                            "v_type_id": 1,
                            "v_type_name": "SUV",
                            "vin": "4T1BF1FKXEU123456",
                            "container_number": "CNTR001",
                            "arrival_date": "2023-12-15",
                            "transporter": "ABC Logistics",
                            "recipient": "XYZ Dealership",
                            "comment": "New shipment",
                            "status": "Новый",
                            "status_changed": "2023-10-01T12:34:56Z",
                            "creation_time": "2023-10-01T12:34:56Z",
                        },
                    ),
                    OpenApiExample(
                        "Bulk vehicle response",
                        value=[
                            {
                                "id": 1,
                                "client_id": 1,
                                "client_name": "John Doe",
                                "brand": "Toyota",
                                "model": "Camry",
                                "v_type_id": 1,
                                "v_type_name": "SUV",
                                "vin": "4T1BF1FKXEU123456",
                                "container_number": "CNTR001",
                                "arrival_date": "2023-12-15",
                                "transporter": "ABC Logistics",
                                "recipient": "XYZ Dealership",
                                "status": "Новый",
                                "status_changed": "2023-10-01T12:34:56Z",
                                "creation_time": "2023-10-01T12:34:56Z",
                            },
                            {
                                "id": 2,
                                "client_id": 1,
                                "client_name": "Jane Smith",
                                "brand": "Honda",
                                "model": "Accord",
                                "v_type_id": 2,
                                "v_type_name": "Sedan",
                                "vin": "1HGCM82633A123456",
                                "container_number": "CNTR002",
                                "arrival_date": "2023-12-16",
                                "transporter": "DEF Logistics",
                                "recipient": "UVW Dealership",
                                "status": "Новый",
                                "status_changed": "2023-10-01T12:34:56Z",
                                "creation_time": "2023-10-01T12:34:56Z",
                            },
                        ],
                    ),
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=dict,
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Single vehicle error",
                        value={"vin": ["Invalid VIN format"], "arrival_date": ["Arrival date cannot be in the past"]},
                    ),
                    OpenApiExample(
                        "Bulk vehicle error",
                        value={
                            "non_field_error": "Can create multiply vehicles only for one client",
                            "0": {"vin": ["Invalid VIN format"]},
                            "1": {"arrival_date": ["Arrival date cannot be in the past"]},
                        },
                    ),
                ],
            ),
        },
    )
    @transaction.atomic
    def create(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        if isinstance(request.data, dict):
            return super().create(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="List vehicles",
        description="""Returns list of vehicles based on user role:
        - Admins see all vehicles
        - Clients see only their own vehicles""",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=VehicleInfoSerializer(many=True),
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(description="Not authorized to view vehicles"),
        },
    )
    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        staff_roles = {User.Roles.ADMIN, User.Roles.MANAGER}
        queryset = self.get_queryset()

        if request.user.role not in staff_roles:
            queryset = queryset.filter(client=request.user)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
