from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from autotrips.models.acceptance_report import AcceptenceReport
from autotrips.serializers.acceptance_report import AcceptanceReportSerializer
from project.permissions import IsApprovedUser

User = get_user_model()


class AcceptanceReportViewSet(viewsets.ModelViewSet[AcceptenceReport]):
    queryset = AcceptenceReport.objects.all()
    serializer_class = AcceptanceReportSerializer
    permission_classes = [IsApprovedUser]
    filterset_fields = ["status", "reporter", "acceptance_date"]
    search_fields = ["vin", "model", "place"]
    ordering_fields = ["report_time", "acceptance_date", "report_number"]
    ordering = ["-report_time"]

    def get_queryset(self) -> QuerySet[AcceptenceReport]:
        return super().get_queryset().select_related("reporter")

    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        three_months_ago = timezone.now() - timedelta(days=90)
        queryset = self.queryset.filter(report_time__gte=three_months_ago)
        vin = request.query_params.get("vin")
        if vin:
            queryset = queryset.filter(vin=vin)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        serializer.save(reporter=self.request.user)

    def get_serializer_context(self) -> dict[str, Any]:
        context: dict[str, Any] = super().get_serializer_context()
        context.update({"request": self.request})
        return context
