from typing import Any, cast

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.models.user import DocumentImage, User
from accounts.serializers.user import DocumentImageSerializer, UserSerializer
from accounts.services.single_resource import SingleResourceMixin


class CurrentUserViewSet(SingleResourceMixin, mixins.ListModelMixin):
    serializer_class = UserSerializer
    queryset = User.objects.order_by("id")
    permission_classes = [IsAuthenticated]

    def get_object(self) -> User:
        return cast(User, self.request.user)

    @extend_schema(
        summary="Retrieve the currently authenticated user",
        description="Retrieve details of the currently authenticated user, including their documents.",
        responses={
            200: OpenApiResponse(
                description="User details retrieved successfully",
                response=UserSerializer,
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value={
                            "id": 1,
                            "full_name": "John Doe",
                            "phone": "+79991234567",
                            "telegram": "@johndoe",
                            "role": "user",
                            "is_approved": True,
                            "is_onboarded": True,
                            "documents": [
                                {
                                    "id": 1,
                                    "image": "http://example.com/media/documents/2023/10/01/image1.jpg",
                                    "created": "2023-10-01T12:34:56Z",
                                },
                            ],
                        },
                    ),
                ],
            ),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        return super().list(request, *args, **kwargs)


class DocumentImageViewSet(viewsets.ReadOnlyModelViewSet[DocumentImage]):
    serializer_class = DocumentImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[DocumentImage]:
        if not isinstance(self.request.user, User):
            return cast(QuerySet[DocumentImage], DocumentImage.objects.none())
        return cast(QuerySet[DocumentImage], DocumentImage.objects.filter(user=self.request.user))

    @extend_schema(
        summary="List all images for a specific user",
        description="Retrieve a list of all doc images uploaded by a specific user. "
        "Only accessible to users with the role 'admin' or 'manager'.",
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="The ID of the user whose doc images are to be retrieved.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Images retrieved successfully",
                response=DocumentImageSerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value=[
                            {
                                "id": 1,
                                "image": "http://example.com/media/documents/2023/10/01/image1.jpg",
                                "created": "2023-10-01T12:34:56Z",
                            },
                            {
                                "id": 2,
                                "image": "http://example.com/media/documents/2023/10/01/image2.jpg",
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
