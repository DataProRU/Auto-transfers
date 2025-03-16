from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdminOrManager(permissions.BasePermission):
    """Custom permission to only allow users with role 'admin' or 'manager'."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        allowed_roles = {"admin", "manager"}
        return bool(request.user and request.user.is_authenticated and request.user.role in allowed_roles)
