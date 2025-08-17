from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Q
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
    LogisticianInitialVehicleBidSerializer,
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
    "loading": {
        "untouched": {"vehicle_transporter__isnull": True},
        "in_progress": {"ready_for_receiver": True, "approved_by_receiver": False},
        "completed": {"approved_by_receiver": True},
    },
}

MANAGER_GROUPS = {
    "untouched": {"openning_date__isnull": True},
    "in_progress": {"openning_date__isnull": False},
}

TITLE_GROUPS = {
    "untouched": {"notified_logistician_by_title": False},
    "in_progress": {"notified_logistician_by_title": True, "approved_by_title": False},
    "completed": {"approved_by_title": True},
}

RE_EXPORT_GROUPS = {
    "untouched": {"export": False, "prepared_documents": False},
    "in_progress": {"export": False, "prepared_documents": True},
    "completed": {"approved_by_re_export": True},
}

INSPECTOR_GROUPS = {
    "untouched": Q(transit_method=VehicleInfo.TransitMethod.RE_EXPORT, reports__isnull=True)
    | Q(
        transit_method=VehicleInfo.TransitMethod.WITHOUT_OPENNING,
        notified_logistician_by_inspector=False,
    ),
    "in_progress": Q(transit_method=VehicleInfo.TransitMethod.RE_EXPORT, reports__isnull=False)
    | Q(
        transit_method=VehicleInfo.TransitMethod.WITHOUT_OPENNING,
        notified_logistician_by_inspector=True,
    ),
}

RECEIVER_GROUPS = {
    "untouched": Q(vehicle_arrival_date__isnull=True) | Q(vehicle_arrival_date__gt=timezone.now() + timedelta(days=1)),
    "in_progress": {"vehicle_arrival_date__lte": timezone.now() + timedelta(days=1), "full_acceptance": False},
    "completed": {"full_acceptance": True},
}


@extend_schema_view(
    list=extend_schema(
        summary="List vehicle bids (admin: flat list, logistician: grouped, opening_manager: grouped, "
        "title: grouped, inspector: grouped, re_export: grouped, receiver: grouped)",
        description="Admins receive a flat list of all vehicle bids. "
        "Logisticians receive grouped bids by status and approval. "
        "Opening managers receive grouped bids by approval status and arrival date. "
        "Title role receives grouped bids by pickup address and approval. "
        "Inspectors receive grouped bids by inspection status. "
        "Re-export role receives grouped bids by export status and document preparation.",
        parameters=[
            OpenApiParameter(
                name="status",
                description="Vehicle status to filter by (e.g., 'initial'). Required for logisticians."
                "This parameter controls both filtering and serializer selection for GET requests.",
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
                description="Flat list for admin or grouped for logistician/opening_manager/title/inspector/re_export.",
                response=LogisticianInitialVehicleBidSerializer(many=True),
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
                                "approved_by_receiver": False,
                                "creation_time": "2024-06-01T10:00:00Z",
                            },
                        ],
                    ),
                    OpenApiExample(
                        "Logistician Initial grouped list",
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
                        "Logistician Loading grouped list",
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
                                    "logistician_keys_number": None,
                                    "vehicle_transporter": None,
                                    "v_type": {"id": 1, "name": "Sedan"},
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
                                    "logistician_keys_number": 1,
                                    "vehicle_transporter": 1,
                                    "v_type": {"id": 1, "name": "Sedan"},
                                },
                            ],
                            "completed": [
                                {
                                    "id": 3,
                                    "vin": "3HGCM82633A004354",
                                    "brand": "BMW",
                                    "model": "X5",
                                    "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
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
                                    "logistician_keys_number": 1,
                                    "vehicle_transporter": 1,
                                    "v_type": {"id": 1, "name": "Sedan"},
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
                                    "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                                    "transit_method": "re_export",
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
                                    "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
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
                                    "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                                    "transit_method": "re_export",
                                    "pickup_address": "456 Elm St",
                                    "took_title": "yes",
                                    "title_collection_date": "2024-06-10",
                                },
                            ],
                        },
                    ),
                    OpenApiExample(
                        "Inspector grouped list",
                        value={
                            "untouched": [
                                {
                                    "id": 1,
                                    "vin": "1HGCM82633A004352",
                                    "brand": "Honda",
                                    "model": "Accord",
                                    "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                                    "transit_method": "re_export",
                                    "location": "Warehouse 1",
                                    "transit_number": None,
                                    "inspection_done": None,
                                    "number_sent": False,
                                    "inspection_paid": False,
                                    "inspection_date": None,
                                    "number_sent_date": None,
                                    "inspector_comment": None,
                                    "acceptance_date": "2024-06-12",
                                },
                            ],
                            "in_progress": [
                                {
                                    "id": 2,
                                    "vin": "2HGCM82633A004353",
                                    "brand": "Toyota",
                                    "model": "Camry",
                                    "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                                    "transit_method": "re_export",
                                    "location": "Warehouse 2",
                                    "transit_number": "TN123456",
                                    "inspection_done": "yes",
                                    "number_sent": True,
                                    "inspection_paid": True,
                                    "inspection_date": "2024-06-10",
                                    "number_sent_date": "2024-06-11",
                                    "inspector_comment": "Passed inspection",
                                    "acceptance_date": "2024-06-12",
                                },
                            ],
                        },
                    ),
                    OpenApiExample(
                        "Re-export grouped list",
                        value={
                            "untouched": [
                                {
                                    "id": 10,
                                    "vin": "5HGCM82633A004360",
                                    "brand": "Mercedes",
                                    "model": "C-Class",
                                    "client": {"id": 6, "full_name": "Eva White", "email": "eva@example.com"},
                                    "transit_method": "re_export",
                                    "export": False,
                                    "prepared_documents": False,
                                    "title_collection_date": "2024-06-12",
                                },
                            ],
                            "in_progress": [
                                {
                                    "id": 11,
                                    "vin": "6HGCM82633A004361",
                                    "brand": "Lexus",
                                    "model": "RX",
                                    "client": {"id": 7, "full_name": "Sam Blue", "email": "sam@example.com"},
                                    "transit_method": "re_export",
                                    "export": False,
                                    "prepared_documents": True,
                                    "title_collection_date": "2024-06-12",
                                },
                            ],
                            "completed": [
                                {
                                    "id": 12,
                                    "vin": "7HGCM82633A004362",
                                    "brand": "Volvo",
                                    "model": "XC90",
                                    "client": {"id": 8, "full_name": "Tom Red", "email": "tom@example.com"},
                                    "transit_method": "re_export",
                                    "export": True,
                                    "prepared_documents": True,
                                    "title_collection_date": "2024-06-15",
                                },
                            ],
                        },
                    ),
                    OpenApiExample(
                        "Receiver grouped list",
                        value={
                            "untouched": [
                                {
                                    "id": 2,
                                    "client": {
                                        "id": 57,
                                        "full_name": "John Doe",
                                        "phone": "+79991234514",
                                        "telegram": "johndup",
                                        "company": "",
                                        "address": "123 Main St, New York, NY",
                                        "email": "",
                                    },
                                    "brand": "Toyota",
                                    "model": "Camry",
                                    "vin": "4T1BF1FKXEU123470",
                                    "transit_method": "re_export",
                                    "vehicle_arrival_date": "2025-08-22",
                                    "receive_vehicle": False,
                                    "receive_documents": False,
                                    "full_acceptance": False,
                                    "receiver_keys_number": 2,
                                    "vehicle_transporter": {"id": 1, "number": "CAN123OS"},
                                }
                            ],
                            "in_progress": [
                                {
                                    "id": 1,
                                    "client": {
                                        "id": 1,
                                        "full_name": "test",
                                        "phone": "+7111111111",
                                        "telegram": "@test",
                                        "company": None,
                                        "address": None,
                                        "email": "",
                                    },
                                    "brand": "Toyota",
                                    "model": "Camry",
                                    "vin": "4T1BF1FKXEU123469",
                                    "transit_method": "t1",
                                    "vehicle_arrival_date": "2025-08-18",
                                    "receive_vehicle": True,
                                    "receive_documents": True,
                                    "full_acceptance": False,
                                    "receiver_keys_number": 2,
                                    "vehicle_transporter": {"id": 1, "number": "CAN123OS"},
                                }
                            ],
                            "completed": [
                                {
                                    "id": 3,
                                    "client": {
                                        "id": 57,
                                        "full_name": "John Doe",
                                        "phone": "+79991234514",
                                        "telegram": "johndup",
                                        "company": "",
                                        "address": "123 Main St, New York, NY",
                                        "email": "",
                                    },
                                    "brand": "Toyota",
                                    "model": "Camry",
                                    "vin": "4T1BF1FKXEU123468",
                                    "transit_method": "without_openning",
                                    "vehicle_arrival_date": "2025-08-17",
                                    "receive_vehicle": True,
                                    "receive_documents": True,
                                    "full_acceptance": True,
                                    "receiver_keys_number": 3,
                                    "vehicle_transporter": {"id": 1, "number": "CAN123OS"},
                                }
                            ],
                        },
                    ),
                ],
            )
        },
    ),
    retrieve=extend_schema(
        summary="Retrieve a vehicle bid",
        description="Retrieve a single vehicle bid by ID."
        "Use 'status' query parameter to select appropriate serializer.",
        parameters=[
            OpenApiParameter(
                name="status",
                description="Vehicle status for serializer selection. Use 'initial' or 'loading' for logisticians.",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                examples=[
                    OpenApiExample("Initial Status", value="initial"),
                    OpenApiExample("Loading Status", value="loading"),
                ],
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="A vehicle bid instance.",
                response=LogisticianInitialVehicleBidSerializer,
                examples=[
                    OpenApiExample(
                        "Logistician Initial single bid",
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
                        "Logistician Loading single bid",
                        value={
                            "id": 3,
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
                            "logistician_keys_number": 1,
                            "vehicle_transporter": 1,
                            "v_type": {"id": 1, "name": "Sedan"},
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
                            "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                            "transit_method": "re_export",
                            "pickup_address": "456 Elm St",
                            "took_title": "yes",
                            "title_collection_date": "2024-06-10",
                        },
                    ),
                    OpenApiExample(
                        "Inspector single bid",
                        value={
                            "id": 2,
                            "vin": "2HGCM82633A004353",
                            "brand": "Toyota",
                            "model": "Camry",
                            "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                            "transit_method": "re_export",
                            "location": "Warehouse 2",
                            "transit_number": "TN123456",
                            "inspection_done": "yes",
                            "number_sent": True,
                            "inspection_paid": True,
                            "inspection_date": "2024-06-10",
                            "number_sent_date": "2024-06-11",
                            "inspector_comment": "Passed inspection",
                            "acceptance_date": "2024-06-12",
                        },
                    ),
                    OpenApiExample(
                        "Re-export single bid",
                        value={
                            "id": 10,
                            "vin": "5HGCM82633A004360",
                            "brand": "Mercedes",
                            "model": "C-Class",
                            "client": {"id": 6, "full_name": "Eva White", "email": "eva@example.com"},
                            "transit_method": "re_export",
                            "export": False,
                            "prepared_documents": True,
                            "title_collection_date": "2024-06-12",
                        },
                    ),
                    OpenApiExample(
                        "Receiver single bid",
                        value={
                            "id": 3,
                            "client": {
                                "id": 57,
                                "full_name": "John Doe",
                                "phone": "+79991234514",
                                "telegram": "johndup",
                                "company": "",
                                "address": "123 Main St, New York, NY",
                                "email": "",
                            },
                            "brand": "Toyota",
                            "model": "Camry",
                            "vin": "4T1BF1FKXEU123468",
                            "transit_method": "without_openning",
                            "vehicle_arrival_date": "2025-08-17",
                            "receive_vehicle": True,
                            "receive_documents": True,
                            "full_acceptance": True,
                            "receiver_keys_number": 3,
                            "vehicle_transporter": {"id": 1, "number": "CAN123OS"},
                        },
                    ),
                ],
            )
        },
    ),
    update=extend_schema(
        summary="Update a vehicle bid",
        description="Update a vehicle bid by ID. Only fields allowed by the serializer and role can be updated. "
        "The example shows admin, logistician, opening_manager, title and inspector update payloads. "
        "Use X-Vehicle-Status header to select appropriate serializer for logisticians.",
        parameters=[
            OpenApiParameter(
                name="X-Vehicle-Status",
                description="Vehicle status for serializer selection. Use 'initial' or 'loading' for logisticians.",
                required=False,
                type=str,
                location=OpenApiParameter.HEADER,
                examples=[
                    OpenApiExample("Initial Status", value="initial"),
                    OpenApiExample("Loading Status", value="loading"),
                ],
            ),
        ],
        request=LogisticianInitialVehicleBidSerializer,
        responses={
            200: OpenApiResponse(
                description="Updated vehicle bid instance.",
                response=LogisticianInitialVehicleBidSerializer,
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
                            "approved_by_receiver": False,
                            "creation_time": "2024-06-01T10:00:00Z",
                        },
                    ),
                    OpenApiExample(
                        "Logistician Initial update",
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
                        "Logistician Loading update",
                        value={
                            "id": 3,
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
                            "logistician_keys_number": 1,
                            "vehicle_transporter": 1,
                            "v_type": {"id": 1, "name": "Sedan"},
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
                            "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                            "transit_method": "re_export",
                            "pickup_address": "789 Oak Ave",
                            "took_title": "yes",
                            "title_collection_date": "2024-06-15",
                        },
                    ),
                    OpenApiExample(
                        "Inspector update response",
                        value={
                            "id": 3,
                            "vin": "3HGCM82633A004354",
                            "brand": "BMW",
                            "model": "X5",
                            "client": {"id": 2, "full_name": "John Doe", "email": "john@example.com"},
                            "transit_method": "re_export",
                            "location": "Warehouse 3",
                            "transit_number": "TN789012",
                            "inspection_done": "yes",
                            "number_sent": True,
                            "inspection_paid": True,
                            "inspection_date": "2024-06-15",
                            "number_sent_date": "2024-06-16",
                            "inspector_comment": "Updated inspection notes",
                            "acceptance_date": "2024-06-17",
                        },
                    ),
                    OpenApiExample(
                        "Re-export update response",
                        value={
                            "id": 10,
                            "vin": "5HGCM82633A004360",
                            "brand": "Mercedes",
                            "model": "C-Class",
                            "client": {"id": 6, "full_name": "Eva White", "email": "eva@example.com"},
                            "transit_method": "re_export",
                            "export": True,
                            "prepared_documents": True,
                            "title_collection_date": "2024-06-12",
                        },
                    ),
                    OpenApiExample(
                        "Receiver update response",
                        value={
                            "id": 3,
                            "client": {
                                "id": 57,
                                "full_name": "John Doe",
                                "phone": "+79991234514",
                                "telegram": "johndup",
                                "company": "",
                                "address": "123 Main St, New York, NY",
                                "email": "",
                            },
                            "brand": "Toyota",
                            "model": "Camry",
                            "vin": "4T1BF1FKXEU123468",
                            "transit_method": "without_openning",
                            "vehicle_arrival_date": "2025-08-17",
                            "receive_vehicle": True,
                            "receive_documents": True,
                            "full_acceptance": True,
                            "receiver_keys_number": 3,
                            "vehicle_transporter": {"id": 1, "number": "CAN123OS"},
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

        if self.request.method == "GET":
            status = self.request.query_params.get("status")
        else:
            status = self.request.headers.get("X-Vehicle-Status")

        return get_vehicle_bid_serializer(role, status)

    def get_queryset(self) -> QuerySet:
        role = self.request.user.role
        qs = super().get_queryset()

        role_filters = {
            User.Roles.ADMIN: lambda qs: qs,
            User.Roles.LOGISTICIAN: lambda qs: qs,
            User.Roles.OPENING_MANAGER: lambda qs: qs.filter(
                status=VehicleInfo.Statuses.INITIAL,
                approved_by_logistician=True,
                arrival_date__lte=timezone.now() + timedelta(days=7),
                transit_method__in=[VehicleInfo.TransitMethod.T1, VehicleInfo.TransitMethod.RE_EXPORT],
            ),
            User.Roles.TITLE: lambda qs: qs.filter(
                Q(
                    Q(
                        transit_method__in=[VehicleInfo.TransitMethod.T1, VehicleInfo.TransitMethod.RE_EXPORT],
                        approved_by_manager=True,
                    )
                    | Q(transit_method=VehicleInfo.TransitMethod.WITHOUT_OPENNING)
                ),
                approved_by_logistician=True,
            ),
            User.Roles.INSPECTOR: lambda qs: qs.filter(
                Q(
                    Q(transit_method=VehicleInfo.TransitMethod.RE_EXPORT, approved_by_manager=True)
                    | Q(transit_method=VehicleInfo.TransitMethod.WITHOUT_OPENNING)
                ),
                status=VehicleInfo.Statuses.INITIAL,
                approved_by_logistician=True,
            ),
            User.Roles.RE_EXPORT: lambda qs: qs.filter(
                status=VehicleInfo.Statuses.LOADING,
                transit_method__in=[VehicleInfo.TransitMethod.RE_EXPORT, VehicleInfo.TransitMethod.WITHOUT_OPENNING],
            ),
            User.Roles.USER: lambda qs: qs.filter(
                status=VehicleInfo.Statuses.LOADING,
                ready_for_receiver=True,
            ),
        }

        filter_func = role_filters.get(role, lambda qs: qs.none())
        return filter_func(qs)  # type: ignore[no-untyped-call]

    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        role_groupers = {
            User.Roles.ADMIN: lambda: self.get_admin_list(request, *args, **kwargs),
            User.Roles.LOGISTICIAN: lambda: self.get_logistician_grouped_list(request),
            User.Roles.OPENING_MANAGER: lambda: self.get_manager_grouped_list(),
            User.Roles.TITLE: lambda: self.get_title_grouped_list(),
            User.Roles.INSPECTOR: lambda: self.get_inspector_grouped_list(),
            User.Roles.RE_EXPORT: lambda: self.get_re_export_grouped_list(),
            User.Roles.USER: lambda: self.get_receiver_grouped_list(),
        }

        grouper = role_groupers.get(request.user.role)
        if grouper is None:
            raise PermissionDenied("You do not have permission to view bids.")

        return grouper()  # type: ignore[no-untyped-call]

    def get_admin_list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        return super().list(request, *args, **kwargs)

    def get_logistician_grouped_list(self, request: Request) -> Response:
        status_param = request.query_params.get("status", "initial")
        base_qs = self.get_queryset().filter(status=status_param)
        group_param = LOGISTICIAN_GROUPS.get(status_param, {})
        data = {}
        for group_name, group_filter in group_param.items():
            qs = base_qs.filter(**group_filter).distinct()
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

    def get_inspector_grouped_list(self) -> Response:
        base_qs = self.get_queryset()
        data = {}
        for group_name, group_filter in INSPECTOR_GROUPS.items():
            qs = base_qs.filter(group_filter).distinct()
            data[group_name] = self.get_serializer(qs, many=True).data
        return Response(data)

    def get_re_export_grouped_list(self) -> Response:
        base_qs = self.get_queryset()
        data = {}
        for group_name, group_filter in RE_EXPORT_GROUPS.items():
            qs = base_qs.filter(**group_filter)
            data[group_name] = self.get_serializer(qs, many=True).data
        return Response(data)

    def get_receiver_grouped_list(self) -> Response:
        base_qs = self.get_queryset()
        data = {}
        for group_name, group_filter in RECEIVER_GROUPS.items():
            qs = base_qs.filter(group_filter) if isinstance(group_filter, Q) else base_qs.filter(**group_filter)
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
                response=LogisticianInitialVehicleBidSerializer,
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
