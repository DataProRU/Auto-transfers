from typing import Any

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.models.user import User
from accounts.serializers.register import UserRegistrationSerializer
from autotrips.tasks import send_registration_notification


class RegisterView(generics.CreateAPIView[User]):
    parser_class = [MultiPartParser, FormParser]
    permission_classes = (permissions.AllowAny,)
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

    @extend_schema(
        summary="Register a new user",
        description="Register a new user with the provided details, "
        "including full name, phone, telegram, password, and uploaded images.",
        request=UserRegistrationSerializer,
        responses={
            201: OpenApiResponse(
                description="User registered successfully",
                response=UserRegistrationSerializer,
                examples=[
                    OpenApiExample(
                        name="Successful registration",
                        value={
                            "id": 1,
                            "full_name": "John Doe",
                            "phone": "+79991234567",
                            "telegram": "@johndoe",
                            "images": [
                                {
                                    "id": 1,
                                    "image": "http://example.com/media/documents/2023/10/01/image1.jpg",
                                },
                                {
                                    "id": 2,
                                    "image": "http://example.com/media/documents/2023/10/01/image2.jpg",
                                },
                            ],
                        },
                    ),
                ],
            ),
            400: OpenApiResponse(description="Invalid input"),
        },
    )
    def create(self, request: Request, *args: list[Any], **kwargs: dict[str, Any]) -> Response:
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            send_registration_notification.delay(response.data["id"])
        return response
