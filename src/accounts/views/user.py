from typing import Any, cast

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.models.user import DocumentImage, User
from accounts.serializers.user import DocumentImageSerializer, UserSerializer
from accounts.services.single_resource import SingleResourceMixin
from project.permissions import IsAdminOrManager, IsApproved


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

    @extend_schema(
        summary="Onboard current user",
        description="Endpoint to onboard a user. Can only be accessed by approved users.",
        request=None,
        responses={
            200: OpenApiResponse(
                response=dict,
                examples=[
                    OpenApiExample("Already Onboarded", value={"message": "The user is already onboarded"}),
                    OpenApiExample(
                        "Successfully Onboarded", value={"message": "User 'John Doe' has been successfully onboarded"}
                    ),
                ],
            ),
        },
    )
    @action(
        methods=["PATCH"], detail=False, url_path="onboard", url_name="onboard_user", permission_classes=[IsApproved]
    )
    def onboard(self, request: Request) -> Response:
        user: User = request.user
        if user.is_onboarded:
            return Response({"message": "The user is already onboarded"}, status=status.HTTP_200_OK)

        user.is_onboarded = True
        user.save()
        return Response(
            {"message": f"User '{user.full_name}' has been successfully onboarded"}, status=status.HTTP_200_OK
        )


class DocumentImageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DocumentImageSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self) -> DocumentImage:
        user_id = self.kwargs.get("user_id")
        return DocumentImage.objects.filter(user_id=user_id)

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


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(role=User.Roles.USER)
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrManager]

    @extend_schema(
        summary="List all users",
        description="Retrieve a list of all users. Only accessible to users with the role 'admin' or 'manager'.",
        responses={
            200: OpenApiResponse(
                description="Users retrieved successfully",
                response=UserSerializer(many=True),
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value=[
                            {
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
                            {
                                "id": 2,
                                "full_name": "John Smith",
                                "phone": "+79991234566",
                                "telegram": "@johnsmith",
                                "role": "user",
                                "is_approved": True,
                                "is_onboarded": True,
                                "documents": [
                                    {
                                        "id": 2,
                                        "image": "http://example.com/media/documents/2023/10/01/image1.jpg",
                                        "created": "2023-10-01T12:34:56Z",
                                    },
                                ],
                            },
                        ],
                    ),
                ],
            ),
            403: OpenApiResponse(description="Forbidden"),
        },
    )
    def list(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        return super().list(request, *args, **kwargs)
