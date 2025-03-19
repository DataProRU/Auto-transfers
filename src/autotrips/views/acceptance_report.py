"""Views для работы с отчетами о приемке."""

from datetime import timedelta
from typing import TYPE_CHECKING, Any, Never

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from autotrips.models.acceptance_report import AcceptanceReport
from autotrips.serializers.acceptance_report import AcceptanceReportSerializer
from project.permissions import IsApprovedUser

if TYPE_CHECKING:
    from django.db.models import QuerySet

User = get_user_model()


class AcceptanceReportViewSet(viewsets.ModelViewSet[AcceptanceReport]):
    """ViewSet для работы с отчетами о приемке."""

    queryset = AcceptanceReport.objects.all()
    serializer_class = AcceptanceReportSerializer
    permission_classes = [IsApprovedUser]
    filterset_fields = ["status", "user", "created"]
    search_fields = ["report_number"]
    ordering_fields = ["created", "report_number"]
    ordering = ["-created"]

    def get_queryset(self) -> "QuerySet[AcceptanceReport]":
        """
        Получает queryset с предзагруженными связанными данными.

        Returns:
            QuerySet[AcceptanceReport]: QuerySet с отчетами.

        """
        return super().get_queryset().select_related("user")

    def list(self, request: Request, *args: Never, **kwargs: Never) -> Response:
        """
        Получает список отчетов за последние 3 месяца.

        Args:
            request: HTTP запрос.
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.

        Returns:
            Response: HTTP ответ со списком отчетов.

        """
        three_months_ago = timezone.now() - timedelta(days=90)
        queryset = self.get_queryset().filter(created__gte=three_months_ago)
        report_number = request.query_params.get("report_number")
        if report_number:
            queryset = queryset.filter(report_number=report_number)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer: BaseSerializer[AcceptanceReport]) -> None:
        """
        Сохраняет отчет, устанавливая текущего пользователя.

        Args:
            serializer: Сериализатор отчета.

        """
        serializer.save(user=self.request.user)

    def get_serializer_context(self) -> dict[str, Any]:
        """
        Получает контекст для сериализатора.

        Returns:
            dict[str, Any]: Контекст сериализатора.

        """
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
