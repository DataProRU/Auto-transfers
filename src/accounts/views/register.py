from rest_framework import generics, permissions
from accounts.serializers.register import UserRegistrationSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (permissions.AllowAny,)


class CustomTokenObtainPairView(TokenObtainPairView):
    # Кастомизация при необходимости
    pass
