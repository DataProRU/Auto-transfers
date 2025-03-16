from typing import Any

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import generics, permissions
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.serializers.register import UserRegistrationSerializer


class RegisterView(generics.CreateAPIView):
    parser_class = [MultiPartParser, FormParser]
    permission_classes = (permissions.AllowAny,)
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
    def post(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        return super().post(request, *args, **kwargs)
