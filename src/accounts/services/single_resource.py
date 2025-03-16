from typing import Any

from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response


class SingleResourceMixin(viewsets.GenericViewSet):
    pagination_class = None

    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
