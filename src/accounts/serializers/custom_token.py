from typing import Any

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken, Token

from accounts.models.user import User


class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: User) -> Token:
        """Add custom claims directly to the token payload."""
        token = super().get_token(user)

        token["user_id"] = user.id
        token["role"] = user.role
        token["approved"] = user.is_approved
        token["onboarded"] = user.is_onboarded

        return token


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        refresh = RefreshToken(attrs["refresh"])
        user_id = refresh.payload.get("user_id")
        user = User.objects.get(id=user_id)

        data = super().validate(attrs)

        new_access = AccessToken(data["access"])  # type: ignore[arg-type]
        new_access.payload.update(
            {
                "role": user.role,
                "approved": user.is_approved,
                "onboarded": user.is_onboarded,
            }
        )
        data["access"] = str(new_access)
        return data
