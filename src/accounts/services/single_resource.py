from typing import Any, TypeVar, cast

from django.db.models import Model
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from accounts.models.user import User

T = TypeVar("T", bound=Model)
S = TypeVar("S", bound=BaseSerializer[Any])


class SingleResourceMixin(viewsets.GenericViewSet[T]):
    pagination_class = None

    def get_object(self) -> T:
        if not isinstance(self.request.user, User):
            raise User.DoesNotExist("User not found or invalid type")
        return cast(T, self.request.user)

    def list(self, request: Request, *args: list[Any], **kwargs: dict[str, Any]) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
