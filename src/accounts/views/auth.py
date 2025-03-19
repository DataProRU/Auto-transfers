
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.serializers.custom_token import CustomTokenSerializer


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
                            "user_id": "<id>",
                            "role": "user",
                            "approved": "true",
                            "onboarded": "true",
                        },
                    ),
                ],
            ),
            400: OpenApiResponse(description="Invalid field format"),
        },
    )
    def post(self, request: Request, *args: tuple[object, ...], **kwargs: dict[str, object]) -> Response:
        return super().post(request, *args, **kwargs)
