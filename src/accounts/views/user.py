from typing import cast

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models.user import DocumentImage, User
from accounts.serializers.user import DocumentImageSerializer, UserSerializer
from accounts.services.single_resource import SingleResourceMixin
from project.permissions import IsAdminOrManager


class CurrentUserViewSet(SingleResourceMixin, mixins.ListModelMixin):
    serializer_class = UserSerializer
    queryset = User.objects.order_by("id")
    permission_classes = [IsAuthenticated]

    def get_object(self) -> User:
        return cast(User, self.request.user)


class DocumentImageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DocumentImageSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self) -> DocumentImage:
        user_id = self.kwargs.get("user_id")
        return DocumentImage.objects.filter(user_id=user_id)
