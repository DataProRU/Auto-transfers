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
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from autotrips.models.vehicle_info import VehicleInfo, VehicleType
from autotrips.serializers.vehicle_info import (
    VehicleExcelUploadSerializer,
    VehicleInfoSerializer,
    VehicleTypeSerializer,
)
from project.permissions import VehicleAccessPermission

User = get_user_model()


class VehicleInfoViewSet(viewsets.ModelViewSet):
    queryset = VehicleInfo.objects.select_related("client", "v_type").order_by("-id")
    serializer_class = VehicleInfoSerializer
    permission_classes = (VehicleAccessPermission,)
    http_method_names = ["get", "post", "patch"]

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
        Can optionally upload document photos during creation using
        'uploaded_document_photos' field.
        All operations are atomic.""",
        request=OpenApiRequest(
            request=VehicleInfoSerializer,
            examples=[
                OpenApiExample(
                    "Single vehicle creation",
                    value={
                        "client": 1,
                        "year_brand_model": "2021 Toyota Camry",
                        "v_type": 1,
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
                            "client": 1,
                            "year_brand_model": "2021 Toyota Camry",
                            "v_type": 1,
                            "vin": "4T1BF1FKXEU123456",
                            "price": 12000.00,
                            "container_number": "CNTR001",
                            "arrival_date": "2023-12-15",
                            "transporter": "ABC Logistics",
                            "recipient": "XYZ Dealership",
                        },
                        {
                            "client": 1,
                            "year_brand_model": "2020 Honda Accord",
                            "v_type": 2,
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
                OpenApiExample(
                    "Single vehicle with document photos",
                    value={
                        "client": 1,
                        "year_brand_model": "2021 Toyota Camry",
                        "v_type": 1,
                        "vin": "4T1BF1FKXEU123456",
                        "price": 12000.00,
                        "container_number": "CNTR001",
                        "uploaded_document_photos": ["<file1>", "<file2>"],
                    },
                    request_only=True,
                ),
                OpenApiExample(
                    "Bulk vehicles with document photos",
                    value=[
                        {
                            "client": 1,
                            "year_brand_model": "2021 Toyota Camry",
                            "v_type": 1,
                            "vin": "4T1BF1FKXEU123456",
                            "uploaded_document_photos": ["<title_doc>", "<registration_doc>"],
                        },
                        {
                            "client": 1,
                            "year_brand_model": "2020 Honda Accord",
                            "v_type": 2,
                            "vin": "1HGCM82633A123456",
                            "uploaded_document_photos": ["<insurance_doc>"],
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
                            "client": {"id": 1, "full_name": "John Doe", "phone": "+1234567890"},
                            "year_brand_model": "2021 Toyota Camry",
                            "v_type": {"id": 1, "v_type": "SUV"},
                            "vin": "4T1BF1FKXEU123456",
                            "price": 12000.00,
                            "container_number": "CNTR001",
                            "arrival_date": "2023-12-15",
                            "transporter": "ABC Logistics",
                            "recipient": "XYZ Dealership",
                            "comment": "New shipment",
                            "document_photos": [],
                            "status": "Новый",
                            "status_changed": "2023-10-01T12:34:56Z",
                            "creation_time": "2023-10-01T12:34:56Z",
                        },
                    ),
                    OpenApiExample(
                        "Single vehicle with photos response",
                        value={
                            "id": 1,
                            "client": {"id": 1, "full_name": "John Doe", "phone": "+1234567890"},
                            "year_brand_model": "2021 Toyota Camry",
                            "v_type": {"id": 1, "v_type": "SUV"},
                            "vin": "4T1BF1FKXEU123456",
                            "price": 12000.00,
                            "container_number": "CNTR001",
                            "document_photos": [
                                {
                                    "id": 1,
                                    "image": "/media/vehicle-docs/2023/12/15/file1.jpg",
                                    "created": "2023-12-15T10:00:00Z",
                                },
                                {
                                    "id": 2,
                                    "image": "/media/vehicle-docs/2023/12/15/file2.jpg",
                                    "created": "2023-12-15T10:01:00Z",
                                },
                            ],
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
                                "client": {"id": 1, "full_name": "John Doe", "phone": "+1234567890"},
                                "year_brand_model": "2021 Toyota Camry",
                                "v_type": {"id": 1, "v_type": "SUV"},
                                "vin": "4T1BF1FKXEU123456",
                                "price": 12000.00,
                                "container_number": "CNTR001",
                                "arrival_date": "2023-12-15",
                                "transporter": "ABC Logistics",
                                "recipient": "XYZ Dealership",
                                "document_photos": [],
                                "status": "Новый",
                                "status_changed": "2023-10-01T12:34:56Z",
                                "creation_time": "2023-10-01T12:34:56Z",
                            },
                            {
                                "id": 2,
                                "client": {"id": 1, "full_name": "John Doe", "phone": "+1234567890"},
                                "year_brand_model": "2020 Honda Accord",
                                "v_type": {"id": 2, "v_type": "Sedan"},
                                "vin": "1HGCM82633A123456",
                                "price": 12000.00,
                                "container_number": "CNTR002",
                                "arrival_date": "2023-12-16",
                                "transporter": "DEF Logistics",
                                "recipient": "UVW Dealership",
                                "document_photos": [],
                                "status": "Новый",
                                "status_changed": "2023-10-01T12:34:56Z",
                                "creation_time": "2023-10-01T12:34:56Z",
                            },
                        ],
                    ),
                    OpenApiExample(
                        "Bulk vehicles with photos response",
                        value=[
                            {
                                "id": 1,
                                "client": {"id": 1, "full_name": "John Doe", "phone": "+1234567890"},
                                "year_brand_model": "2021 Toyota Camry",
                                "v_type": {"id": 1, "v_type": "SUV"},
                                "vin": "4T1BF1FKXEU123456",
                                "document_photos": [
                                    {
                                        "id": 1,
                                        "image": "/media/vehicle-docs/2023/12/15/title_doc.jpg",
                                        "created": "2023-12-15T10:00:00Z",
                                    },
                                    {
                                        "id": 2,
                                        "image": "/media/vehicle-docs/2023/12/15/registration_doc.jpg",
                                        "created": "2023-12-15T10:01:00Z",
                                    },
                                ],
                                "status": "Новый",
                                "status_changed": "2023-10-01T12:34:56Z",
                                "creation_time": "2023-10-01T12:34:56Z",
                            },
                            {
                                "id": 2,
                                "client": {"id": 1, "full_name": "John Doe", "phone": "+1234567890"},
                                "year_brand_model": "2020 Honda Accord",
                                "v_type": {"id": 2, "v_type": "Sedan"},
                                "vin": "1HGCM82633A123456",
                                "document_photos": [
                                    {
                                        "id": 3,
                                        "image": "/media/vehicle-docs/2023/12/15/insurance_doc.jpg",
                                        "created": "2023-12-15T10:02:00Z",
                                    }
                                ],
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

    @extend_schema(
        summary="Update vehicle information and manage document photos",
        description="Update vehicle information, add new document photos, and remove existing document photos."
        "All operations can be performed in a single request. Read-only fields: id, year_brand_model, status,"
        "status_changed, creation_time.",
        request=OpenApiRequest(
            request=dict,
            examples=[
                OpenApiExample(
                    "Add document photos",
                    value={"uploaded_document_photos": ["<file1>", "<file2>"]},
                    request_only=True,
                ),
                OpenApiExample(
                    "Remove document photos",
                    value={"remove_document_photo_ids": [1, 2, 3]},
                    request_only=True,
                ),
                OpenApiExample(
                    "Add and remove document photos",
                    value={"uploaded_document_photos": ["<file1>"], "remove_document_photo_ids": [2, 3]},
                    request_only=True,
                ),
                OpenApiExample(
                    "Update vehicle info and photos",
                    value={
                        "price": 15000.00,
                        "comment": "Updated comment",
                        "transporter": "New Logistics Company",
                        "uploaded_document_photos": ["<new_doc>"],
                        "remove_document_photo_ids": [1],
                    },
                    request_only=True,
                ),
            ],
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=VehicleInfoSerializer,
                description="Document photos updated successfully",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "id": 1,
                            "client": {"id": 1, "full_name": "John Doe", "phone": "+1234567890"},
                            "year_brand_model": "2021 Toyota Camry",
                            "v_type": {"id": 1, "v_type": "SUV"},
                            "vin": "4T1BF1FKXEU123456",
                            "price": 12000.00,
                            "container_number": "CNTR001",
                            "arrival_date": "2023-12-15",
                            "transporter": "ABC Logistics",
                            "recipient": "XYZ Dealership",
                            "comment": "New shipment",
                            "document_photos": [
                                {
                                    "id": 1,
                                    "image": "/media/vehicle-docs/2023/12/15/doc1.jpg",
                                    "created": "2023-12-15T10:00:00Z",
                                },
                                {
                                    "id": 2,
                                    "image": "/media/vehicle-docs/2023/12/15/doc2.jpg",
                                    "created": "2023-12-15T10:05:00Z",
                                },
                            ],
                            "status": "Новый",
                            "status_changed": "2023-10-01T12:34:56Z",
                            "creation_time": "2023-10-01T12:34:56Z",
                        },
                    ),
                ],
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(description="Not authorized to modify this vehicle"),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description="Vehicle not found"),
        },
    )
    def partial_update(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        instance = self.get_object()

        serializer = VehicleInfoSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        response_serializer = VehicleInfoSerializer(updated_instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Upload Excel file to create vehicles",
        description=(
            "Upload an Excel file with Russian column headers to create multiple vehicles for a client.\n\n"
            "Excel file requirements:\n"
            "- Columns: Год Марка Модель, VIN\n"
            "- All rows must have both values\n"
            "- VINs must be unique within the file\n"
            "- File format: .xlsx or .xls"
        ),
        request=OpenApiRequest(
            request=dict,
            examples=[
                OpenApiExample(
                    "Valid upload request",
                    value={"client": 1, "excel_file": "(binary Excel file with Год Марка Модель & VIN columns)"},
                    request_only=True,
                ),
            ],
        ),
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=dict,
                description="Successfully uploaded vehicles from Excel",
                examples=[
                    OpenApiExample(
                        "Upload success",
                        value={
                            "created_count": 2,
                            "errors": [],
                            "vehicles": [
                                {
                                    "id": 10,
                                    "client": 1,
                                    "year_brand_model": "2020 Toyota Camry",
                                    "v_type": None,
                                    "vin": "4T1BF1FKXEU123456",
                                    "container_number": "",
                                    "arrival_date": None,
                                    "transporter": "",
                                    "recipient": "",
                                    "comment": "",
                                    "document_photos": [],
                                    "status": "initial",
                                    "status_changed": "2024-05-30T12:00:00Z",
                                    "creation_time": "2024-05-30T12:00:00Z",
                                    "price": None,
                                },
                                {
                                    "id": 11,
                                    "client": 1,
                                    "year_brand_model": "2019 Ford Focus",
                                    "v_type": None,
                                    "vin": "1FADP3F29JL123456",
                                    "container_number": "",
                                    "arrival_date": None,
                                    "transporter": "",
                                    "recipient": "",
                                    "comment": "",
                                    "document_photos": [],
                                    "status": "initial",
                                    "status_changed": "2024-05-30T12:00:01Z",
                                    "creation_time": "2024-05-30T12:00:01Z",
                                    "price": None,
                                },
                            ],
                        },
                        response_only=True,
                        status_codes=[str(status.HTTP_201_CREATED)],
                    ),
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=dict,
                description="Validation error or bad file encountered during Excel upload.",
                examples=[
                    OpenApiExample(
                        "Duplicate VINs in file (error)",
                        value={
                            "errors": [
                                {
                                    "row": 3,
                                    "vin": "4T1BF1FKXEU123456",
                                    "error": "Duplicate VIN within file: 4T1BF1FKXEU123456",
                                }
                            ]
                        },
                        response_only=True,
                        status_codes=[str(status.HTTP_400_BAD_REQUEST)],
                    ),
                    OpenApiExample(
                        "VIN exists in database (error)",
                        value={
                            "errors": [
                                {
                                    "row": "N/A",
                                    "vin": "1HGCM82633A123456",
                                    "error": "VIN already exists in database: 1HGCM82633A123456",
                                }
                            ]
                        },
                        response_only=True,
                        status_codes=[str(status.HTTP_400_BAD_REQUEST)],
                    ),
                    OpenApiExample(
                        "Missing required columns (error)",
                        value={
                            "excel_file": ["Excel file is missing required columns: Год Марка Модель"]
                        },
                        response_only=True,
                        status_codes=[str(status.HTTP_400_BAD_REQUEST)],
                    ),
                    OpenApiExample(
                        "Empty year_brand_model cell (error)",
                        value={
                            "errors": [
                                {
                                    "row": 2,
                                    "vin": "N/A",
                                    "error": "year_brand_model cannot be empty",
                                }
                            ]
                        },
                        response_only=True,
                        status_codes=[str(status.HTTP_400_BAD_REQUEST)],
                    ),
                    OpenApiExample(
                        "Empty VIN cell (error)",
                        value={
                            "errors": [
                                {
                                    "row": 2,
                                    "vin": "N/A",
                                    "error": "VIN cannot be empty",
                                }
                            ]
                        },
                        response_only=True,
                        status_codes=[str(status.HTTP_400_BAD_REQUEST)],
                    ),
                ],
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="upload-excel", url_name="upload-excel")
    def upload_excel(self, request: Request) -> Response:
        serializer = VehicleExcelUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result, status=status.HTTP_201_CREATED)


class VehicleTypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = (VehicleAccessPermission,)
