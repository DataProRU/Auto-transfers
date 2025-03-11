from rest_framework import generics, permissions
from rest_framework.parsers import FormParser, MultiPartParser

from accounts.serializers.register import UserRegistrationSerializer


class RegisterView(generics.CreateAPIView):
    parser_class = [MultiPartParser, FormParser]
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer
