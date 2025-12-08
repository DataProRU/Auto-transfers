from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.query import QuerySet
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiRequest,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import mixins, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from autotrips.models.vehicle_info import VehicleInfo, VehicleType
from autotrips.serializers.vehicle_info import VehicleInfoSerializer, VehicleTypeSerializer
from project.permissions import VehicleAccessPermission

User = get_user_model()


class VehicleInfoViewSet(viewsets.ModelViewSet):
    queryset = VehicleInfo.objects.select_related("client", "v_type").order_by("-id")
    serializer_class = VehicleInfoSerializer
    permission_classes = (VehicleAccessPermission,)

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        staff_roles = {User.Roles.ADMIN, User.Roles.MANAGER}

        client_id = self.request.query_params.get("client_id")

        if self.request.user.role in staff_roles:
            if client_id:
                queryset = queryset.filter(client_id=client_id)
        else:
            queryset = queryset.filter(client=self.request.user)

        return queryset

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
                        "year_brand_model": "2021 Toyota Camry",
                        "v_type_id": 1,
                        "vin": "4T1BF1FKXEU123456",
                        "price": 12000.00,
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
                            "year_brand_model": "2021 Toyota Camry",
                            "v_type_id": 1,
                            "vin": "4T1BF1FKXEU123456",
                            "price": 12000.00,
                            "container_number": "CNTR001",
                            "arrival_date": "2023-12-15",
                            "transporter": "ABC Logistics",
                            "recipient": "XYZ Dealership",
                        },
                        {
                            "client_id": 1,
                            "year_brand_model": "2020 Honda Accord",
                            "v_type_id": 2,
                            "vin": "1HGCM82633A123456",
                            "price": 12000.00,
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
                            "year_brand_model": "2021 Toyota Camry",
                            "v_type_id": 1,
                            "v_type_name": "SUV",
                            "vin": "4T1BF1FKXEU123456",
                            "price": 12000.00,
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
                                "price": 12000.00,
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
                                "price": 12000.00,
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
                        value={
                            "vin": {"message": "Vehicle with this VIN already exists", "error_type": "vin_exists"},
                            "arrival_date": ["Arrival date cannot be in the past"],
                        },
                    ),
                    OpenApiExample(
                        "Bulk vehicle error",
                        value=[
                            {"vin": {"message": "Vehicle with this VIN already exists", "error_type": "vin_exists"}},
                            {"arrival_date": ["Arrival date cannot be in the past"]},
                        ],
                    ),
                    OpenApiExample(
                        "Multiply clients",
                        value={"non_field_error": "Can create multiply vehicles only for one client"},
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
        - Admins and managers see all vehicles (can filter by client_id)
        - Clients see only their own vehicles""",
        parameters=[
            OpenApiParameter(
                name="client_id",
                description="Filter vehicles by client ID (admin/manager only)",
                required=False,
                type=int,
            ),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=VehicleInfoSerializer(many=True),
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(description="Not authorized to view vehicles"),
        },
    )
    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class VehicleTypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = (VehicleAccessPermission,)
