from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from accounts.models.user import User


class IsApprovedUser(BasePermission):
    def has_permission(self, request: Request, view: APIView | ViewSet) -> bool:
        if not isinstance(request.user, User):
            return False
        return bool(request.user.is_authenticated and request.user.is_approved)


class IsAdminOrManager(BasePermission):
    def has_permission(self, request: Request, view: APIView | ViewSet) -> bool:
        if not isinstance(request.user, User):
            return False
        is_authenticated = request.user.is_authenticated
        is_staff_or_manager = request.user.is_staff or request.user.role == User.Roles.MANAGER
        return bool(is_authenticated and is_staff_or_manager)
