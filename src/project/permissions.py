from django.contrib.auth import get_user_model
from django.db import models
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

User = get_user_model()


class IsAdminOrManager(permissions.BasePermission):
    """Custom permission to only allow users with role 'admin' or 'manager'."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        allowed_roles = {User.Roles.ADMIN, User.Roles.MANAGER}
        return bool(request.user and request.user.is_authenticated and request.user.role in allowed_roles)


class IsApproved(permissions.BasePermission):
    """Custom permission to only allow users with is_approved=True to access the view."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Check if the user is authenticated and approved
        allowed_roles = {User.Roles.ADMIN, User.Roles.MANAGER, User.Roles.USER}
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role in allowed_roles
        )


class VehicleAccessPermission(permissions.BasePermission):
    """
    Custom permission to only allow admins and managers to create/update vehicles info for all clients.

    Clients to create vehicle or update their own vehicles.
    """

    staff_roles = {User.Roles.ADMIN, User.Roles.MANAGER}
    allowed_roles = staff_roles | {User.Roles.CLIENT}

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role in self.allowed_roles)

    def has_object_permission(self, request: Request, view: APIView, obj: models.Model) -> bool:
        if request.user.role in self.staff_roles:
            return True

        if request.user.role == User.Roles.CLIENT:
            return bool(obj.client == request.user)

        return False


class VehicleBidAccessPermission(permissions.BasePermission):
    """Custom permission to only allow admins and crm users to access vehicles info."""

    allowed_roles = {
        User.Roles.ADMIN,
        User.Roles.LOGISTICIAN,
        User.Roles.OPENING_MANAGER,
        User.Roles.TITLE,
        User.Roles.INSPECTOR,
        User.Roles.RE_EXPORT,
        User.Roles.USER,
    }

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role in self.allowed_roles)


class AdminLogisticianVehicleBidAccessPermission(permissions.BasePermission):
    """Custom permission to only allow admins and logisticians to access vehicles info."""

    allowed_roles = {
        User.Roles.ADMIN,
        User.Roles.LOGISTICIAN,
    }

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role in self.allowed_roles)
