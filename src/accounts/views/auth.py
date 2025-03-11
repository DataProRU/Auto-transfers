from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.serializers.custom_token import CustomTokenSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer
