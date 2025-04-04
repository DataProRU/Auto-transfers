from typing import Any

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.serializers.custom_token import CustomTokenRefreshSerializer, CustomTokenSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer

    @extend_schema(
        summary="Obtain JWT token pair (access and refresh)",
        description="Authenticate a user and return a JWT token pair (access and refresh tokens) and user info.",
        responses={
            200: OpenApiResponse(
                description="Token pair obtained successfully",
                response=CustomTokenSerializer,
                examples=[
                    OpenApiExample(
                        name="Successful authentication",
                        value={
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        },
                    ),
                ],
            ),
            400: OpenApiResponse(description="Invalid field format"),
        },
    )
    def post(self, request: Request, *args: tuple[Any], **kwargs: dict[str, Any]) -> Response:
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer
