from typing import Any

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        data = super().validate(attrs)
        data.update(
            {
                "user_id": self.user.id,
                "role": self.user.role,
                "approved": self.user.is_approved,
                "onboarded": self.user.is_onboarded,
            }
        )
        return data
