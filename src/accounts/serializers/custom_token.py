from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token

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
