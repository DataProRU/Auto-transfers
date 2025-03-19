from typing import Any

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models.user import User


class CustomTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        data = super().validate(attrs)
        user = self.user
        if not isinstance(user, User):
            return data

        data.update(
            {
                "user_id": user.id,
                "role": user.role,
                "approved": user.is_approved,
                "onboarded": user.is_onboarded,
            }
        )
        return data
