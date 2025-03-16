from typing import cast

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models.user import User
from accounts.serializers.user import UserSerializer
from accounts.services.single_resource import SingleResourceMixin


class CurrentUserViewSet(SingleResourceMixin, viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.order_by("id")
    permission_classes = [IsAuthenticated]

    def get_object(self) -> User:
        return cast(User, self.request.user)
