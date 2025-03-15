from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from accounts.permissons import IsApproved
from autotrips.models.acceptance_report import AcceptenceReport
from autotrips.serializers.acceptance_report import AcceptanceReportSerializer

User = get_user_model()


class AcceptanceReportViewSet(viewsets.ModelViewSet):
    queryset = AcceptenceReport.objects.all()
    serializer_class = AcceptanceReportSerializer
    permission_classes = [IsApproved]
    http_method_names = ["get", "post"]

    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        three_months_ago = timezone.now() - timedelta(days=90)
        queryset = self.queryset.filter(report_time__gte=three_months_ago)
        vin = request.query_params.get("vin")
        if vin:
            queryset = queryset.filter(vin=vin)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer:ModelSerializer) -> None:
        serializer.save(reporter=self.request.user)

    def get_serializer_context(self) -> dict[str, Any]:
        context: dict[str, Any] = super().get_serializer_context()
        context.update({"request": self.request})
        return context
