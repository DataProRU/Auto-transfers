from rest_framework import generics, permissions

from accounts.serializers.custom_token import CustomTokenSerializer
from accounts.serializers.register import UserRegistrationSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


# accounts/views.py
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = (permissions.AllowAny,)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer
