from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from accounts.models.user import User


class IsApprovedUser(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not isinstance(user, User):
            return False
        return bool(user.is_authenticated and user.is_approved and user.role in ["admin", "manager"])


class IsAdminOrManager(BasePermission):
    """Custom permission to only allow users with role 'admin' or 'manager'."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not isinstance(user, User):
            return False
        return bool(user.is_authenticated and user.role in ["admin", "manager"])
