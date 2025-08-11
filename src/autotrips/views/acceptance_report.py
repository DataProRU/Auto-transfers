from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from autotrips.models.acceptance_report import AcceptenceReport, CarPhoto, DocumentPhoto, KeyPhoto
from autotrips.models.vehicle_info import VehicleInfo
from autotrips.serializers.acceptance_report import (
    AcceptanceReportSerializer,
    CarPhotoSerializer,
    DocumentPhotoSerializer,
    KeyPhotoSerializer,
)
from project.permissions import IsAdminOrManager, IsApproved

User = get_user_model()

WORKSHEET = settings.VINS_WORKSHEET


class AcceptanceReportViewSet(viewsets.ModelViewSet):
    queryset = AcceptenceReport.objects.all()
    serializer_class = AcceptanceReportSerializer
    permission_classes = [IsApproved]
    http_method_names = ["get", "post"]

    @extend_schema(
        summary="List all acceptance reports",
        description="Retrieve a list of all acceptance reports created in the last 3 months. Optionally filter by VIN.",
        parameters=[
            OpenApiParameter(
                name="vin",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter reports by VIN.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=AcceptanceReportSerializer(many=True),
                description="Reports retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value=[
                            {
                                "id": 1,
                                "vin": "1HGCM82633A123456",
                                "reporter": {
                                    "id": 1,
                                    "full_name": "John Doe",
                                    "phone": "+79991234567",
                                    "telegram": "@johndoe",
                                },
                                "model": "Model X",
                                "place": "Factory A",
                                "comment": "First report",
                                "report_number": 1,
                                "report_time": "2025-03-15T13:57:11.953964+03:00",
                                "acceptance_date": "2025-03-15",
                                "status": "Принят",
                                "car_photos": [
                                    {
                                        "id": 1,
                                        "image": "http://example.com/media/cars/2025/03/15/car1.jpg",
                                        "created": "2025-03-15T13:57:11.953964+03:00",
                                    }
                                ],
                                "key_photos": [
                                    {
                                        "id": 1,
                                        "image": "http://example.com/media/keys/2025/03/15/key1.jpg",
                                        "created": "2025-03-15T13:57:11.953964+03:00",
                                    }
                                ],
                                "document_photos": [
                                    {
                                        "id": 1,
                                        "image": "http://example.com/media/car-docs/2025/03/15/doc1.jpg",
                                        "created": "2025-03-15T13:57:11.953964+03:00",
                                    }
                                ],
                            }
                        ],
                    ),
                ],
            ),
            403: OpenApiResponse(description="forbidden"),
        },
    )
    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        three_months_ago = timezone.now() - timedelta(days=90)
        queryset = self.queryset.filter(report_time__gte=three_months_ago)
        vin = request.query_params.get("vin")
        if vin:
            queryset = queryset.filter(vehicle__vin=vin)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create a new acceptance report",
        description="Create a new acceptance report with uploaded car photos, key photos, and document photos.",
        request=AcceptanceReportSerializer,
        responses={
            201: OpenApiResponse(
                description="Report created successfully",
                response=AcceptanceReportSerializer,
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value={
                            "id": 1,
                            "vin": "1HGCM82633A123456",
                            "reporter": {
                                "id": 1,
                                "full_name": "John Doe",
                                "phone": "+79991234567",
                                "telegram": "@johndoe",
                            },
                            "model": "Model X",
                            "place": "Factory A",
                            "comment": "First report",
                            "report_number": 1,
                            "report_time": "2025-03-15T13:57:11.953964+03:00",
                            "acceptance_date": "2025-03-15",
                            "status": "Принят",
                            "car_photos": [
                                {
                                    "id": 1,
                                    "image": "http://example.com/media/cars/2025/03/15/car1.jpg",
                                    "created": "2025-03-15T13:57:11.953964+03:00",
                                }
                            ],
                            "key_photos": [
                                {
                                    "id": 1,
                                    "image": "http://example.com/media/keys/2025/03/15/key1.jpg",
                                    "created": "2025-03-15T13:57:11.953964+03:00",
                                }
                            ],
                            "document_photos": [
                                {
                                    "id": 1,
                                    "image": "http://example.com/media/car-docs/2025/03/15/doc1.jpg",
                                    "created": "2025-03-15T13:57:11.953964+03:00",
                                }
                            ],
                        },
                    ),
                ],
            ),
            400: OpenApiResponse(description="Invalid input"),
            403: OpenApiResponse(description="Forbidden"),
        },
    )
    def create(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer: ModelSerializer) -> None:
        serializer.save(reporter=self.request.user)

    def get_serializer_context(self) -> dict[str, Any]:
        context: dict[str, Any] = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @extend_schema(
        description="Retrieve a mapping of VINs to car brands from the vehicle info db table.",
        summary="Get VIN to Car Brand Mapping",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved VIN to car brand mapping.",
                response=dict,
                examples=[
                    OpenApiExample(
                        name="Success Example",
                        value={
                            "vins": {
                                "ABC123456789DEFGH": "Toyota Camry",
                                "XYZ987654321UVWST": "Honda Civic",
                            }
                        },
                        status_codes=[str(status.HTTP_200_OK)],
                    ),
                ],
            ),
        },
        methods=["GET"],
    )
    @action(methods=["GET"], detail=False, url_path="cars", url_name="get_cars")
    def get_vins(self, request: Request) -> Response:
        vehicles = VehicleInfo.objects.values("vin", "brand", "model").all()
        vins_mapping = {vehicle["vin"]: f"{vehicle['brand']} {vehicle['model']}" for vehicle in vehicles}

        return Response({"vins": vins_mapping})


class CarPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CarPhotoSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self) -> CarPhoto:
        report_id = self.kwargs.get("report_id")
        return CarPhoto.objects.filter(report_id=report_id)

    @extend_schema(
        summary="List all images for a specific report",
        description="Retrieve a list of all car images uploaded for a specific report. "
        "Only accessible to users with the role 'admin' or 'manager'.",
        parameters=[
            OpenApiParameter(
                name="report_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="The ID of the report whose car images are to be retrieved.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Images retrieved successfully",
                response=CarPhotoSerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value=[
                            {
                                "id": 1,
                                "image": "http://example.com/media/cars/2023/10/01/image1.jpg",
                                "created": "2023-10-01T12:34:56Z",
                            },
                            {
                                "id": 2,
                                "image": "http://example.com/media/cars/2023/10/01/image2.jpg",
                                "created": "2023-10-01T12:35:56Z",
                            },
                        ],
                    ),
                ],
            ),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        return super().list(request, *args, **kwargs)


class KeyPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = KeyPhotoSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self) -> KeyPhoto:
        report_id = self.kwargs.get("report_id")
        return KeyPhoto.objects.filter(report_id=report_id)

    @extend_schema(
        summary="List all images for a specific report",
        description="Retrieve a list of all key images uploaded for a specific report. "
        "Only accessible to users with the role 'admin' or 'manager'.",
        parameters=[
            OpenApiParameter(
                name="report_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="The ID of the report whose key images are to be retrieved.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Images retrieved successfully",
                response=CarPhotoSerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value=[
                            {
                                "id": 1,
                                "image": "http://example.com/media/keys/2023/10/01/image1.jpg",
                                "created": "2023-10-01T12:34:56Z",
                            },
                            {
                                "id": 2,
                                "image": "http://example.com/media/keys/2023/10/01/image2.jpg",
                                "created": "2023-10-01T12:35:56Z",
                            },
                        ],
                    ),
                ],
            ),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        return super().list(request, *args, **kwargs)


class DocPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DocumentPhotoSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self) -> DocumentPhoto:
        report_id = self.kwargs.get("report_id")
        return DocumentPhoto.objects.filter(report_id=report_id)

    @extend_schema(
        summary="List all images for a specific report",
        description="Retrieve a list of all document images uploaded for a specific report. "
        "Only accessible to users with the role 'admin' or 'manager'.",
        parameters=[
            OpenApiParameter(
                name="report_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="The ID of the report whose document images are to be retrieved.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Images retrieved successfully",
                response=CarPhotoSerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value=[
                            {
                                "id": 1,
                                "image": "http://example.com/media/car-docs/2023/10/01/image1.jpg",
                                "created": "2023-10-01T12:34:56Z",
                            },
                            {
                                "id": 2,
                                "image": "http://example.com/media/car-docs/2023/10/01/image2.jpg",
                                "created": "2023-10-01T12:35:56Z",
                            },
                        ],
                    ),
                ],
            ),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        return super().list(request, *args, **kwargs)
