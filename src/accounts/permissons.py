from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsApproved(permissions.BasePermission):
    """Custom permission to only allow users with is_approved=True to access the view."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Check if the user is authenticated and approved
        return bool(request.user and request.user.is_authenticated and request.user.is_approved)
